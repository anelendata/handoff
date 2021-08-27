#!/usr/bin/python
import io
import sys


def run():
    """Touch files except Input "4"
    """
    lines = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    for line in lines:
        line = line.strip()
        if line == "4":
            raise Exception("I don't like 4.")
        with open(f"./artifacts/out_{line}.txt", "w") as f:
            f.write("")
    print(line)


if __name__ == "__main__":
    run()
