#!/usr/bin/python
import io, json, logging, sys, os

LOGGER = logging.getLogger()

def run():
    """Create long format
    """
    schema = {"type": "SCHEMA", "stream": "exchange_rate_long_format",
              "stream": "exchange_rate_long_format",
              "schema": {"type": "object",
                         "properties": {
                             "date": {"type": "string", "format": "date-time"},
                             "symbol": {"type": ["null", "string"]},
                             "rate": {"type": ["null", "number"]}}},
              "key_properties": ["date"]
              }
    print(json.dumps(schema))
    lines = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    for line in lines:
        o = json.loads(line)
        if o["type"].lower() != "record":
            if o["type"].lower() != "schema":
                print(json.dumps(o))
            continue
        record = o["record"]
        date = record["date"]
        for key in record.keys():
            if key == "date":
                continue
            r = {"type": "RECORD",
                 "stream": "exchange_rate_long_format",
                 "record": {"date": date, "symbol": key, "rate": record[key]}}
            print(json.dumps(r))


if __name__ == "__main__":
    run()
