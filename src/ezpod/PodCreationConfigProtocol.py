from typing import Protocol, ClassVar, Any
from typing_extensions import Self


class PodCreationConfigProtocol(Protocol):
    """Unified interface for all pod-creation backends."""

    config_ext: ClassVar[str]

    def create(self, name: str) -> Any: ...

    @classmethod
    def from_profile(cls, profile: str | None = None) -> Self: ...

    @classmethod
    def list_profiles(cls) -> list[str]: ...

    def save(self, name: str) -> None: ...

    @classmethod
    def interactive_make(cls) -> Self: ...
