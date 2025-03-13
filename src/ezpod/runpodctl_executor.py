import subprocess
from functools import wraps
import os
import warnings


def runpod_login(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        key = os.environ.get("EZPOD_RUNPOD_API_KEY", None)
        if key is not None:
            r = subprocess.run(
                f"runpodctl config --apiKey {key}",
                shell=True,
                check=True,
                capture_output=True,
            )
            if r.stderr:
                raise Exception(r.stderr.decode("utf-8"))
        else:
            warnings.warn(
                "No EZPOD_RUNPOD_API_KEY environment variable found. Using existing runpodctl login."
            )
        return fn(*args, **kwargs)

    return wrapper


@runpod_login
def runpod_info():
    r = subprocess.run("runpodctl get pod -a", shell=True, capture_output=True)
    return r.stdout.decode("utf-8")


@runpod_login
def remove_pod(id: str) -> subprocess.CompletedProcess:
    return subprocess.run(f"runpodctl remove pod {id}", shell=True, check=True)
