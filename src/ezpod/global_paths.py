from pathlib import Path
import os
from ezpod.backend_choice_env_var import BACKEND_GCP


PROFILES_PATH = Path(
    os.environ.get("EZPOD_PROFILES_PATH", Path.home() / ".ezpod_profiles")
)


ACCOUNTS_PATH = PROFILES_PATH / "accounts"

POD_NAME_DELIMITER = "_" if not BACKEND_GCP else "-"
