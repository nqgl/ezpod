"""AWS EC2 instance metadata wrapper mirroring the runpod *PodData* API.

This module lets the rest of *ezpod* reuse the same logic (Pod / Pods, etc.)
for AWS‑backed clusters by exposing a *PodData*-compatible class built from
EC2 instance information.

Instances are identified via the tag ``EzPod=true`` – this tag is automatically
added when launching new instances through :pyclass:`~ezpod.create_pods.AWSPodCreationConfig`.
"""

from __future__ import annotations

import os

from pydantic import BaseModel
from typing_extensions import Self

from ezpod.AddrEntry import AddrEntry

from ezpod.aws_models.ec2.describe_instances import Tag

from ezpod.pod_group_info import PodGroupInfo

# ---------------------------------------------------------------------------
# Networking helpers
# ---------------------------------------------------------------------------
from ezpod.PodDataProtocol import InstanceData

# class AddrEntry(BaseModel):
#     ip: str
#     port: int = 22  # default SSH port
#     dst_port: int = 22  # destination on the instance
#     pub: str = "pub"
#     proto: str = "tcp"

#     @property
#     def sshcmd(self) -> str:
#         return f"ssh -o StrictHostKeyChecking=no -p {self.port} root@{self.ip} "

#     @property
#     def addr(self) -> str:
#         return f"{self.host}:{self.port}"

#     @property
#     def host(self) -> str:
#         return f"root@{self.ip}"


# ---------------------------------------------------------------------------
# Friendly naming – we keep the same *group_num* convention as runpodctl for
# consistency across back‑ends.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Main data container – tries to align with original PodData fields.
# ---------------------------------------------------------------------------


# class PodData(BaseModel):
#     id: str  # EC2 instance‑ID
#     podname: PodName
#     gpu_qty: int | None = None
#     gpu_type: str | None = None
#     imgname: str | None = None  # AMI ID
#     status: str  # pending / running / stopped / …
#     podtype: str  # instance type (g5.xlarge, …)
#     vcpu: int | None = None
#     mem: int | None = None  # in MiB (optional)
#     container: int | None = None  # unused placeholder, kept for API parity
#     volume: int | None = None  # root volume size in GiB
#     cost: float | None = None  # On‑demand hourly cost (optional)
#     addrs: List[AddrEntry]

#     # ------------------------------------------------------------------
#     # Derived / helper fields
#     # ------------------------------------------------------------------

#     @computed_field  # type: ignore[misc]
#     @property
#     def name(self) -> str:
#         return str(self.podname)

#     # ------------------------------------------------------------------
#     # Builders & queries
#     # ------------------------------------------------------------------

#     @classmethod
#     def from_instance(cls, instance) -> "PodData":  # EC2.Instance resource
#         # Name tag (optional)
#         name_tag = next(
#             (t["Value"] for t in instance.tags or [] if t["Key"] == "Name"),
#             instance.id,
#         )

#         # Attempt to retrieve vCPU & memory via *describe_instance_types* for
#         # more accurate reporting.  We cache the call per instance‑type to
#         # avoid extra API hits.
#         instance_type = instance.instance_type

#         _type_cache = cls._instance_type_cache  # type: ignore[attr-defined]
#         if instance_type not in _type_cache:
#             ec2_client = boto3.client(
#                 "ec2", region_name=instance.placement["AvailabilityZone"][:-1]
#             )
#             resp = ec2_client.describe_instance_types(InstanceTypes=[instance_type])
#             _type_cache[instance_type] = resp["InstanceTypes"][0]

#         itype_info = _type_cache[instance_type]

#         vcpu = itype_info["VCpuInfo"]["DefaultVCpus"]
#         mem = itype_info["MemoryInfo"]["SizeInMiB"]

#         gpu_qty = None
#         gpu_type = None
#         if "GpuInfo" in itype_info:
#             gpus = itype_info["GpuInfo"]["Gpus"]
#             if gpus:
#                 gpu_qty = gpus[0]["Count"]
#                 gpu_type = gpus[0]["Name"]

