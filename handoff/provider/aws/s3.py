import json, logging, os

import boto3

from . import credentials as cred


logger = logging.getLogger(__name__)


def get_client():
    return cred.get_client("s3")


def copy_dir_to_another_bucket(src_bucket, src_prefix, dest_bucket, dest_prefix):
    logger.info("Copying recursively from s3://%s/* to s3://%s/*" %
                (os.path.join(src_bucket, src_prefix), os.path.join(dest_bucket, dest_prefix)))
    client = get_client()
    keys = []
    next_token = ""
    base_kwargs = {
        "Bucket": src_bucket,
        "Prefix": src_prefix,
    }
    while next_token is not None:
        kwargs = base_kwargs.copy()
        if next_token != "":
            kwargs.update({"ContinuationToken": next_token})
        results = client.list_objects_v2(**kwargs)
        contents = results.get("Contents")

        next_token = results.get("NextContinuationToken")
        if not contents:
            logger.warning("Nothing found in the location")
            continue

        for i in contents:
            k = i.get("Key")
            if k[-1] == "/":
                continue

            # why doesn't os.path.join work with these?
            dest_path = dest_prefix + k[len(src_prefix):]

            keys.append(k)
            copy_source = {
                "Bucket": src_bucket,
                "Key": k
            }
            client.copy(copy_source, dest_bucket, dest_path)

            logger.info("Copied s3://%s to s3://%s" %
                        (os.path.join(src_bucket, k), os.path.join(dest_bucket, dest_path)))


def download_dir(prefix, local, bucket):
    """
    params:
    - prefix: pattern to match in s3
    - local: local path to folder in which to place files
    - bucket: s3 bucket with target contents

    Modified from: https://stackoverflow.com/a/56267603
    """
    client = get_client()
    logger.info("GET s3://" + bucket + "/" + prefix)
    keys = []
    dirs = []
    next_token = ""
    base_kwargs = {
        "Bucket":bucket,
        "Prefix":prefix,
    }
    while next_token is not None:
        kwargs = base_kwargs.copy()
        if next_token != "":
            kwargs.update({"ContinuationToken": next_token})
        results = client.list_objects_v2(**kwargs)
        contents = results.get("Contents")

        next_token = results.get("NextContinuationToken")
        if not contents:
            logger.warning("Nothing found in the location")
            continue

        for i in contents:
            k = i.get("Key")
            if k[-1] != "/":
                keys.append(k)
            else:
                dirs.append(k)

    for d in dirs:
        # Don't create root directory. Do local="./<prefix>" if you want it.
        dest_pathname = d[len(prefix):]
        dest_pathname = os.path.join(local, dest_pathname)
        if not os.path.exists(os.path.dirname(dest_pathname)):
            os.makedirs(os.path.dirname(dest_pathname))

    for k in keys:
        dest_pathname = k[len(prefix):]
        if dest_pathname[0] == "/":
            dest_pathname = dest_pathname[1:]
        dest_pathname = os.path.join(local, dest_pathname)
        if not os.path.exists(os.path.dirname(dest_pathname)):
            os.makedirs(os.path.dirname(dest_pathname))
        client.download_file(bucket, k, dest_pathname)


def upload_dir(source, prefix, bucket_name):
    """
    References:
    - https://boto3.amazonaws.com/v1/documentation/api/latest/guide/migrations3.html
    """
    client = get_client()

    # check if the bucket exists
    s3 = boto3.resource("s3")
    # raise if bucket does not exist
    s3.meta.client.head_bucket(Bucket=bucket_name)

    logger.info("Uploading %s to bucket %s" % (source, bucket_name))

    # construct the upload file list
    upload_file_names = []
    for root, dirs, files in os.walk(source, topdown=False):
       for name in files:
          fname = os.path.join(root, name)
          upload_file_names.append(fname)

    if not upload_file_names:
        logger.info("Nothing found in " + source)
        return

    logger.info("Files to be uploaded: %s" % upload_file_names)

    # start uploading
    for filename in upload_file_names:
        source_path = filename
        dest_path = os.path.join(prefix, filename[len(source) + 1:])
        logger.info("Uploading %s to Amazon S3 bucket %s" % (source_path, os.path.join(bucket_name, dest_path)))
        client.upload_file(source_path, bucket_name, dest_path)


def delete_object(bucket_name, key):
    """
    References:
    - https://boto3.amazonaws.com/v1/documentation/api/latest/guide/migrations3.html
    """
    client = get_client()

    # check if the bucket exists
    s3 = boto3.resource("s3")
    # raise if bucket does not exist
    s3.meta.client.head_bucket(Bucket=bucket_name)

    logger.info("Deleting %s from bucket %s" % (source, bucket_name))

    client.upload_file(bucket_name, key)



def delete_recurse(prefix, bucket):
    """
    params:
    - prefix: pattern to match in s3
    - local: local path to folder in which to place files
    - bucket: s3 bucket with target contents

    Modified from: https://stackoverflow.com/a/56267603
    """
    client = get_client()
    logger.info("GET s3://" + bucket + "/" + prefix)
    objects = []
    next_token = ''
    base_kwargs = {
        'Bucket':bucket,
        'Prefix':prefix,
    }
    while next_token is not None:
        kwargs = base_kwargs.copy()
        if next_token != '':
            kwargs.update({'ContinuationToken': next_token})
        results = client.list_objects_v2(**kwargs)
        next_token = results.get('NextContinuationToken')
        contents = results.get('Contents')

        if not contents:
            logger.warning("Nothing found in the location")
            continue

        for i in contents:
            objects.append({"Key": i.get("Key")})


    if objects:
        client.delete_objects(Bucket=bucket, Delete={"Objects": objects})

    logger.info("Deleted %s" % objects)
