import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from typing_extensions import Self

from ezpod.AWSPodCreationConfig import AWSPodCreationConfig
from ezpod.backend_aws_env_var import BACKEND_AWS
from ezpod.BasePodCreationConfig import BasePodCreationConfig, boto3

from .runpodctl_executor import runpod_run
from .shell_local_data import (
    acct_profiles,
    current_account_name,
    current_profile_name,
    set_current_account,
    set_current_profile,
)


# ---------------------------------------------------------------------------
# Generic / shared logic between back‑ends
# ---------------------------------------------------------------------------


class RunPodCreationConfig(BasePodCreationConfig):
    imgname: str = os.environ.get("EZPOD_IMAGE_NAME", "nqgl/runpod_test")
    volume_mount_path: str = "/root/workspace"
    volume_id: str | None = os.environ.get("EZPOD_VOLUME_ID", "m8xpzudogd")
    template_id: str = os.environ.get("EZPOD_TEMPLATE_ID", "hczop1wb7d")
    vcpu: int = int(os.environ.get("EZPOD_POD_VCPU", 16))
    mem: int = int(os.environ.get("EZPOD_POD_MEM", 60))
    gpu_count: int = 1
    gpu_type: str = os.environ.get("EZPOD_GPU_TYPE", "NVIDIA GeForce RTX 4090")
    volume_size: int = int(os.environ.get("EZPOD_VOLUME_SIZE", 100))
    disk_size: int = int(os.environ.get("EZPOD_DISK_SIZE", 20))

    @classmethod
    def from_profile(cls, profile: str | None = None):
        if profile is None:
            profile = current_profile_name()
            # profile = os.environ.get("EZPOD_PROFILE", None)
        if profile is None:
            return cls()
        cfg_path = acct_profiles() / f"{profile}.json"
        return cls.model_validate_json(cfg_path.read_text())

    @classmethod
    def list_profiles(cls):
        return [p.name for p in acct_profiles().iterdir() if p.is_file()]

    def _create_impl(self, name):
        print("making", self)
        pubkey = os.environ.get("EZPOD_PUBLIC_KEY", None)
        extra_pubkey = ""
        if pubkey:
            extra_pubkey = f"echo {pubkey} >> authorized_keys;"

        if os.environ.get("EZPOD_INJECT_LOCAL_API_KEYS", False):
            env_vars = f"echo export WANDB_API_KEY={os.environ.get('WANDB_API_KEY', '$WANDB_API_KEY')} >> /etc/rp_environment;\
            echo export HUGGINGFACE_API_KEY={os.environ.get('HUGGINGFACE_API_KEY', '$HUGGINGFACE_API_KEY')} >> /etc/rp_environment;\
            echo export NEPTUNE_API_TOKEN={os.environ.get('NEPTUNE_API_TOKEN', '$NEPTUNE_API_TOKEN')} >> /etc/rp_environment;\n"
        else:
            env_vars = f"echo export WANDB_API_KEY=$WANDB_API_KEY >> /etc/rp_environment; \
            echo export HUGGINGFACE_API_KEY=$HUGGINGFACE_API_KEY >> /etc/rp_environment; \
            echo export NEPTUNE_API_TOKEN=$NEPTUNE_API_TOKEN >> /etc/rp_environment;\n"
        volume_id_arg = f"--networkVolumeId {self.volume_id}" if self.volume_id else ""
        cmd = f"create pod \
        --gpuType '{self.gpu_type}' \
        --mem {self.mem} \
        --name {name} \
        {volume_id_arg} \
        --templateId {self.template_id} \
        --gpuCount {self.gpu_count} \
        --vcpu {self.vcpu} \
        --volumePath {self.volume_mount_path} \
        --imageName {self.imgname} \
        --secureCloud \
        --volumeSize {self.volume_size} \
        --containerDiskSize {self.disk_size} \
        --args 'bash -c \" apt update; apt install -y git rsync; \
        DEBIAN_FRONTEND=noninteractive apt-get install openssh-server -y; \
        mkdir -p ~/.ssh; \
        cd $_; \
        chmod 700 ~/.ssh; \
        echo \"$PUBLIC_KEY\" >> authorized_keys; \
        {extra_pubkey} \
        chmod 700 authorized_keys; \
        service ssh start; \
        {env_vars}\
        /start.sh\"'"
        r = runpod_run(cmd)
        print(r.stdout.decode("utf-8"))
        if r.stderr:
            raise Exception(r.stderr.decode("utf-8"))
        return r

    @classmethod
    def interactive_make(cls):
        default = cls()
        imgname = input(f"Image name (default: {default.imgname}): ") or default.imgname
        volume_mount_path = (
            input(f"Volume mount path (default: {default.volume_mount_path}): ")
            or default.volume_mount_path
        )
        volume_id = (
            input(f"Volume ID (default: {default.volume_id}): ") or default.volume_id
        )
        template_id = (
            input(f"Template ID (default: {default.template_id}): ")
            or default.template_id
        )
        vcpu = input(f"VCPU (default: {default.vcpu}): ") or default.vcpu
        mem = input(f"Memory (default: {default.mem}): ") or default.mem
        gpu_type = (
            input(f"GPU Type (default: {default.gpu_type}): ") or default.gpu_type
        )
        volume_size = (
            input(f"Volume Size (default: {default.volume_size}): ")
            or default.volume_size
        )
        disk_size = (
            input(f"Disk Size (default: {default.disk_size}): ") or default.disk_size
        )
        # api_key = input(f"API Key (default: {default.api_key}): ") or default.api_key
        return cls(
            # api_key=api_key,
            imgname=imgname,
            volume_mount_path=volume_mount_path,
            volume_id=volume_id,
            template_id=template_id,
            vcpu=int(vcpu),
            mem=int(mem),
            gpu_type=gpu_type,
            volume_size=int(volume_size),
            disk_size=int(disk_size),
        )

    def save(self, name):
        path = acct_profiles() / f"{name}.json"
        if path.exists():
            raise ValueError(f"Profile {name} already exists")
        path.write_text(self.model_dump_json())


# ---------------------------------------------------------------------------
# AWS back‑end
# ---------------------------------------------------------------------------
"""

aws ec2 run-instances \
    --image-id ami-034c3feaa4af88624 \
    --instance-type t2.micro \
    --key-name testkey2 \
    --security-group-ids sg-07df4d19ad1b1bf8f \
    --subnet-id subnet-0da05d9e51f590a8f \
    --count 1 \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=testname}]'
"""


# Backwards compatibility export so existing imports keep working
#   from ezpod import PodCreationConfig  -> RunPod backend by default
# The user can instead do:
#   from ezpod.create_pods import AWSPodCreationConfig
if TYPE_CHECKING:

    class PodCreationConfig(RunPodCreationConfig):
        pass

else:
    PodCreationConfig = AWSPodCreationConfig if BACKEND_AWS else RunPodCreationConfig
