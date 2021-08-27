#!/usr/bin/python
import io
import sys


def run(num):
    """Touch files except Input "4"
    """
    if num == "4":
        raise Exception("I don't like 4.")
    with open(f"./artifacts/out_{num}.txt", "w") as f:
        f.write("")
    n = int(num)
    print(n * 2)


if __name__ == "__main__":
    run(sys.argv[1])
