import datetime, json, logging, os
import boto3
import dateutil.parser
import requests

logger = logging.getLogger(__name__)

CLIENTS = dict()


def fetch_container_credentials(rel_uri: str) -> dict:
    """The task role's current credentials from the ECS endpoint.
    See https://docs.aws.amazon.com/AmazonECS/latest/userguide/task-iam-roles.html
    """
    response = requests.get("http://169.254.170.2" + rel_uri, timeout=10)
    response.raise_for_status()
    return json.loads(response.content)


def _get_credentials(cred: dict = {}):
    """
    In AWS instance, AWS credentials are either retrieved from credentials local endpoint
    """
    rel_uri = os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")

    if not cred and rel_uri:
        task_cred = fetch_container_credentials(rel_uri)
        logger.debug("Role ARN: " + task_cred["RoleArn"])
        logger.debug("Set AWS credentials from " +
                     "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
        # Standardize the key names
        cred["aws_access_key_id"] = task_cred["AccessKeyId"]
        cred["aws_secret_access_key"] = task_cred["SecretAccessKey"]
        cred["aws_session_token"] = task_cred["Token"]
        # cred["aws_role_arn"] = task_cred["RoleArn"]

    if not cred.get("region_name") and cred.get("aws_region"):
        cred["region_name"] = cred["aws_region"]

    return cred


def _get_boto3_session_kwargs(params):
    kwargs = {}
    valid_boto3_session_keys = [
        "aws_access_key_id",
        "aws_secret_access_key",
        "aws_session_token",
        "region_name",
        "botocore_session",
        "profile_name",
    ]
    for key in params.keys():
        if key in valid_boto3_session_keys:
            kwargs[key] = params[key]
    return kwargs


def get_session(cred_keys: dict = {}):
    cred_keys = _get_credentials(cred_keys)
    kwargs = _get_boto3_session_kwargs(cred_keys)
    session = boto3.session.Session(**kwargs)
    return session


def get_client(service, cred_keys: dict = {}):
    global CLIENTS
    # Disabling cache as it is doing strange bug
    # if CLIENTS.get(service):
    #   return CLIENTS[service]
    session = get_session(cred_keys)
    CLIENTS[service] = session.client(service)
    return CLIENTS[service]




# How this run assumed a role, kept in memory only (never in state, logs or
# files), so refresh() can assume it again before a late upload.
_ASSUMED_ROLE = dict()
# Refresh when less than this is left. Fetching task-role credentials is a local
# call, so those are always refreshed.
REFRESH_MARGIN = datetime.timedelta(minutes=15)


def remember_assumed_role(role_arn, external_id, source_cred_keys, response):
    _ASSUMED_ROLE.clear()
    _ASSUMED_ROLE.update({
        "role_arn": role_arn,
        "external_id": external_id,
        "source_cred_keys": dict(source_cred_keys),
        "expiration": response["Credentials"].get("Expiration"),
    })


def store_role_credentials(state, response):
    state["AWS_ACCESS_KEY_ID"] = response["Credentials"]["AccessKeyId"]
    state["AWS_SECRET_ACCESS_KEY"] = response["Credentials"]["SecretAccessKey"]
    state["AWS_SESSION_TOKEN"] = response["Credentials"]["SessionToken"]


def _as_utc(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = dateutil.parser.parse(value)
    if value.tzinfo is None:
        value = value.replace(tzinfo=datetime.timezone.utc)
    return value


def refresh(state) -> str:
    """Renew the temporary AWS credentials in state before a late S3 call.

    handoff copies credentials into its state at login, and every later call
    reuses that copy, so a long job can outlive them and fail at its final
    upload. In a container, fetch the task role's current credentials again
    from the ECS endpoint. If the run assumed a role, assume it again when it
    expires within REFRESH_MARGIN. Long-lived keys and profiles need nothing.
    Returns what was done, for the log. Never logs the credentials.
    """
    rel_uri = os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
    if rel_uri and not _ASSUMED_ROLE:
        task_cred = fetch_container_credentials(rel_uri)
        state["AWS_ACCESS_KEY_ID"] = task_cred["AccessKeyId"]
        state["AWS_SECRET_ACCESS_KEY"] = task_cred["SecretAccessKey"]
        state["AWS_SESSION_TOKEN"] = task_cred["Token"]
        return f"task role credentials refreshed (expire {task_cred.get('Expiration')})"
    if _ASSUMED_ROLE:
        expiration = _as_utc(_ASSUMED_ROLE.get("expiration"))
        now = datetime.datetime.now(datetime.timezone.utc)
        if expiration and expiration - now > REFRESH_MARGIN:
            return f"assumed role credentials still valid until {expiration.isoformat()}"
        from . import sts  # sts imports this module
        source = dict(_ASSUMED_ROLE["source_cred_keys"])
        response = sts.assume_role(_ASSUMED_ROLE["role_arn"],
                                   external_id=_ASSUMED_ROLE["external_id"],
                                   cred_keys=source)
        remember_assumed_role(_ASSUMED_ROLE["role_arn"], _ASSUMED_ROLE["external_id"],
                              source, response)
        store_role_credentials(state, response)
        return f"assumed role again (expire {_ASSUMED_ROLE.get('expiration')})"
    return "long-lived credentials, nothing to refresh"
