#!/usr/bin/env python3

import sys

import runprompt

# Fizzbuzz assembled in decimal
program = {
    1536: (169, 1,),
    1538: (133, 16,),
    1540: (169, 2,),
    1542: (133, 17,),
    1544: (169, 4,),
    1546: (133, 18,),
    1548: (166, 16,),
    1550: (165, 17,),
    1552: (5, 18,),
    1554: (208, 7,),
    1556: (169, 251,),
    1558: (149, 0,),
    1560: (76, 53, 6,),
    1563: (165, 17,),
    1565: (208, 7,),
    1567: (169, 240,),
    1569: (149, 0,),
    1571: (76, 53, 6,),
    1574: (165, 18,),
    1576: (208, 7,),
    1578: (169, 176,),
    1580: (149, 0,),
    1582: (76, 53, 6,),
    1585: (165, 16,),
    1587: (149, 0,),
    1589: (198, 17,),
    1591: (16, 4,),
    1593: (169, 2,),
    1595: (133, 17,),
    1597: (198, 18,),
    1599: (16, 4,),
    1601: (169, 4,),
    1603: (133, 18,),
    1605: (230, 16,),
    1607: (169, 16,),
    1609: (37, 16,),
    1611: (240, 191,),
    1613: (0,),
}

if False: # debug
    for (addr, bytes) in program.items():
        bytes_string = " ".join([("%d" % byte) for byte in bytes])
        print("%d: %s" % (addr, bytes_string))

opcode_to_description_strings = {
    0: "BRK; %(BYTES)d bytes; stop execution",
    133: "STA %(L)d; %(BYTES)d bytes; store A in memory location %(L)d",
    149: "STA %(L)d, %(BYTES)d bytes; X; store A in memory location %(L)d+X",
    165: "LDA %(L)d; %(BYTES)d bytes; load A from memory location %(L)d",
    166: "LDX %(L)d; %(BYTES)d bytes; load X register from memory location %(L)d",
    169: "LDA %(I)d; %(BYTES)d bytes; load A from the next instruction byte, %(I)d",
    198: "DEC %(L)d; %(BYTES)d bytes; decrement value in memory location %(L)d",
    230: "INC %(L)d; %(BYTES)d bytes; increment value in memory location %(L)d",
    37: "AND %(L)d; %(BYTES)d bytes; load memory from memory location %(L)d and bitwise-AND into accumulator",
    5: "ORA %(L)d; %(BYTES)d bytes; load memory from memory location %(L)d and bitwise-OR into accumulator",
    16: "BPL %(M)d; %(BYTES)d bytes; if N flag is clear, also add the signed value to PC",
    240: "BEQ %(M)d; %(BYTES)d bytes; if Z flag set, also add the signed value to PC",
    208: "BNE %(M)d; %(BYTES)d bytes; if Z flag is clear, also add the signed value to PC",
    76: "JMP %(JMP)d; %(BYTES)d bytes; set the PC to the value of the next two instruction bytes, %(P)d + %(Q)d * 256",
}

# run our 6502 through one instruction
def execute6502(PC, bytes, A, X, N, Z, MEMORY):
    opcode = bytes[0]
    newPC = PC + len(bytes)
    go = True
    if opcode == 0:
        go = False
    elif opcode == 133:
        MEMORY[bytes[1]] = A
    elif opcode == 149:
        MEMORY[bytes[1] + X] = A
    elif opcode == 165:
        A = MEMORY[bytes[1]]
        N = (A & 0x80) != 0
        Z = A == 0
    elif opcode == 166:
        X = MEMORY[bytes[1]]
        N = (X & 0x80) != 0
        Z = X == 0
    elif opcode == 169:
        A = bytes[1]
        N = (A & 0x80) != 0
        Z = A == 0
    elif opcode == 198:
        MEMORY[bytes[1]] = (MEMORY[bytes[1]] + 256 - 1) % 256
        N = (MEMORY[bytes[1]] & 0x80) != 0
        Z = MEMORY[bytes[1]] == 0
    elif opcode == 230:
        MEMORY[bytes[1]] += 1
        N = (MEMORY[bytes[1]] & 0x80) != 0
        Z = MEMORY[bytes[1]] == 0
    elif opcode == 37:
        A = A & MEMORY[bytes[1]]
        N = (A & 0x80) != 0
        Z = A == 0
    elif opcode == 5:
        A = A | MEMORY[bytes[1]]
        N = (A & 0x80) != 0
        Z = A == 0
    elif opcode == 16:
        M = bytes[1]
        if M > 127:
            M = M - 256
        if N == 0:
            newPC += M
    elif opcode == 240:
        M = bytes[1]
        if M > 127:
            M = M - 256
        if Z != 0:
            newPC += M
    elif opcode == 208:
        M = bytes[1]
        if M > 127:
            M = M - 256
        if Z == 0:
            newPC += M
    elif opcode == 76:
        newPC = bytes[1] + 256 * bytes[2]
    else:
        raise ValueError

    return (go, newPC, A, X, N, Z, MEMORY)

# Simple 6502 state and computer state
PC = 1536
A = 0
X = 0
Y = 0
N = 0
Z = 0
MEMORY = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,]

# Query GPT only after this many instructions; set to 300 to only print reference
query_only_after = 0

# Only run this many instructions.
# To run a short test, set to e.g. 10.
# There are 288 instructions, so set to e.g. 300 to run all of them.
only_execute = 300

go = True       # if False, exit main loop
while go and only_execute > 0:
    bytes = program[PC]

    # construct current state for prompt
    bytes_string = " ".join([("%d" % byte) for byte in bytes])
    insn_bytes_string = "%d: %s" % (PC, bytes_string)
    memory_string = ", ".join([("%d" % byte) for byte in MEMORY])
    state_string = "uint8_t MEMORY[]={%s}, A=%d, X=%d, N=%d, Z=%d; uint16_t PC=%d;" % (memory_string, A, X, N, Z, PC)

    # print to output so we can parse it
    print("%s" % insn_bytes_string)
    print("%s" % state_string)
    print("Reference:")

    # set up some substitutions for our instruction descriptions
    vars = {}
    vars["BYTES"] = len(bytes)
    if len(bytes) > 1:
        vars["L"] = bytes[1]
        vars["I"] = bytes[1]
        vars["M"] = (bytes[1] + 128) % 256 - 128
        if len(bytes) > 2:
            vars["P"]  = bytes[1]
            vars["Q"]  = bytes[2]
            vars["JMP"]  = bytes[1] + 256 * bytes[2]
    print("    DESC: %s" % (opcode_to_description_strings[bytes[0]] % vars))

    # execute the instruction in our reference implementation
    old_PC = PC
    (go, PC, A, X, N, Z, MEMORY) = execute6502(PC, bytes, A, X, N, Z, MEMORY)
    memory_string = ", ".join([("%d" % byte) for byte in MEMORY])
    print("    CPU: MEMORY[]={%s}, A=%d, X=%d, N=%d, Z=%d, PC=%d" % (memory_string, A, X, N, Z, PC))

    if query_only_after <= 0:
        # send to GPT and print that result
        response = runprompt.GetChatGPTResult(state_string, insn_bytes_string)

        print("Chat-GPT:")
        lines = response["content"].split("\n")
        for l in lines:
            print("    %s" % l)

    # in case of piping to tee or whatever
    sys.stdout.flush()

    query_only_after -= 1
    only_execute -= 1
