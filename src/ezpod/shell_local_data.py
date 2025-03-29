# common_state_utils.py
from argparse import Action
import os
import tempfile
from pathlib import Path
from typing import ClassVar
from pydantic import BaseModel
from .global_paths import ACCOUNTS_PATH, PROFILES_PATH
import subprocess
import toml

STATE_DIR = Path(tempfile.gettempdir()) / "ezpod_shell_states" / f"shell_{os.getppid()}"
STATE_DIR.mkdir(parents=True, exist_ok=True)
account_path = STATE_DIR / "account.state"
profile_path = STATE_DIR / "profile.state"


def runpodctl_log_in(key: str):
    r = subprocess.run(
        f"runpodctl config --apiKey {key}",
        shell=True,
        check=True,
        capture_output=True,
    )
    if r.stderr:
        raise Exception(r.stderr.decode("utf-8"))


# class RunpodConfigState(BaseModel):
#     config_text: str
#     private_key: str
#     public_key: str

#     runpod_cfg_dir: ClassVar[Path] = Path.home() / ".runpod"
#     runpod_cfg_ssh_dir: ClassVar[Path] = runpod_cfg_dir / "ssh"
#     private_key_path: ClassVar[Path] = runpod_cfg_ssh_dir / "RunPod-Key-Go"
#     public_key_path: ClassVar[Path] = runpod_cfg_ssh_dir / "RunPod-Key-Go.pub"
#     config_path: ClassVar[Path] = runpod_cfg_dir / "config.toml"

#     @classmethod
#     def read_from_filesystem(cls, assert_apikey=None):
#         assert len(list(cls.runpod_cfg_ssh_dir.glob("*"))) == 2
#         private_key = cls.private_key_path.read_text()
#         public_key = cls.public_key_path.read_text()
#         config = cls.config_path.read_text()
#         config_parsed = toml.loads(config)
#         assert (
#             len(config_parsed.keys()) == 2
#             and "apikey" in config_parsed
#             and "apiurl" in config_parsed
#         )
#         assert config_parsed["apikey"] == assert_apikey
#         return cls(
#             config_text=config,
#             private_key=private_key,
#             public_key=public_key,
#         )

#     def write_to_filesystem(self):
#         self.private_key_path.write_text(self.private_key)
#         self.public_key_path.write_text(self.public_key)
#         self.config_path.write_text(self.config_text)


class Account(BaseModel):
    api_key: str
    default_group: str | None = None

    def save(self, name: str):
        ACCOUNTS_PATH.mkdir(parents=True, exist_ok=True)
        path = ACCOUNTS_PATH / name
        if path.exists():
            raise ValueError(f"Account {name} already exists")
        path.write_text(self.model_dump_json())

    @classmethod
    def load(cls, name: str | None = None) -> "Account":
        if name is None:
            return cls.load(current_account_name())
        path = ACCOUNTS_PATH / name
        if not path.exists():
            if name == "default":
                print("Default account does not exist, creating...")
                input(
                    "The 'default' profile will be used when an account is not otherwise specified!\nYou can delete/modify it in ~/.ezpod_profiles/accounts if needed. \nPress enter to acknowledge and create 'default'."
                )
                cls.interactive_create(name)
                return cls.load(name)
            raise ValueError(f"Account {name} does not exist")
        return cls.model_validate_json(path.read_text())

    @classmethod
    def interactive_create(cls, name: str | None = None):
        if name is not None:
            print(f"Creating account with name {name}")
        else:
            name = input("Account name: ")
        group = input("Default group (leave empty for no group/all pods): ")
        assert (
            "_" not in group and "pod" not in group
        ), "Group name should not contain '_' or 'pod'"
        api_key = input("RunPod API key: ")

        account = Account(api_key=api_key, default_group=group or None)
        account.save(name)


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
        if (acct_profiles() / "default").exists():
            return "default"
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
