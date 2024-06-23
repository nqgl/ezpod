# %%
import sys

sys.path.append("/home/g/code/ml/ezpod")
from ezpod.pod import Pods, RunProject, RunFolder

pods = Pods.All(
    project=RunProject(
        folder=RunFolder(
            local_path="/home/g/code/ml/sae_components", remote_name="sae_components"
        )
    )
)
pods.purge()
