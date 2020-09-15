import datetime, json, logging, os, re, sys
from dateutil.parser import parse as dateparse
import attr


LOGGER = None


def get_logger(name="handoff"):
    global LOGGER
    if not LOGGER:
        logging.basicConfig(
            stream=sys.stdout,
            format="[%(asctime)s] [%(levelname)8s] - %(message)s - (%(filename)s:%(lineno)s)",
            level=logging.INFO)
        LOGGER = logging.getLogger(name)
    return LOGGER


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def time_trunc(org_datetime, by='minute'):
    """Convenience function to truncate the timestamp by the specified unit"""
    if by not in ['year', 'month', 'day', 'hour', 'minute', 'second']:
        raise ValueError('Invalid time unit for truncation')
    t_elems = {'year': org_datetime.year, 'month': org_datetime.month,
               'day': org_datetime.day,
               'hour': org_datetime.hour, 'minute': org_datetime.minute,
               'second': org_datetime.second,
               'microsecond': org_datetime.microsecond}
    # Fix for Python 3.x: It does not honor the original key order of the dict
    keys = ["year", "month", "day", "hour", "minute", "second", "microsecond"]
    found = False
    for k in keys:
        if found:
            t_elems[k] = 1 if k in ['month', 'day'] else 0
        if k == by:
            found = True
    return datetime.datetime(**t_elems)


def get_time_window(data,
                    date_trunc="day",
                    start_offset=datetime.timedelta(days=0),
                    end_offset=datetime.timedelta(days=1),
                    iso_str=True):
    """
    Check the input data for start_at and end_at.
    If not present, determine them by relative time from now.
    Returns the ISO formatted strings in UTC.

    - data: A dictionary that may or may not contain "start_at" and "end_at"
    - date_trunc: "day", "hour", "minute" to truncate the time.
    - start_offset: Usually a negative timedelta to go back in time from now.
    - end_offset: Timedelta from start_at to determine the window. The exact
      end_at is not included in the data point.
    """
    start_at = data.get("start_at")
    end_at = data.get("end_at")

    if type(start_at) == str:
        start_at = dateparse(start_at)
    if type(end_at) == str:
        end_at = dateparse(end_at)

    if type(start_at) != datetime.datetime:
        # Time-truncated version of now
        now = time_trunc(datetime.datetime.utcnow(), date_trunc)
        start_at = now + start_offset

    if type(end_at) != datetime.datetime:
        end_at = start_at + end_offset

    if (type(start_at) == datetime.datetime and
            type(end_at) == datetime.datetime):
        if start_at >= end_at:
            raise ValueError("start_at must be strictly earlier than end_at")
        if iso_str:
            return start_at.isoformat(), end_at.isoformat()
        return start_at, end_at

    raise ValueError("Something went wrong determining start_at and end_at")


def get_python_info(module=__file__):
    python_exec = sys.executable
    lib_dir = os.path.dirname(os.path.realpath(attr.__file__))
    work_dir = os.getcwd()
    code_dir = os.path.dirname(os.path.realpath(module))
    python_info = {"python": python_exec,
                   "python_lib_dir": lib_dir,
                   "work_dir": work_dir,
                   "code_dir": code_dir
                   }

    return python_info
