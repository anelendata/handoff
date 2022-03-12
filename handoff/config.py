VERSION = "0.3.4"
VERSION_MINOR = ".".join(VERSION.split(".")[0:2])

import datetime, os, re
from handoff import utils

LOGGER = utils.get_logger(__name__)

APP_PREFIX = "handoff"
HANDOFF_DIR = ".handoff"
ARTIFACTS_DIR = "artifacts"
BUNDLES_DIR = "bundles"
TEMPLATES_DIR = "templates"
FILES_DIR = "files"
PROJECT_FILE = "project.yml"
SECRETS_DIR = ".secrets"
SECRETS_FILE = "secrets.yml"

BUCKET_CURRENT_PREFIX = "last"
BUCKET_ARCHIVE_PREFIX = "archives"

ENV_PREFIX = "HO_"

DEFAULT_STAGE = "dev"

# environment variable keys (not the values)
STAGE = ENV_PREFIX + "STAGE"
CLOUD_PROVIDER = ENV_PREFIX + "CLOUD_PROVIDER"
CLOUD_PLATFORM = ENV_PREFIX + "CLOUD_PLATFORM"

CONTAINER_PROVIDER = ENV_PREFIX + "CONTAINER_PROVIDER"

RESOURCE_GROUP = ENV_PREFIX + "RESOURCE_GROUP"
RESOURCE_GROUP_NAKED  = ENV_PREFIX + "RESOURCE_GROUP_NAKED"
TASK = ENV_PREFIX + "TASK"
TASK_NAKED = ENV_PREFIX + "TASK_NAKED"
BUCKET = ENV_PREFIX + "BUCKET"

CONTAINER_IMAGE = ENV_PREFIX + "CONTAINER_IMAGE"
IMAGE_DOMAIN = ENV_PREFIX + "IMAGE_DOMAIN"
IMAGE_VERSION = ENV_PREFIX + "IMAGE_VERSION"

GITHUB_ACCESS_TOKEN = "GITHUB_ACCESS_TOKEN"


ADMIN_ENVS = {
    RESOURCE_GROUP: {
        "pattern": "^[a-zA-Z][a-zA-Z0-9-]*$",
        "min": 3,
        "max": 128
    },
    TASK: {
        "pattern": "^[a-zA-Z][a-zA-Z0-9-]*$",
        "min": 3,
        "max": 128
    },
    BUCKET: {
        "pattern": "^[a-z0-9][a-z0-9.-]*$",
        "min": 4,
        "max": 63
    },
    CONTAINER_IMAGE: {
        "pattern": "^[a-zA-Z0-9][a-zA-Z0-9_.-]*$",
        "min": 4,
        "max": 63
    },
    CLOUD_PROVIDER: {
    },
    CLOUD_PLATFORM: {
    },
    CONTAINER_PROVIDER: {
    },
    STAGE: {
    }
}

SAFE_ENVS = {
    "AWS_REGION": {
        "pattern": "^[a-z][a-z0-9-]*$",
        "min": 4,
        "max": 63
    },
    IMAGE_VERSION: {}
}


class State(dict):
    """
    Central-manage the environment variables and in-memory states

    - in-memory key-values are accessed like a regular dict object.
    - env vars are accessed via set/get_env methods only.
    - env vars are not copied to in-memory key-values.
    - env vars are whitelisted and validated before they are set.
    """
    def __init__(self, *args, **kwargs):
        super(State, self).__init__(*args,  **kwargs)
        self._mandatory_envs = ADMIN_ENVS
        self._allowed_envs = {**self._mandatory_envs, **SAFE_ENVS}

    def __getitem__(self, key):
        """Get value
        First look up in-memory key. Tries to return env var if not in memory
        """
        v = super(State, self).get(key, self.get_env(key))
        return v

    def get(self, key, sub=None):
        ret = self.__getitem__(key)
        if not ret:
            ret = sub
        return ret

    def unset(self, key):
        """Erases both from memoery and env var
        """
        if super(State, self).get(key):
            super(State, self).pop(key)
        if os.environ.get(key):
            del os.environ[key]

    def is_allowed_env(self, key):
        return key in self._allowed_envs.keys()

    def set_env(self, key, value, trust=False):
        if not trust and not self.is_allowed_env(key):
            raise KeyError(key + " is not whitelisted for env var usage.")
        self.unset(key)
        self[key] = value
        os.environ[key] = value

    def get_env(self, name):
        return os.environ.get(name)

    def validate_env(self, keys=None):
        """
        Check if env vars are present and valid
        """
        invalid = list()
        if not keys:
            keys = self._mandatory_envs.keys()
        for env in keys:
            value = self.get(env)
            if not value:
                msg = env + " environment variable is not defined."
                if self._mandatory_envs.get(env, dict()).get("pattern"):
                    msg = (msg + " Valid pattern: " +
                           self._mandatory_envs[env]["pattern"])
                LOGGER.error(msg)
                invalid.append(env)
                continue
            is_valid = (
                (not self._mandatory_envs.get(env, dict()).get("pattern") or
                 bool(re.fullmatch(self._mandatory_envs[env]["pattern"],
                                   value))) and
                (not self._mandatory_envs.get(env, dict()).get("min") or
                 self._mandatory_envs[env]["min"] <= len(value)) and
                (not self._mandatory_envs.get(env, dict()).get("max") or
                 self._mandatory_envs[env]["max"] >= len(value)))
            if not is_valid:
                LOGGER.error(("%s environment variable is not following" +
                                 " the pattern %s. value: %s") %
                                (env, self._mandatory_envs[env], value))
                invalid.append(env)
        if invalid:
            ms = ("Invalid environment variables: %s\n" % invalid +
                  "1. Check if you properly defined environment variables " +
                  "  such as AWS_PROFILE.\n" +
                  f"  https://dev.handoff.cloud/en/v{VERSION_MINOR}" +
                  "/guided_tour.html#setting-up-an-aws-account-and-profile\n" +
                  "2. Check if necessary variables are defined in " +
                  "the project file.\n" +
                  f"  https://dev.handoff.cloud/en/v{VERSION_MINOR}" +
                  "/quick_reference.html")
            return {
                "status": "error",
                "message": ms,
                }

        return {
            "status": "success"
        }

STATE = None


def init_state(stage=DEFAULT_STAGE):
    global STATE
    STATE = State()
    if stage == "prod":
        STATE["_stage"] = ""
        STATE["_stage_"] = ""
        STATE["_stage-"] = ""
        STATE["__stage"] = ""
        STATE["__stage_"] = ""
    else:
        STATE["_stage"] = stage
        STATE["_stage_"] = stage + "_"
        STATE["_stage-"] = stage + "-"
        STATE["__stage"] = "_" + stage
        STATE["__stage_"] = "_" + stage + "_"
    STATE["_today"] = datetime.date.today().isoformat()
    STATE["_yesterday"] = (
        datetime.date.today() + datetime.timedelta(days=-1)).isoformat()
    STATE["_tomorrow"] = (
        datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    STATE.set_env(STAGE, stage)


def get_state():
    global STATE
    if not STATE:
        raise Exception("state needs to be initialized with init_state")
    return STATE
