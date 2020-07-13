import sys, yaml

def list_installs(project_file):
    """
    Read in the project file and list the install commands and venv
    """
    with open(project_file, "r") as f:
        project = yaml.load(f, Loader=yaml.FullLoader)
    for command in project["commands"]:
        venv = command.get("venv", " ")
        for install in command.get("installs", []):
            print("%s, %s" % (venv, install))

if __name__ == "__main__":
    list_installs(sys.argv[1])
