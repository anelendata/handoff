"""Cloud credentials helpers that work for any platform."""
from handoff.utils import get_logger as _get_logger

LOGGER = _get_logger(__name__)


def refresh() -> None:
    """Renew the platform's temporary credentials before a late upload or
    download, if the platform supports it (its refresh_credentials()).

    A failure is logged, not raised: the current credentials may still work,
    and the call that needs them reports the real error.
    """
    from handoff.services.cloud import get_platform
    try:
        platform = get_platform()
    except Exception as e:
        LOGGER.warning(f"Credential refresh skipped: {e}")
        return
    fn = getattr(platform, "refresh_credentials", None)
    if fn is None:
        return
    try:
        LOGGER.info("Credentials: " + fn())
    except Exception as e:
        LOGGER.warning(f"Credential refresh failed, using the current credentials: {e}")
