import os
import subprocess
import time


def create_pod(name):

    cmd = f'runpodctl create pod \
    --gpuType \'NVIDIA GeForce RTX 4090\' \
    --mem 60 \
    --name {name} \
    --networkVolumeId ll7y06yojj \
    --templateId hczop1wb7d \
    --vcpu 16 \
    --volumePath /root/workspace \
    --imageName runpod/pytorch:2.2.0-py3.10-cuda12.1.1-devel-ubuntu22.04 \
    --secureCloud \
    --args \'bash -c " apt update; apt install -y git rsync; \
        DEBIAN_FRONTEND=noninteractive apt-get install openssh-server -y; \
    mkdir -p ~/.ssh; \
    cd $_; \
    chmod 700 ~/.ssh; \
    echo PUBLIC_KEY "$PUBLIC_KEY";\
    echo WANDB_API_KEY "$WANDB_API_KEY";\
    echo HUGGINGFACE_API_KEY "$HUGGINGFACE_API_KEY";\
    echo PUBLIC_KEY "$PUBLIC_KEY";\
    echo "$PUBLIC_KEY" >> authorized_keys; \
    chmod 700 authorized_keys; \
    service ssh start; \
    sleep infinity"\''
    r = subprocess.run(cmd, shell=True, capture_output=True)
    print(r.stdout.decode("utf-8"))
    if r.stderr:
        raise Exception(r.stderr.decode("utf-8"))
    return r


from pydantic import BaseModel


class PodCreationConfig(BaseModel):
    imgname: str = "nqgl/runpod_test"
    # imgname: str = "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04"
    volume_mount_path: str = "/root/workspace"
    volume_id: str = os.environ.get("EZPOD_VOLUME_ID", "58v97b820i")
    template_id: str = os.environ.get("EZPOD_TEMPLATE_ID", "hczop1wb7d")
    vcpu: int = os.environ.get("EZPOD_POD_VCPU", 16)
    mem: int = os.environ.get("EZPOD_POD_MEM", 60)
    gpu_type: str = os.environ.get("EZPOD_GPU_TYPE", "NVIDIA GeForce RTX 4090")
    volume_size: int = os.environ.get("EZPOD_VOLUME_SIZE", 100)

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
        /start.sh\"'"
        r = subprocess.run(cmd, shell=True, capture_output=True)
        print(r.stdout.decode("utf-8"))
        if r.stderr:
            raise Exception(r.stderr.decode("utf-8"))
        return r
