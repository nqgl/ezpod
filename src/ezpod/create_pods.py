import os
import subprocess

from pydantic import BaseModel
from .runpodctl_executor import runpod_login


class PodCreationConfig(BaseModel):
    imgname: str = os.environ.get("EZPOD_IMAGE_NAME", "nqgl/runpod_test")
    volume_mount_path: str = "/root/workspace"
    volume_id: str = os.environ.get("EZPOD_VOLUME_ID", "m7r7qattcz")
    template_id: str = os.environ.get("EZPOD_TEMPLATE_ID", "hczop1wb7d")
    vcpu: int = int(os.environ.get("EZPOD_POD_VCPU", 16))
    mem: int = int(os.environ.get("EZPOD_POD_MEM", 60))
    gpu_type: str = os.environ.get("EZPOD_GPU_TYPE", "NVIDIA GeForce RTX 4090")
    volume_size: int = int(os.environ.get("EZPOD_VOLUME_SIZE", 100))

    @runpod_login
    def create_pod(self, name):
        cmd = f"runpodctl create pod \
        --gpuType '{self.gpu_type}' \
        --mem {self.mem} \
        --name {name} \
        --networkVolumeId {self.volume_id} \
        --templateId {self.template_id} \
        --vcpu {self.vcpu} \
        --volumePath {self.volume_mount_path} \
        --imageName {self.imgname} \
        --secureCloud \
        --volumeSize {self.volume_size} \
        --args 'bash -c \" apt update; apt install -y git rsync; \
        DEBIAN_FRONTEND=noninteractive apt-get install openssh-server -y; \
        mkdir -p ~/.ssh; \
        cd $_; \
        chmod 700 ~/.ssh; \
        echo \"$PUBLIC_KEY\" >> authorized_keys; \
        chmod 700 authorized_keys; \
        service ssh start; \
        echo export WANDB_API_KEY=$WANDB_API_KEY >> /etc/rp_environment; \
        echo export HUGGINGFACE_API_KEY=$HUGGINGFACE_API_KEY >> /etc/rp_environment; \
        echo export NEPTUNE_API_TOKEN=$NEPTUNE_API_TOKEN >> /etc/rp_environment; \
        /start.sh\"'"
        r = subprocess.run(cmd, shell=True, capture_output=True)
        print(r.stdout.decode("utf-8"))
        if r.stderr:
            raise Exception(r.stderr.decode("utf-8"))
        return r
