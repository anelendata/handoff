import argparse, json

from impl import runner


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ETL.")
    parser.add_argument("command", type=str, help="command")
    parser.add_argument("-d", "--data", type=str, default="{}", help="Data required for the command as a JSON string")
    parser.add_argument("-p", "--parameter_file", type=str, default=None, help="Read parameters from file instead from remote store")
    parser.add_argument("-a", "--no_artifacts_upload", action="store_true", help="Don't upload artifacts to remote storage")

    args = parser.parse_args()
    command = args.command

    data_json = args.data
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError as e:
        data = json.loads(data_json[0:-1])

    upload_artifacts = args.no_artifacts_upload is False
    runner.run(command, data, args.parameter_file, upload_artifacts=upload_artifacts)
