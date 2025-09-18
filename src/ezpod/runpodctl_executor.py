import subprocess
from functools import wraps

from .backend_choice_env_var import BACKEND_AWS, BACKEND_GCP

from .shell_local_data import Account


def runpod_run(cmd):
    if BACKEND_AWS or BACKEND_GCP:
        raise NotImplementedError("runpod_run_output not implemented for this backend")
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


def runpod_info():
    if BACKEND_AWS or BACKEND_GCP:
        raise NotImplementedError("runpod_info not implemented for this backend")
    return runpod_run_output("get pod -a")
