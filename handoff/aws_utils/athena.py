#!/usr/bin/env python3
import logging, os, sys, time
import boto3

from aws_utils import credentials as cred

ATHENA_CLIENT = None


logger = logging.getLogger(__name__)


def get_database():
    """Get Athena database name
    DB name is defined as environment variable athena_database
    """
    return os.environ.get("athena_database", None)


def get_region():
    """Get the S3 bucket name used for writing output from Athena.
    s3 bucket name is defined as environment variable athena_output_bucket
    """
    return os.environ.get("athena_region", None)


def get_output_bucket():
    """Get the S3 bucket name used for writing output from Athena.
    s3 bucket name is defined as environment variable athena_output_bucket
    """
    return os.environ.get("athena_output_bucket", None)


def get_workgroup():
    """Get Athena workgroup name
    workgroup name is defined as environment variable athena_workgroup
    If not defined, it uses the default "primary"
    """
    return os.environ.get("athena_workgroup", "primary")


def get_client():
    global ATHENA_CLIENT
    if ATHENA_CLIENT:
        return ATHENA_CLIENT

    aws_access_key_id, aws_secret_access_key, aws_session_token, aws_default_region = cred.get_credentials()
    athena_region = get_region()
    boto_session = boto3.session.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=athena_region)
    ATHENA_CLIENT = boto_session.client("athena")
    return ATHENA_CLIENT


def submit_query(query, database, s3_output):
    """
    Submit query to Athena
    """
    client = get_client()
    response = client.start_query_execution(
        QueryString=query,
        # ClientRequestToken="string",
        QueryExecutionContext={
            "Database": database,
        },
        ResultConfiguration={
            "OutputLocation": s3_output,
            "EncryptionConfiguration": {
                "EncryptionOption": "SSE_S3",
                # "EncryptionOption": "SSE_S3"|"SSE_KMS"|"CSE_KMS",
                # "KmsKey": "string"
            }
        },
        # WorkGroup=workgroup
    )
    return response


def run_query(query, output_bucket=None, dry_run=False):
    database = get_database()
    if output_bucket is None:
        output_bucket = get_output_bucket()
    workgroup = get_workgroup()
    if dry_run:
        return {"QueryExecutionId": "dry_run",
                "client": client, "query": query, "database": database,
                "s3_bucket": output_bucket}
    response = submit_query(query, database, output_bucket)
    logger.info("Submitted query (query_id: %s)" % response["QueryExecutionId"])
    logger.debug("Query: " + query)
    return response


def read_query_from_file(filename):
    with open(filename, "r") as f:
        query = f.read().replace("\n", " ")
    return query


def get_query_status(query_execution_id):
    """
    Get the query execution status
    """
    client = get_client()
    response = client.get_query_execution(QueryExecutionId=query_execution_id)
    return response


def run_query_and_wait(query, output_bucket=None, timeout=600, check_interval=5):
    response = run_query(query, output_bucket)
    query_execution_id = response["QueryExecutionId"]

    # Wait for the completion.
    status = "QUEUED"
    logger.info("Waiting for query %s to complete." % query_execution_id)
    current_time = start_time = time.time()
    while status in ("RUNNING", "QUEUED") and current_time - start_time < timeout:
        current_time = time.time()
        sys.stdout.write(".")
        time.sleep(check_interval)
        response = get_query_status(query_execution_id)
        status = response["QueryExecution"]["Status"]["State"]
    if current_time - start_time >= timeout:
        logger.warn("run_query_and_wait: timed out after %d seconds." % timeout)
    return(response)


def fetch_result(query_execution_id, page_size=1000):
    """
    Fetch the result of the completed query
    TODO: Implement an option to fetch only a specified page
    """
    client = get_client()
    results_paginator = client.get_paginator('get_query_results')
    results_iter = results_paginator.paginate(
        QueryExecutionId=query_execution_id,
        PaginationConfig={
            'PageSize': page_size
        }
    )
    results = []
    data_list = []
    for results_page in results_iter:
        for row in results_page['ResultSet']['Rows']:
            data_list.append(row['Data'])
    for datum in data_list[0:]:
        results.append([x['VarCharValue'] for x in datum])
    return [tuple(x) for x in results]


if __name__ == '__main__':
    query = 'SHOW tables IN default'
    # or query = 'SELECT * FROM <your_table> LIMIT 100'
    print('Executing query: %s' % (query))

    response = run_query_and_wait(query)
    print(response)

    query_execution_id = response["QueryExecution"]["QueryExecutionId"]

    print(fetch_result(query_execution_id))
