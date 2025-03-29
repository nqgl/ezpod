import subprocess
from functools import wraps
import warnings
from .shell_local_data import load_account

LOGGED_IN_THIS_SESSION = False


def log_in(key=None):
    global LOGGED_IN_THIS_SESSION
    LOGGED_IN_THIS_SESSION = True
    account = load_account()
    key = account.api_key
    # if key is None:
    #     key = os.environ.get("EZPOD_RUNPOD_API_KEY", None)
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


def runpod_login(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        global LOGGED_IN_THIS_SESSION
        if LOGGED_IN_THIS_SESSION:
            return fn(*args, **kwargs)
        log_in()
        return fn(*args, **kwargs)

    return wrapper


@runpod_login
def runpod_info():
    r = subprocess.run("runpodctl get pod -a", shell=True, capture_output=True)
    return r.stdout.decode("utf-8")


@runpod_login
def remove_pod(id: str) -> subprocess.CompletedProcess:
    return subprocess.run(f"runpodctl remove pod {id}", shell=True, check=True)
