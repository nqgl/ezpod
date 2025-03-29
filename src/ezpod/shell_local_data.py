# common_state_utils.py
from argparse import Action
import os
import tempfile
from pathlib import Path
from pydantic import BaseModel
from .global_paths import ACCOUNTS_PATH, PROFILES_PATH

STATE_DIR = Path(tempfile.gettempdir()) / "ezpod_shell_states" / f"shell_{os.getppid()}"
STATE_DIR.mkdir(parents=True, exist_ok=True)
account_path = STATE_DIR / "account.state"
profile_path = STATE_DIR / "profile.state"


class Account(BaseModel):
    api_key: str


def save_account(name: str, account: Account):
    ACCOUNTS_PATH.mkdir(parents=True, exist_ok=True)
    (ACCOUNTS_PATH / name).write_text(account.model_dump_json())


def load_account(name: str | None = None) -> Account:
    if name is None:
        return load_account(current_account_name())
    return Account.model_validate_json((ACCOUNTS_PATH / name).read_text())


def current_account_name():
    if "EZPOD_ACCOUNT_OVERRIDE" in os.environ:
        return os.environ["EZPOD_ACCOUNT_OVERRIDE"]
    if not account_path.exists():
        return "default"
    return account_path.read_text().strip()


def set_current_account(account: str):
    account_path.write_text(account)


def current_profile_name():
    if "EZPOD_PROFILE_OVERRIDE" in os.environ:
        return os.environ["EZPOD_PROFILE_OVERRIDE"]
    if not profile_path.exists():
        return None
    return profile_path.read_text().strip()


def set_current_profile(profile: str | None):
    if profile is None:
        profile_path.unlink(missing_ok=True)
    else:
        profile_path.write_text(profile)


def acct_profiles() -> Path:
    path = PROFILES_PATH / current_account_name()
    path.mkdir(parents=True, exist_ok=True)
    return path


def flexible_login(name: str):
    if "/" in name:
        acct, profile = name.split("/")
        set_current_account(acct)
        set_current_profile(profile)
    else:
        set_current_account(name)
