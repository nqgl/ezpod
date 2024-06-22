# %%
from ezpod.pod import Pods, RunProject, RunFolder

pods = Pods.All(
    project=RunProject(
        folder=RunFolder(
            local_path="/home/g/code/ml/sae_components", remote_name="sae_components"
        )
    )
)
# pods = Pods.All()
# pods = Pods.All()
# pods = Pods.All()

# %%
# pods.run("ls")
# %%
# pods.update()
# pods.sync()
# pods.run("ls")

pods.make_new_pods(2)
pods.sync()

pods.run("ls")
pods.purge()
