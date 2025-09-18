import os
import subprocess
from typing import ClassVar

from typing_extensions import Self

from ezpod.BasePodCreationConfig import BasePodCreationConfig
import google.cloud.compute_v1 as gcp


class StringedAttribs:
    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, name):
        if name.startswith("_"):
            return super().__getattr__(name)


class GCPPodCreationConfig(BasePodCreationConfig):
    """Configuration for launching a Google Cloud Compute Engine instance."""

    config_ext: ClassVar[str] = "gcp.json"

    zone: str = os.environ.get("EZPOD_GCP_ZONE", "us-west1-a")
    machine_type: str = os.environ.get("EZPOD_GCP_MACHINE_TYPE", "a3-highgpu-1g")
    image_project: str = os.environ.get("EZPOD_GCP_IMAGE_PROJECT", "ubuntu-os-cloud")
    image_family: str = os.environ.get("EZPOD_GCP_IMAGE_FAMILY", "ubuntu-2204-lts")
    disk_size: int = int(os.environ.get("EZPOD_GCP_DISK_SIZE", 50))  # GiB

    def _create_impl(self, name: str):  # type: ignore[override]
        """Create a Compute Engine instance using the gcloud CLI."""

        zone_arg = f"--zone {self.zone}" if self.zone else ""
        cmd = (
            f"gcloud compute instances create {name} "
            f"{zone_arg} "
            f"--machine-type {self.machine_type} "
            f"--image-project {self.image_project} "
            f"--image-family {self.image_family} "
            f"--boot-disk-size {self.disk_size} "
            f"--labels=ezpod=true"
        )
        print(f"gcp create instance {name}: {cmd}")

        p = subprocess.run(cmd, shell=True, capture_output=True)
        if p.stderr:
            raise Exception(p.stderr.decode("utf-8"))
        print(f"result: {p.stdout.decode('utf-8')}")
        return p

    @classmethod
    def interactive_make(cls) -> Self:  # pragma: no cover - user interaction
        default = cls()
        zone = input(f"Zone (default: {default.zone}): ") or default.zone
        machine_type = (
            input(f"Machine type (default: {default.machine_type}): ")
            or default.machine_type
        )
        image_project = (
            input(f"Image project (default: {default.image_project}): ")
            or default.image_project
        )
        image_family = (
            input(f"Image family (default: {default.image_family}): ")
            or default.image_family
        )
        disk_size = (
            input(f"Disk size GB (default: {default.disk_size}): ") or default.disk_size
        )
        return cls(
            zone=zone,
            machine_type=machine_type,
            image_project=image_project,
            image_family=image_family,
            disk_size=int(disk_size),
        )
