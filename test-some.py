import sys
import os

import runprompt

input = sys.stdin.read()
lines = input.split("\n")
del(lines[len(lines) - 1])

while len(lines) > 0:
    (insns, state) = [l.strip() for l in lines[0:2]]
    del(lines[0:2])
    print(state)
    print(insns)
    result = runprompt.GetChatGPTResult(state, insns)
    print(result["content"])
