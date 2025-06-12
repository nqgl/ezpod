from abc import ABC, abstractmethod

from pydantic import BaseModel
from typing_extensions import Self

from ezpod.shell_local_data import acct_profiles, current_profile_name

# Optional boto3 import – only required when using the AWS backend
try:
    import boto3
except (
    ModuleNotFoundError
):  # pragma: no cover – boto3 might not be installed in minimal setups
    boto3 = None  # type: ignore


class BasePodCreationConfig(BaseModel, ABC):
    """Abstract base class for cluster/pod/instance creation.

    Concrete back‑ends (RunPod, AWS, …) should inherit from this class and
    implement :py:meth:`create_pod`.
    """

    config_ext: str = "json"

    @abstractmethod  # pragma: no cover – must be implemented by subclasses
    def _create_impl(self, name: str):
        """Subclasses implement their own creation logic and return a backend‑
        specific identifier (e.g. pod ID or EC2 instance ID)."""

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def create(self, name: str):  # noqa: D401 – imperative verb OK here
        """Create a new node/instance/pod.

        This unified entry‑point lets the higher‑level *ezpod* code stay backend
        agnostic.  Subclasses only need to implement :py:meth:`_create_impl`.
        """

        return self._create_impl(name)

    @classmethod
    def from_profile(cls, profile: str | None = None):
        if profile is None:
            profile = current_profile_name()
            # profile = os.environ.get("EZPOD_PROFILE", None)
        if profile is None:
            return cls()
        cfg_path = acct_profiles() / f"{profile}.{cls.config_ext}"
        return cls.model_validate_json(cfg_path.read_text())

    @classmethod
    def list_profiles(cls) -> list[str]:
        return [
            p.name
            for p in acct_profiles().iterdir()
            if p.is_file() and p.suffix == cls.config_ext
        ]

    def save(self, name):
        path = acct_profiles() / f"{name}.{self.config_ext}"
        if path.exists():
            raise ValueError(f"Profile {name} already exists")
        path.write_text(self.model_dump_json())

    @classmethod
    @abstractmethod
    def interactive_make(cls) -> Self: ...
