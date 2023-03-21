#!/usr/bin/env python3

import sys
import os
import openai
import time
import random

openai.api_key = os.getenv("OPENAI_API_KEY")

with open("prompt.txt", "r") as prompts:
    system_content = prompts.readline()
    preamble = prompts.read()

# From https://platform.openai.com/docs/guides/rate-limits/error-mitigation
# define a retry decorator
def retry_with_exponential_backoff(
    func,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 10,
    rate_errors: tuple = (openai.error.RateLimitError,),
    retry_errors: tuple = (openai.error.APIConnectionError,openai.error.Timeout,),
):
    """Retry a function with exponential backoff."""

    def wrapper(*args, **kwargs):
        # Initialize variables
        num_retries = 0
        delay = initial_delay

        # Loop until a successful response or max_retries is hit or an exception is raised
        while True:
            try:
                return func(*args, **kwargs)

            # Retry on specific errors
            except rate_errors as e:
                # Increment retries
                num_retries += 1

                # Check if max retries has been reached
                if num_retries > max_retries:
                    raise Exception(
                        f"Maximum number of retries ({max_retries}) exceeded."
                    )

                # Increment the delay
                delay *= exponential_base * (1 + jitter * random.random())

                # Sleep for the delay
                time.sleep(delay)

	    # Brad added this after receiving many APIConnectionError
	    # and Timeout during the initial weeks of gpt-4
            except retry_errors as e:
                # Increment retries
                num_retries += 1

                # Check if max retries has been reached
                if num_retries > max_retries:
                    raise Exception(
                        f"Maximum number of retries ({max_retries}) exceeded."
                    )

                # Sleep for the delay
                time.sleep(10.0)

            # Raise exceptions for any errors not specified
            except Exception as e:
                raise e

    return wrapper

@retry_with_exponential_backoff
def GetChatGPTResult(state_string, insn_bytes_string):
    prompt = '''%s

Set state to %s
%s
''' % (preamble, state_string, insn_bytes_string)

    # print("%s" % prompt)
    # sys.exit(0)

    completion = openai.ChatCompletion.create(
      model="gpt-4",
      temperature=0.0,
      messages=[
          {"role": "system", "content": system_content},
          {"role": "user", "content": prompt},
        ]
    )

    return completion.choices[0].message


