ARTIFACTS_DIR = "artifacts"
CONFIG_DIR = "config"
FILES_DIR = "files"
PROJECT_FILE = "project.yml"

BUCKET_CURRENT_PREFIX = "last"
BUCKET_ARCHIVE_PREFIX = "runs"

# environment variable keys (not the values)
BUCKET = "BUCKET"
DOCKER_IMAGE = "DOCKER_IMAGE"
IMAGE_DOMAIN = "IMAGE_DOMAIN"
IMAGE_VERSION = "IMAGE_VERSION"
RESOURCE_GROUP = "RESOURCE_GROUP"
TASK = "TASK"

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
}
