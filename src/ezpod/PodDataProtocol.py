from abc import ABC, abstractmethod
import subprocess
from typing_extensions import Self
from pydantic import BaseModel
from ezpod.AddrEntry import AddrEntry
from ezpod.pod_group_info import PodGroupInfo


class PodDataProperties(BaseModel):
    """Concrete Pydantic model capturing static pod data fields."""

    id: str
    podname: PodGroupInfo
    addrs: list[AddrEntry]
    gpu_type: str
    gpu_qty: int
    name: str
    sshaddr: AddrEntry
    source_file: str
    status: str


type PDList[T: PodDataProtocol] = list[T]


class PodDataProtocol(ABC):
    """Abstract base for dynamic pod‑data implementations."""

    @classmethod
    @abstractmethod
    def get_all(cls) -> PDList:
        """Return all pod data instances for this backend."""
        ...

    @abstractmethod
    def remove_pod(self) -> subprocess.CompletedProcess:
        """Remove this pod in the backend."""
        ...

    @property
    @abstractmethod
    def properties(self) -> PodDataProperties:
        """Static pod data snapshot."""
        ...

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Whether the pod is running."""
        ...
