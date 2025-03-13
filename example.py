import ezpod
from ezpod import PodCreationConfig
from ezpod.pods import Pods
from ezpod.runproject import RunFolder, RunProject


# folder to sync:
folder = RunFolder(
    local_path="/home/username/code/xyz",  # local path to the dir to sync
    # remote_name="xyz",  # the name of the folder on the remote (it will go to /root/xyz)
    # remote name feature was removed, may add back later if needed
)
folder = RunFolder(
    local_path="/home/g/code/ml/sae_components",  # local path to the dir to sync
    # remote_name="xyz",  # the name of the folder on the remote (it will go to /root/xyz)
)


# Create new pods:
new_pods_config = PodCreationConfig(
    # volume_id=...,
    # template_id=...,
    gpu_type="cpu3c-2-4",
    mem=2,
    vcpu=2,
    # other config options like gpu type etc
)


# Get a Pods object with all your current pods:
pods = Pods.All(project=RunProject(folder=folder), new_pods_config=new_pods_config)

pods.make_new_pods(5)  # creates 5 new pods
pods.sync()  # syncs the folder to all pods
# pods.setup()  # installs your folder or it's requirements.txt

# run a command on all pods
# (this will happen on the remote inside the folder you synced
# unless you specify"in_folder=False" )
pods.run("ls")  # to view, run 'tmux -a srun' in a terminal


input("Press enter to terminate all pods (will also delete tmux windows)...")
# terminate and destroy all pods
pods.purge()
