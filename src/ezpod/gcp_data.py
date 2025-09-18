"""GCP instance information and helpers."""

from __future__ import annotations

import json
import os
import subprocess
from typing import List

from pydantic import BaseModel
from typing_extensions import Self

from ezpod.AddrEntry import AddrEntry
from ezpod.pod_group_info import PodGroupInfo
from ezpod.PodDataProtocol import InstanceData


class GCPNetworkInterface(BaseModel):
    network: str | None = None
    networkIP: str | None = None
    accessConfigs: list[dict] | None = None


class GCPInstanceData(BaseModel):
    """Subset of fields returned by ``gcloud compute instances list``."""

    id: str | int
    name: str
    zone: str
    status: str
    machineType: str
    networkInterfaces: list[GCPNetworkInterface]
    labels: dict[str, str] | None = None
    source_file: str = "~/.bashrc"

    # ------------------------------------------------------------------
    # Properties required by :class:`~ezpod.Pod` via :class:`InstanceData`
    # ------------------------------------------------------------------
    @property
    def podname(self) -> PodGroupInfo:
        return PodGroupInfo.from_str(self.name)

    @property
    def addrs(self) -> list[AddrEntry]:
        user = os.environ.get("EZPOD_GCP_USER", "ubuntu")
        key_path = os.environ.get(
            "EZPOD_GCP_KEY_PATH", "~/.ssh/google_compute_engine"
        )
        ip = ""
        if self.networkInterfaces:
            iface = self.networkInterfaces[0]
            if iface.accessConfigs:
                ip = iface.accessConfigs[0].get("natIP", "")
        return [
            AddrEntry(
                ip=ip,
                port=22,
                dst_port=22,
                pub="pub",
                proto="tcp",
                user=user,
                key_path=key_path,
                homedir=f"/home/{user}",
            )
        ]

    @property
    def sshaddr(self) -> AddrEntry:
        return self.addrs[0]

    @property
    def gpu_type(self) -> str:
        return self.machineType.split("/")[-1]

    @property
    def gpu_qty(self) -> int:
        return 0

    @property
    def status(self) -> str:  # already defined but for protocol clarity
        return self.__dict__["status"]

    @classmethod
    def get_all(cls) -> List[Self]:
        filter_expr = "labels.ezpod=true"
        cmd = (
            "gcloud compute instances list --format=json "
            f"--filter='{filter_expr}'"
        )
        out = subprocess.check_output(cmd, shell=True)
        data = json.loads(out)
        return [cls.model_validate(d) for d in data]

    def remove_pod(self):
        zone = self.zone.split("/")[-1]
        return subprocess.run(
            f"gcloud compute instances delete {self.name} --zone {zone} --quiet",
            shell=True,
            capture_output=True,
        )

    @property
    def is_running(self) -> bool:
        return self.status.lower() == "running"