#         # Cost estimation – optional, we don't fail if Pricing API not
#         # accessible; leaving None in that case.
#         cost = None

#         # Network / SSH address
#         addrs: List[AddrEntry] = []
#         if instance.public_ip_address:
#             addrs.append(AddrEntry(ip=instance.public_ip_address))

#         return cls(
#             id=instance.id,
#             podname=name_tag,
#             gpu_qty=gpu_qty or 0,
#             gpu_type=gpu_type or instance_type,
#             imgname=instance.image_id,
#             status=instance.state["Name"],
#             podtype=instance_type,
#             vcpu=vcpu,
#             mem=mem,
#             container=None,
#             volume=(
#                 instance.block_device_mappings[0]["Ebs"]["VolumeSize"]
#                 if instance.block_device_mappings
#                 else None
#             ),
#             cost=cost,
#             addrs=addrs,
#         )

#     # Cache for describe_instance_types
#     _instance_type_cache: ClassVar[dict[str, dict]] = {}

#     # ------------------------------------------------------------------
#     # Collection helpers (replicating the runpod PodData API)
#     # ------------------------------------------------------------------

#     @classmethod
#     def get_all(cls) -> List["PodData"]:
#         region = os.environ.get("EZPOD_AWS_REGION", "us-west-2")
#         ec2 = boto3.resource("ec2", region_name=region)

#         # Only instances tagged as EzPod are returned; we also ignore
#         # terminated ones.
#         filters = [
#             # {"Name": "tag:EzPod", "Values": ["true"]},
#             {
#                 "Name": "instance-state-name",
#                 "Values": ["pending", "running", "stopping", "stopped"],
#             },
#         ]

#         instances = ec2.instances.filter(Filters=filters)

#         out: List[PodData] = []
#         for inst in instances:
#             # Some instances might still be initialising without a public IP;
#             # we retry a few times similar to the RunPod logic.
#             # try:
#             out.append(cls.from_instance(inst))
#         # except Exception as e:
#         #     print(f"Instance {inst.id} not ready yet: {e}")
#         #     continue

#         return out

#     # Note: The original runpod variant had methods for internal retry & purge
#     # of failing pods.  With EC2 we rely on AWS lifecycle hooks / states.  We
#     # therefore provide no‑ops to keep API parity.

#     @classmethod
#     def _purge_failing(cls) -> List["PodData"]:  # pragma: no cover – stub
#         return []


class EC2State(BaseModel):
    Name: str
    Code: int


class EC2InstanceData(BaseModel):
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
    source_file: str = "~/.bashrc"

    @property
    def tags(self):
        if self.Tags is None:
            return {}
        return {t.key: t.value for t in self.Tags}

    @classmethod
    def model_validate_jsonl(cls, json_str: str) -> "EC2InstanceData":
        print("json_str", json_str)
        return cls.model_validate_json(json_str)

    @property
    def podname(self) -> PodGroupInfo:
        return PodGroupInfo.from_str(self.name)

    @property
    def name(self) -> str:
        if self.tags and "Name" in self.tags:
            return self.tags["Name"]
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

    def remove_pod(self):
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
    def is_running(self) -> bool:
        return self.status.lower() == "running"


#         # TODO parse only the ezpod tagged ones DONE
#         # TODO parse name tag -> podname obj so we get grouping etc DONE


class EC2ReservationData(BaseModel):
    ReservationId: str
    OwnerId: str
    Instances: list[EC2InstanceData]


import subprocess


class EC2Data(BaseModel):

    Reservations: list[EC2ReservationData]

    @classmethod
    def from_json_str(cls, json_str: str) -> "EC2Data":
        print("json_str", json_str)
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
    from pathlib import Path

    d = EC2InstanceData.get_all()

    print(d)


if __name__ == "__main__":
    main()
