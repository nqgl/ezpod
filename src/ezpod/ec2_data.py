"""AWS EC2 instance metadata wrapper mirroring the runpod *PodData* API.

This module lets the rest of *ezpod* reuse the same logic (Pod / Pods, etc.)
for AWS‑backed clusters by exposing a *PodData*-compatible class built from
EC2 instance information.

Instances are identified via the tag ``EzPod=true`` – this tag is automatically
added when launching new instances through :pyclass:`~ezpod.create_pods.AWSPodCreationConfig`.
"""

from __future__ import annotations

import subprocess
from typing import Any

from pydantic import BaseModel
from typing_extensions import Self

from ezpod.AddrEntry import AddrEntry
from ezpod.PodDataProtocol import PodDataProtocol, PodDataProperties
from ezpod.aws_models.ec2.describe_instances import Tag
from ezpod.pod_group_info import PodGroupInfo


class EC2State(BaseModel):
    Name: str
    Code: int


class EC2InstanceData(BaseModel, PodDataProtocol):
    Architecture: str
    # BlockDeviceMappings: list[BlockDeviceMapping]
    ClientToken: str
    # EbsOptimized
    # EnaSupport: bool
    Hypervisor: str
    ImageId: str
    InstanceId: str
    # SecurityGroups: list[SecurityGroup]
    PrivateDnsName: str
    PublicDnsName: str
    KeyName: str
    InstanceType: str
    State: EC2State
    SubnetId: str | None = None
    VpcId: str | None = None
    PrivateIpAddress: str | None = None
    PublicIpAddress: str | None = None
    Tags: list[Tag] | None = None

    @property
    def tags(self):
        if self.Tags is None:
            return {}
        return {t.key: t.value for t in self.Tags}

    @classmethod
    def model_validate_jsonl(cls, json_str: str) -> "EC2InstanceData":
        # Historical helper kept for compatibility (json lines not currently required)
        return cls.model_validate_json(json_str)

    @property
    def podname(self) -> PodGroupInfo:
        return PodGroupInfo.from_str(self.name)

    @property
    def name(self) -> str:
        # Safely handle non-str/None tag values
        tag_name = self.tags.get("Name") if self.tags else None
        if isinstance(tag_name, str) and tag_name:
            return tag_name
        return self.InstanceId

    @property
    def id(self) -> str:
        return self.InstanceId

    @property
    def addrs(self) -> list[AddrEntry]:
        return [
            AddrEntry(
                ip=self.PublicIpAddress or "",
                port=22,
                dst_port=22,
                pub="pub",
                proto="tcp",
                user="ubuntu",
                opts="-o StrictHostKeychecking=no",
                key_path="~/.awskeys/testkey2.pem",
                homedir="/home/ubuntu",
            )
        ]

    @property
    def gpu_type(self) -> str: ...

    @property
    def gpu_qty(self) -> int: ...

    @property
    def sshaddr(self) -> AddrEntry:
        return self.addrs[0]

    def remove_pod(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            f"aws ec2 terminate-instances --instance-ids {self.InstanceId} --output json",
            shell=True,
            capture_output=True,
        )

    @classmethod
    def get_all(cls) -> list[Self]:
        insts = EC2Data.get_all_pods()
        keep, notkeep = [], []
        for p in insts:
            if p.tags and "EzPod" in p.tags and p.tags["EzPod"] == "true":
                keep.append(p)
            else:
                notkeep.append(p)
        if notkeep:
            print(
                "Warning: some EC2 instances were not valid ezpod instances and will be ignored:",
                notkeep,
            )
        return keep

    @property
    def status(self) -> str:
        return self.State.Name

    @property
    def source_file(self) -> str:
        return "~/.bashrc"

    @property
    def is_running(self) -> bool:
        return self.status.lower() == "running"

    @property
    def properties(self) -> PodDataProperties:
        return PodDataProperties(
            id=self.id,
            podname=self.podname,
            addrs=self.addrs,
            gpu_type=self.gpu_type,
            gpu_qty=self.gpu_qty,
            name=self.name,
            sshaddr=self.sshaddr,
            source_file=self.source_file,
            status=self.status,
        )


class EC2ReservationData(BaseModel):
    ReservationId: str
    OwnerId: str
    Instances: list[EC2InstanceData]


class EC2Data(BaseModel):
    Reservations: list[EC2ReservationData]

    @classmethod
    def from_json_str(cls, json_str: str) -> "EC2Data":
        return cls.model_validate_json(json_str)

    @classmethod
    def get(cls, region: str | None = None) -> Self:
        reg = f" --region {region}" if region else ""
        cmd = f"aws ec2 describe-instances --output json {reg}"
        output = subprocess.check_output(cmd, shell=True)
        return cls.model_validate_json(output)

    @classmethod
    def get_all_pods(cls, region: str | None = None) -> list[EC2InstanceData]:
        inst = cls.get(region)
        return [i for r in inst.Reservations for i in r.Instances]


def main():
    d = EC2InstanceData.get_all()
    print(d)


if __name__ == "__main__":
    main()
