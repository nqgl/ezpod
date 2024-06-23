import time
import subprocess


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
    echo "$PUBLIC_KEY" >> authorized_keys; \
    chmod 700 authorized_keys; \
    service ssh start; \
    sleep infinity"\''
    r = subprocess.run(cmd, shell=True, capture_output=True)
    print(r.stdout.decode("utf-8"))
    if r.stderr:
        raise Exception(r.stderr.decode("utf-8"))
    return r
