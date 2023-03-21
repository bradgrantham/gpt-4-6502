import sys
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

with open("prompt.txt", "r") as prompts:
    system_content = prompts.readline()
    preamble = prompts.read()

def GetChatGPTResult(state_string, insn_bytes_string):
    prompt = '''%s

Set state to %s
%s''' % (preamble, state_string, insn_bytes_string)

    # print("%s" % prompt)
    # sys.exit(0)

    completion = openai.ChatCompletion.create(
      model="gpt-4",
      messages=[
          {"role": "system", "content": system_content},
          {"role": "user", "content": prompt},
        ]
    )

    return completion.choices[0].message

input = sys.stdin.read()
lines = input.split("\n")
del(lines[len(lines) - 1])

while len(lines) > 0:
    (insns, state) = [l.strip() for l in lines[0:2]]
    del(lines[0:2])
    print(state)
    print(insns)
    result = GetChatGPTResult(state, insns)
    print(result["content"])
