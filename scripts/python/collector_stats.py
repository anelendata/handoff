#!/usr/bin/python3
import io, json, logging, sys

LOGGER = logging.getLogger()

def collector_stats(outfile):
    """
    Read from stdin and count the lines. Output to a file after done.
    """
    lines = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    output = {"rows_read": 0}
    for line in lines:
        try:
            o = json.loads(line)
            print(json.dumps(o))
            if o["type"].lower() == "record":
                output["rows_read"] += 1
        except json.decoder.JSONDecodeError:
            print(line)
            output["rows_read"] += 1
    with open(outfile, "w") as f:
        json.dump(output, f)
        f.write("\n")


if __name__ == "__main__":
    collector_stats(".artifacts/collect_stats.json")
