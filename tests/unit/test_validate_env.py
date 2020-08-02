import os
from handoff.config import (RESOURCE_GROUP, TASK, DOCKER_IMAGE, BUCKET,
                            PROVIDER, PLATFORM, get_state)


state = get_state()


def test_valid():
    os.environ[PROVIDER] = "aws"
    os.environ[PLATFORM] = "fargate"
    os.environ[RESOURCE_GROUP] = "test-resource-0123"
    os.environ[TASK] = "test-task-0123"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[DOCKER_IMAGE] = "test-resource_0.123"
    state.validate_env()


def test_missing_variable():
    os.environ[PROVIDER] = "aws"
    os.environ[PLATFORM] = "fargate"
    del  os.environ[RESOURCE_GROUP]
    os.environ[TASK] = "test-task-0123"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[DOCKER_IMAGE] = "test-resource_0.123"
    try:
        state.validate_env()
    except:
        pass
    else:
        assert False


def test_invalid_resource_group():
    os.environ[PROVIDER] = "aws"
    os.environ[PLATFORM] = "fargate"
    os.environ[RESOURCE_GROUP] = "test-resource_0123"
    os.environ[TASK] = "test-task-0123"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[DOCKER_IMAGE] = "test-resource_0.123"
    try:
        state.validate_env()
    except:
        pass
    else:
        assert False


def test_too_many_characters():
    os.environ[PROVIDER] = "aws"
    os.environ[PLATFORM] = "fargate"
    os.environ[RESOURCE_GROUP] = "t" * 256
    os.environ[TASK] = "test-task-0123"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[DOCKER_IMAGE] = "test-resource_0.123"
    try:
        state.validate_env()
    except:
        pass
    else:
        assert False


def test_too_few_characters():
    os.environ[PROVIDER] = "aws"
    os.environ[PLATFORM] = "fargate"
    os.environ[RESOURCE_GROUP] = "test-resource-0123"
    os.environ[TASK] = "t"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[DOCKER_IMAGE] = "test-resource_0.123"
    try:
        state.validate_env()
    except:
        pass
    else:
        assert False
