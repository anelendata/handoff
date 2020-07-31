import os
from handoff.config import RESOURCE_GROUP, TASK, DOCKER_IMAGE, BUCKET
from handoff.core.utils import env_check


def test_valid():
    os.environ[RESOURCE_GROUP] = "test-resource-0123"
    os.environ[TASK] = "test-task-0123"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[DOCKER_IMAGE] = "test-resource_0.123"
    env_check()


def test_missing_variable():
    del  os.environ[RESOURCE_GROUP]
    os.environ[TASK] = "test-task-0123"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[DOCKER_IMAGE] = "test-resource_0.123"
    try:
        env_check()
    except:
        pass
    else:
        assert False


def test_invalid_resource_group():
    os.environ[RESOURCE_GROUP] = "test-resource_0123"
    os.environ[TASK] = "test-task-0123"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[DOCKER_IMAGE] = "test-resource_0.123"
    try:
        env_check()
    except:
        pass
    else:
        assert False


def test_too_many_characters():
    os.environ[RESOURCE_GROUP] = "t" * 256
    os.environ[TASK] = "test-task-0123"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[DOCKER_IMAGE] = "test-resource_0.123"
    try:
        env_check()
    except:
        pass
    else:
        assert False


def test_too_few_characters():
    os.environ[RESOURCE_GROUP] = "test-resource-0123"
    os.environ[TASK] = "t"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[DOCKER_IMAGE] = "test-resource_0.123"
    try:
        env_check()
    except:
        pass
    else:
        assert False
