VERSION = "0.1.2a0"

ARTIFACTS_DIR = "artifacts"
CONFIG_DIR = "config"
FILES_DIR = "files"
PROJECT_FILE = "project.yml"

BUCKET_CURRENT_PREFIX = "last"
BUCKET_ARCHIVE_PREFIX = "runs"

ENV_PREFIX = "HO_"

# environment variable keys (not the values)
PROVIDER = ENV_PREFIX + "PROVIDER"
PLATFORM = ENV_PREFIX + "PLATFORM"

RESOURCE_GROUP = ENV_PREFIX + "RESOURCE_GROUP"
TASK = ENV_PREFIX + "TASK"
BUCKET = ENV_PREFIX + "BUCKET"

DOCKER_IMAGE = ENV_PREFIX + "DOCKER_IMAGE"
IMAGE_DOMAIN = ENV_PREFIX + "IMAGE_DOMAIN"
IMAGE_VERSION = ENV_PREFIX + "IMAGE_VERSION"

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
    DOCKER_IMAGE: {
        "pattern": "^[a-zA-Z0-9][a-zA-Z0-9_.-]*$",
        "min": 4,
        "max": 63
    },
    PROVIDER: {
    },
    PLATFORM: {
    }
}
