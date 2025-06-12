import subprocess
import warnings
from functools import wraps

from .backend_aws_env_var import BACKEND_AWS

from .shell_local_data import Account

# LOGGED_IN_THIS_SESSION = False


# def log_in(key=None):
#     global LOGGED_IN_THIS_SESSION
#     LOGGED_IN_THIS_SESSION = True
#     account = load_account()
#     if key is None:
#         key = account.api_key
#     # if key is None:
#     #     key = os.environ.get("EZPOD_RUNPOD_API_KEY", None)
#     if key is not None:
#         r = subprocess.run(
#             f"runpodctl config --apiKey {key}",
#             shell=True,
#             check=True,
#             capture_output=True,
#         )
#         if r.stderr:
#             raise Exception(r.stderr.decode("utf-8"))
#     else:
#         warnings.warn(
#             "No EZPOD_RUNPOD_API_KEY environment variable found. Using existing runpodctl login."
#         )


# def runpod_login(fn):
#     @wraps(fn)
#     def wrapper(*args, **kwargs):
#         global LOGGED_IN_THIS_SESSION
#         if LOGGED_IN_THIS_SESSION:
#             return fn(*args, **kwargs)
#         log_in()
#         return fn(*args, **kwargs)

#     return wrapper


def runpod_run(cmd):
    if BACKEND_AWS:
        raise NotImplementedError("runpod_run_output not implemented for AWS")
    account = Account.load()
    key = account.api_key

    r = subprocess.run(
        f"RUNPOD_API_KEY={key} runpodctl {cmd}", shell=True, capture_output=True
    )
    return r


def runpod_run_output(cmd):
    r = runpod_run(cmd=cmd)
    if r.stderr:
        raise Exception(r.stderr.decode("utf-8"))
    return r.stdout.decode("utf-8")


# @runpod_login
def runpod_info():
    if BACKEND_AWS:
        raise NotImplementedError("runpod_info not implemented for AWS")
    return runpod_run_output("get pod -a")
    # r = subprocess.run("runpodctl get pod -a", shell=True, capture_output=True)
    # return r.stdout.decode("utf-8")


# @runpod_login
# def remove_pod(id: str) -> subprocess.CompletedProcess:
#     if BACKEND_AWS:
#         import boto3

#         ec2 = boto3.resource("ec2")
#         ec2.Instance(id).terminate()
#         return
#     return runpod_run(f"remove pod {id}")
#     # return subprocess.run(f"runpodctl remove pod {id}", shell=True, check=True)
