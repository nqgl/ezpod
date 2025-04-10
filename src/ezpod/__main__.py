import click
import os
from ezpod.pods import Pods
from ezpod.runproject import RunFolder, RunProject
from ezpod.create_pods import PodCreationConfig
from ezpod.shell_local_data import Account

pods: Pods | None = None
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
            raise ValueError("Both EZPOD_GROUP and default_group are set")
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


@cli.command()
@click.argument("s")
def make(s):
    global pods
    assert pods is not None
    pods.make_new_pods(int(s))


@cli.command()
@click.argument("s")
def ex(s):
    # nonlocal pods
    assert pods is not None

    print("ex")

    pods.run_async(s)


@cli.command()
@click.argument("s")
def py(s):
    # nonlocal pods
    assert pods is not None

    pods.runpy(s)


@cli.command()
@click.argument("s")
def ssh(s):
    # nonlocal pods
    assert pods is not None

    print(pods.pods[int(s)].data.sshaddr.sshcmd)


@cli.command()
def sync():
    # nonlocal pods
    pods.sync()


@cli.command()
def setup():
    pods.sync()
    pods.setup()


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
    from .shell_local_data import set_current_account

    set_current_account(account)


@cli.command()
def print_create_config():

    print(PodCreationConfig.from_profile())


if __name__ == "__main__":
    cli()
