# In Which I Convince GPT-4 to be a 6502 Microprocessor

Almost.

## Context

Although my day job is [GPU](https://www.lunarg.com/) [APIs](https://github.com/lunarg/gfxreconstruct), I was bitten several years ago by the retrocomputing bug ([The Alice 3](https://lkesteloot.github.io/alice/alice3/), [The Alice 4](https://lkesteloot.github.io/alice/alice4/), [The Apple2A BASIC compiler](https://github.com/bradgrantham/apple2a), [a chip-8 emulator](https://github.com/bradgrantham/chip8), [a Colecovision emulator](https://github.com/bradgrantham/leathervision)). One of my favorite programs I wrote myself is an [Apple 2 emulator](https://github.com/bradgrantham/apple2e) I wrote for fun. There are definitely better ones, but that one’s mine. In particular I wrote the 6502 microprocessor emulation from scratch, and it had been tricky to get it right.

When Codex, GPT-3, and then ChatGPT were released in turn, it became clear LLMs can have astonishing levels of [integrated technical knowledge](https://www.engraved.blog/building-a-virtual-machine-inside/). My joke at the time was that I should have ChatGPT do 6502 emulation for me. It’s become very obvious to me lately that [should *not* be a joke](https://karpathy.medium.com/software-2-0-a64152b37c35), and I should investigate ways a trained machine learning model can solve these kinds of problems for me. Probably the most appropriate solution would be to build my own network to emulate a processor, then train it. But since everyone else is making ChatGPT do crazy things, I want to join the bandwagon.

## Initial Stabs

I spent a chunk of a weekend engineering a JSON protocol for interfacing an external 6502 emulator to my Apple 2 emulation code. The initial disk-less BASIC prompt took emulation of many hundreds of thousands of correct instructions. Based on a couple of initial tests with curl, that would have taken days back and forth to OpenAI’s API and probably would have been prohibitively expensive.

More importantly, the emulation would need to be nearly 100% accurate, and it’s not immediately obvious what prompt to use to ensure accuracy. I’m willing to reduce the program size and microprocessor feature set somewhat and still feel like I could make a credible assessment.

On the suggestion of my friend [Lawrence Kesteloot](https://www.teamten.com/lawrence/) I implemented a short [“FizzBuzz”](https://en.wikipedia.org/wiki/Fizz_buzz) program directly in 6502 assembly language. I used [Nick Morgan’s excellent online 6502 assembler and emulator](https://skilldrick.github.io/easy6502/) to write the code and test it.

[Here's fizzbuzz.asm.](https://github.com/bradgrantham/gpt-4-6502/blob/main/fizzbuzz.asm)

When executed, the result of memory locations 1 through 15 are 0xFB if the memory index is FizzBuzz (divisible by 3 and 5), 0xF0 if the index is Fizz (divisible by 3), 0xB0 if Buzz (divisible by 5), or the value of the index itself otherwise.  So that looks like this in decimal numbers including memory location 0:

```
0, 1, 2, 240, 4, 176, 240, 7, 8, 240, 176, 11, 240, 13, 14, 251
```

(240 is 0xF0, 176 is 0xB0, and 251 is 0xFB).

My measure of success is how well `gpt-4` can produce the same values in memory at completion of the program, which is to say how well could it run FizzBuzz for values 1 to 15.

It’s a small program, just 38 assembled instructions, and including loops the entire execution is 288 instructions. Here’s the hexdump.

```
0600: a9 01 85 10 a9 02 85 11 a9 04 85 12 a6 10 a5 11
0610: 05 12 d0 07 a9 fb 95 00 4c 35 06 a5 11 d0 07 a9
0620: f0 95 00 4c 35 06 a5 12 d0 07 a9 b0 95 00 4c 35
0630: 06 a5 10 95 00 c6 11 10 04 a9 02 85 11 c6 12 10
0640: 04 a9 04 85 12 e6 10 a9 10 25 10 f0 bf 00
```

I only use the A and X registers, the N and Z flags, and 18 bytes of zero-page RAM (technically only 17 since I don’t access memory address 0). I don’t expect the normal 6502 startup, which initializes the PC from memory; I set the PC directly. I don’t use the stack. I assume BRK stops execution.  I only use the following 13 opcodes:

| Opcode | Mnemonic   | Description                                                  |
| ------ | ---------- | ------------------------------------------------------------ |
| 0      | BRK        | Stop executing                                               |
| 133    | STA zpg    | Store accumulator in memory                                  |
| 149    | STA zpg, X | Store accumulator in memory, indexed by X                    |
| 165    | LDA zpg    | Load accumulator from memory                                 |
| 169    | LDA imm    | Load accumulator "immediate", from the next byte after the instruction |
| 198    | DEC zpg    | Decrement a value in memory                                  |
| 230    | INC zpg    | Increment a value in memory                                  |
| 37     | AND zpg    | Bitwise-and the accumulator with a value in memory, storing the result in the accumulator |
| 5      | ORA zpg    | Bitwise-or the accumulator with a value in memory, storing the result in the accumulator |
| 16     | BPL        | Signed 8-bit relative branch "if plus" (if the N flag is clear) |
| 240    | BEQ        | Signed 8-bit relative branch "if equal" (if the Z flag is clear) |
| 208    | BNE        | Signed 8-bit relative branch "if not equal" (if the Z flag is set) |
| 76     | JMP        | Absolute value jump (to a 16-bit address)                    |

# Asking ChatGPT to run it directly

Just to get a feel for how far off I was, after providing the entire machine code in hex I asked `gpt-4`  the contents of memory in a separate query.

```
After running the provided 6502 machine code, the memory locations from 0 to 15 would contain the following values:

00: fb
01: f0
02: b0
03: 00
[...]
```

Of course that doesn’t work, `gpt-4` is still a feed-forward network at its core, and I doubt it's deep enough to encode 288 machine instructions from input to output without an intervening cycle through the network. There are ways to add external functionality to `gpt-4` so it can perform more accurate math, for example, but that feels like cheating for this experiment.  I *was* able to lead it to a pretty good high-level description of the program with a couple of corrections (e.g. "Is it possible it's using them as counters to 0?") but I couldn't get the correct memory values out of it.

However, ChatGPT (not using the developer playground) surprised me with a really good disassembly listing from this raw hexdump.  I suggest you paste in the hexdump and ask it for a disassembly for that 6502 machine code block.

# One Instruction At A Time

So I continued with my original approach, running one instruction at a time. I tried a bunch of initial experiments, hoping for a prompt that would allow GPT-3 and then GPT-4 to interpret some kind of regular machine state input, then give me back a machine-readable state vector output.

I finally settled on a [prompt](https://github.com/bradgrantham/gpt-4-6502/blob/main/prompt.txt) that seemed to work pretty well.  (The first line is provided as the "system" context.). I'll explain some of the bits of the prompt and what I think they do.

```
Hello!  I will tell you the bytes for a 6502 instruction.
```

This is pretty straightforward.  I'm going to give it the bytes for the instruction.

```
Respond with "DESC:" and a one-line description of the instruction including the number of bytes in the instruction.  Then output an excerpt of pseudo-code detailing any calculation of the new A, X, N, Z, PC, and reads from and writes to MEMORY.
```

I had a lot more luck with GPT when I asked it to first describe what it was going to do, then do it.  I think this is similar to ["zero-shot" "chain-of-thought" prompting](https://learnprompting.org/docs/intermediate/zero_shot_cot); I'm setting up the cycles of tokens through the model so that at the time the model actually executes the instruction, it's already provided itself with a kind of template or prototype of what the pieces of that execution are.

```
Execute the pseudo-code for the instruction, then finish with "CPU: MEMORY[]={memory contents}, PC=new value, A=new value, X=new value, N=new value, Z=new value"
```

I give an example of the format I want, so when GPT responds it will be more likely to format its own output this way.  That's important because I'd like to parse GPT's response using some simple Python code.

```
  * All numbers are in decimal.
```

When I didn't say this I got wildly different interpretations of numbers.

```
[... list of opcodes describing how each works]
* Opcode 149 is STA L indexed with X; MEMORY[L+X] = A
[... more opcodes]
```

Again here I think I'm priming the model.  The way I think about is that the token "149" makes it much more likely for the model to output results related to "STA L" here.  I also use "L" and the accumulator "A" as variables, so the model will have examples to follow.
```
Here are some examples:

[...]

uint8_t MEMORY[]={0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 4}, A=2, X=1, N=0, Z=0; uint16_t PC=1552;
1552: 5 18
DESC: ORA 18; 2 bytes; A = bitwise-or(MEMORY[18], A)
// MEMORY[18] is 4
A = A | MEMORY[M]; // A becomes 6
N = (A & 128) != 0; // N becomes 0
Z = A == 0; // Z becomes 0
PC = PC + 2; // PC becomes 1554
CPU: MEMORY[]={0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 4}, A=6, X=1, N=0, Z=0, PC=1554
```

I give a few examples of instructions, so this isn't really a zero-shot prompt.  I'm telling the model that I expect to give it a machine state vector and then the instruction bytes, then it will describe the instruction both with a single-line abbreviated version and then a pseudo-code version, and then it will provide the results of executing that pseudo-code on the machine state vector.  I used `uint8_t` as a hint that those values would be 8-bit only, and then `uint16_t PC` just for symmetry.

## Testing

[Source](https://github.com/bradgrantham/gpt-4-6502)

In order to execute an instruction, I take my prompt and append the "current" state vector and the bytes for the next instruction, then I send that whole thing to [OpenAI's web API as a JSON completion request](https://platform.openai.com/docs/guides/chat).  (That's why I've used `gpt-4` instead of GPT-4 throughout most of this README; `gpt-4` is the name of the model in the API.)

I cheat a little bit because I'm decoding the instruction a little bit on my own up front to know how many bytes are in it.  In my earlier experiments when I hoped `gpt-3.5-turbo` could reply to me asking for each byte from memory and then telling me bytes to write to memory it got hopelessly wrong and verbose.

My original 6502 microprocessor emulation is in C++, but to aid tooling in comparing results from `gpt-4` I've implemented a subset of this emulation for this test in a little bit of Python.

The main script, [run-all-instructions.py](https://github.com/bradgrantham/gpt-4-6502/blob/main/run-all-instructions.py), runs the 6502 program all the way through, one instruction at a time, to generate the reference results, and then sends each instruction with my hand-crafted prompt to OpenAI’s Python API as well. The script does not check the correctness of the output from OpenAI. Instead, I used the saved output to assess how close my prompt brought `gpt-4` to accurate results for all of the machine states and instruction variants in the program. This script takes on the order of $24 to run all 288 instructions at OpenAI’s `gpt-4` rates as of March 2023, depending highly on the prompt and how verbose the response is. (So running on the order of 500K instructions to get to an Apple ][ prompt would have cost me around **forty thousand dollars**!)

A second script, [test-some.py](https://github.com/bradgrantham/gpt-4-6502/blob/main/test-some.py), runs one or more machine state vectors and instructions just so I can see the output. This limits my cost for the OpenAI and allows me to quickly try different prompt variants.

## Results

### gpt-3.5-turbo

I didn't have a lot of luck with `gpt-3.5-turbo`.  I never got more than half of the results to match the reference.  There were many categories of failures.  Here are some from my notes.  Over the course of this project I didn't save all the revisions of my prompt, so it's possible that these problems are resolved more by prompt improvements than moving from GPT-3 to GPT-4.

1. The model had trouble getting memory locations right.  Here's an example:
   ```
   1607: 169 16
   uint8_t MEMORY[]={0, 1, 2, 240, 4, 176, 240, 7, 8, 0, 0, 0, 0, 0, 0, 0, 9, 0, 1}, A=8, X=8, N=0, Z=0; uint16_t PC=1607;
   ```

   This is "LDA 16", load the accumulator from address 16 (0-indexed), so it should become 9.  `gpt-3.5-turbo` gave me:
   ```
   DESC: LDA 16; load the value at memory location 16 into A
   M = 16;
   A = MEMORY[M];
   N = (A & 128) != 0;
   Z = A == 0;
   PC = PC + 2;
   CPU: old PC=1607, bytes=2, MEMORY[]={0, 1, 2, 240, 4, 176, 240, 7, 8, 240, 0, 0, 0, 0, 0, 0, 10, 2, 0}, PC=1609, A=240, X=9, N=1, Z=0
   ```

   It described the instruction correctly and even had correct pseudocode, but then the actual value of `A` was just wrong.  The number `240` is in memory, but I don't know why it thought `MEMORY[16]` was 240.  I can't say *exactly* what the issue was because I don't have any visibility into the structure of the model.  I think I [may not be able to enable probabilities in the output](https://twitter.com/sandersted/status/1637156533963472901?s=20) but I could probably ask the model itself to give me some kind of confidence measurement or explain how it looked up memory locations.  

2. There were some places where values appeared to be interpreted as hexadecimal.  One instruction repeated several times is 16,  `BPL`.  `gpt-3.5-turbo` interpreted 16 as `ASL` multiple times, but `0x16` *is* `ASL`. 

3. `gpt-3.5-turbo` would sometimes give me inconsistent output from one instruction to the next, maybe putting commas between memory locations or maybe putting a period at the end of the `CPU` state.  In one instance, it output `\` at the end of the `CPU` state response, and that was never anywhere in my prompts!

4. I had much better results when I specified `MEMORY` as a C-style array, within braces (`{}`).  That also seemed to help imply I wanted zero-based indexing.

Things also settled down somewhat when I set `temperature=0.0` in my chat API request, so that responses were deterministic.

### gpt-4

Out of 288 instructions, from `gpt-4` ***only 2 don't match the reference.***  It took me 77 minutes to run `run-all-instructions.py` on March 20th, 2023.  

One of them is a mismatch in PC from BRK, so I don't care much about that.  `gpt-4` might actually be correct about that; the PC actually should be pushed and reloaded from a two-byte vector in memory, so I could also be confusing the model.

The other is a bitwise error.  The instruction and state vector is:
```
1609: 37 16
uint8_t MEMORY[]={0, 1, 2, 240, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 2, 1}, A=16, X=3, N=0, Z=0; uint16_t PC=1609;
```

And the reference results from my Python version are:

```
    DESC: AND 16; 2 bytes; load memory from memory location 16 and bitwise-AND into accumulator
    CPU: MEMORY[]={0, 1, 2, 240, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 2, 1}, A=0, X=3, N=0, Z=1, PC=1611
```

But `gpt-4` responded with this:

```
    DESC: AND 16; 2 bytes; A = bitwise-and(MEMORY[16], A)
    // MEMORY[16] is 4
    A = A & MEMORY[16]; // A becomes 16 & 4 = 4
    N = (A & 128) != 0; // N becomes 0
    Z = A == 0; // Z becomes 0
    PC = PC + 2; // PC becomes 1611
    CPU: MEMORY[]={0, 1, 2, 240, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 2, 1}, A=4, X=3, N=0, Z=0, PC=1611
```

The notable wrong part is `A = A & MEMORY[16]; // A becomes 16 & 4 = 4`.  I'm not sure why `gpt-4` thinks that.  Maybe the model decided 16 was hexadecimal even after I specified all numbers were decimal, in which case `0x16 & 4` would in fact be 4.

## Conclusions

### Practical Use

At a practical level, I don't think anyone is going to implement a 6502 using a multi-gigabyte model that costs around $0.08 an instruction to run.  But in 10 years will they?  Maybe if it's essentially free.  It probably makes more sense to train a model specifically to replace the microprocessor for simulation or whatever.  What if we had technology to encode a tightly-specified network into an ASIC?

One thing you probably *could* do right now is use `gpt-4` or ChatGPT in GPT-4 mode as a reference for implementing an emulator.  I couldn't get ChatGPT in GPT-3 mode to give me a reasonable emulation switch statement six months ago, but I didn't know much about prompt engineering then.  You might also be able to use GPT-4 to help you reverse-engineer a microprocessor or debug your code.  Some 8-bit processors are still in quite common use.

### Implications

I imagine a hypothetical version of [the Chinese Room](https://en.wikipedia.org/wiki/Chinese_room) in which a human has reference manuals for the 6502 but no calculator and no way to execute the code themselves. I pass them a single sheet of paper with instructions under the door, then pass three-by-five cards with machine state and an instruction, and they hand me back changes to the machine state. We repeat until they tell me they’re done. (The last card says “0” and that’s “BRK”, after which the person would pass me back a card saying “Stop!”)

On one hand, almost every programmer I know could execute that task pretty well. I wouldn’t expect 100% success for 288 instructions just because of lack of attention, ambiguity in instructions, maybe just doing math in one’s head wrong, or exhaustion after doing 288 cards. Maybe a programmer could do better than 90%. On the other hand, people I know who are *not* professional programmers might not even comprehend what I’m asking. I think most of them wouldn’t get many of the cards right at all.

So `gpt-4` is already much better than most people at a technical task which requires significant reasoning and recall.  Even [GPT-3 passed a technical interview at Google](https://www.pcmag.com/news/chatgpt-passes-google-coding-interview-for-level-3-engineer-with-183k-salary), but for a lower-level job.  I think GPT-5 will usually get this emulation task right, and probably a bunch of harder things.  I suspect it will even be able to get close to telling me the memory vector results without executing the instructions.

My job isn’t programming anymore, most days. I spend a lot of my time reviewing code, providing feedback on interfaces, and thinking about how to improve our product.  I haven't had much luck asking ChatGPT about that. How long before some very large language model will do that better than I can?  
