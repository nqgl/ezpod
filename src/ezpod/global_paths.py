from pathlib import Path
import os


PROFILES_PATH = Path(
    os.environ.get("EZPOD_PROFILES_PATH", Path.home() / ".ezpod_profiles")
)


ACCOUNTS_PATH = PROFILES_PATH / "accounts"
