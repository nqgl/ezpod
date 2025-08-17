from collections import UserDict
import os
from warnings import warn

import click

from ezpod.create_pods import PodCreationConfig
from ezpod.pods import Pods
from ezpod.runproject import RunFolder, RunProject
from ezpod.shell_local_data import Account

pods: Pods = None
GROUP = None


@click.group()
@click.option("--group", default=None)
@click.option("--i", default="")
@click.option("--all", is_flag=True)
def cli(group: str | None, i: str, all: bool):
    global pods
    global GROUP
    if all:
        assert not group
        assert not i
        GROUP = None
        pods = Pods.All()
        return
    if not group:
        account = Account.load()
        env_var = os.environ.get("EZPOD_GROUP", None)
        if account.default_group is not None and env_var is not None:
            warn("Both EZPOD_GROUP and default_group are set")
            warn(f"Using EZPOD_GROUP: {env_var}")
        group = env_var or account.default_group
    GROUP = group
    if group:
        pods = Pods.All(group=group)
    else:
        pods = Pods.All()
    assert pods is not None
    if not i:
        return
    if "-" in i:
        s = slice(*[None if n == "" else int(n) for n in i.split("-")])
        pods = pods[s]  # TODO
    elif i.isnumeric():
        pods = pods[int(i)]
    else:
        pods = pods[i]


@cli.command()
def list():
    assert pods is not None
    if pods.pods:
        for pod in pods.pods:
            print(pod)
    else:
        print("No pods.")


@cli.command()
def purge():
    assert pods is not None
    pods.purge()


from ezpod.AWSPodCreationConfig import AWSPodCreationConfig


@cli.command()
@click.argument("s")
@click.option("--mem", default=None)
@click.option("--count", default=None)
@click.option("--cpu", default=None)
@click.option("--storage", default=None)
@click.option("--image", default=None)
@click.option("--instance-type", default=None)
@click.option("--region", default=None)
@click.option("--no-region", is_flag=True)
@click.option("--until-success", is_flag=True)
@click.option("--ami", default=None)
def make(
    s,
    mem: int | None,
    count: int | None,
    cpu: int | None,
    storage: int | None,
    image: str | None,
    instance_type: str | None,
    region: str | None,
    no_region: bool,
    until_success: bool,
    ami: str | None,
):
    global pods
    assert pods is not None
    if mem is not None:
        print("Setting mem to", mem)
        pods.new_pods_config.mem = mem
    if count is not None:
        print("Setting count to", count)
        pods.new_pods_config.gpu_count = count
    if cpu is not None:
        print("Setting cpu to", cpu)
        pods.new_pods_config.vcpu = cpu
    if storage is not None:
        print("Setting storage to", storage)
        pods.new_pods_config.disk_size = storage
    if image is not None:
        print("Setting image to", image)
        pods.new_pods_config.imgname = image
    if instance_type is not None:
        assert isinstance(pods.new_pods_config, AWSPodCreationConfig)
        print("Setting instance_type to", instance_type)
        pods.new_pods_config.instance_type = instance_type
    if region is not None:
        assert isinstance(pods.new_pods_config, AWSPodCreationConfig)
        if no_region:
            raise click.UsageError("Cannot specify both --region and --no-region")
        print("Setting region to", region)
        pods.new_pods_config.region = region
    if no_region:
        assert isinstance(pods.new_pods_config, AWSPodCreationConfig)
        pods.new_pods_config.region = None
    if ami is not None:
        assert isinstance(pods.new_pods_config, AWSPodCreationConfig)
        print("Setting ami to", ami)
        pods.new_pods_config.ami_id = ami
    if until_success:
        make_until_success(pods)
    pods.make_new_pods(int(s))


def make_until_success(pods: Pods):
    import time

    while True:
        pods.make_new_pods(1)
        time.sleep(1)
        if Pods.All().get_alive().pods:
            break
        else:
            print("No pods created yet, retrying...")


@cli.command()
@click.argument("s")
def ex(s):
    # nonlocal pods
    assert pods is not None

    print("ex")

    pods.get_alive().run_async(s)


@cli.command()
@click.argument("s")
def py(s):
    # nonlocal pods
    assert pods is not None

    pods.get_alive().runpy(s)


@cli.command()
@click.argument("s")
@click.option("--user", default=None)
def ssh(s: str, user: str | None = None):
    # nonlocal pods
    assert pods is not None
    if s.isnumeric():
        pod = pods.get_alive().pods[int(s)]
    else:
        pod = pods.get_alive().by_name[s]
    if user:
        pod.data.sshaddr.user = user
    print(pod.data.sshaddr.sshcmd)


@cli.command()
def sync():
    # nonlocal pods
    pods.get_alive().sync()


@cli.command()
def setup():
    pods.get_alive().sync()
    pods.get_alive().setup()


@cli.command()
@click.argument("name")
def create_profile(name):
    cfg = PodCreationConfig.interactive_make()
    cfg.save(name)


@cli.command()
@click.argument("name")
def setprofile(name):
    from .shell_local_data import set_current_profile

    set_current_profile(name)


@cli.command()
def profiles():
    print(PodCreationConfig.list_profiles())


@cli.command()
def create_account():
    from .shell_local_data import Account

    Account.interactive_create()


@cli.command()
@click.argument("account")
def login(account):
    from .shell_local_data import flexible_login

    flexible_login(account)


@cli.command()
def print_create_config():

    print(PodCreationConfig.from_profile())


if __name__ == "__main__":
    cli()
