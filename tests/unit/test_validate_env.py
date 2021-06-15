import os
from handoff.config import (RESOURCE_GROUP, TASK, CONTAINER_IMAGE, BUCKET,
                            CLOUD_PROVIDER, CLOUD_PLATFORM,
                            CONTAINER_PROVIDER,
                            init_state, get_state)


def test_valid():
    init_state()
    state = get_state()
    os.environ[CLOUD_PROVIDER] = "aws"
    os.environ[CLOUD_PLATFORM] = "fargate"
    os.environ[CONTAINER_PROVIDER] = "docker"
    os.environ[RESOURCE_GROUP] = "test-resource-0123"
    os.environ[TASK] = "test-task-0123"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[CONTAINER_IMAGE] = "test-resource_0.123"
    state.validate_env()


def test_missing_variable():
    init_state()
    state = get_state()
    os.environ[CLOUD_PROVIDER] = "aws"
    os.environ[CLOUD_PLATFORM] = "fargate"
    del  os.environ[RESOURCE_GROUP]
    os.environ[TASK] = "test-task-0123"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[CONTAINER_IMAGE] = "test-resource_0.123"
    ret = state.validate_env()
    assert ret["status"] == "error"


def test_invalid_resource_group():
    init_state()
    state = get_state()
    os.environ[CLOUD_PROVIDER] = "aws"
    os.environ[CLOUD_PLATFORM] = "fargate"
    os.environ[RESOURCE_GROUP] = "test-resource_0123"
    os.environ[TASK] = "test-task-0123"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[CONTAINER_IMAGE] = "test-resource_0.123"
    state.validate_env()
    ret = state.validate_env()
    assert ret["status"] == "error"


def test_too_many_characters():
    init_state()
    state = get_state()
    os.environ[CLOUD_PROVIDER] = "aws"
    os.environ[CLOUD_PLATFORM] = "fargate"
    os.environ[RESOURCE_GROUP] = "t" * 256
    os.environ[TASK] = "test-task-0123"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[CONTAINER_IMAGE] = "test-resource_0.123"
    state.validate_env()
    ret = state.validate_env()
    assert ret["status"] == "error"


def test_too_few_characters():
    init_state()
    state = get_state()
    os.environ[CLOUD_PROVIDER] = "aws"
    os.environ[CLOUD_PLATFORM] = "fargate"
    os.environ[RESOURCE_GROUP] = "test-resource-0123"
    os.environ[TASK] = "t"
    os.environ[BUCKET] = "test-bucket.0123"
    os.environ[CONTAINER_IMAGE] = "test-resource_0.123"
    state.validate_env()
    ret = state.validate_env()
    assert ret["status"] == "error"
