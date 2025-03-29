import click
import os
from ezpod.pods import Pods
from ezpod.runproject import RunFolder, RunProject
from ezpod.create_pods import PodCreationConfig

pods: Pods = None  # Pods.Nothing()
GROUP = None


@click.group()
@click.option("--group", default="")
@click.option("--i", default="")
@click.option("--all", is_flag=True)
def cli(group, i, all):
    global pods
    global GROUP
    if all:
        assert not group
        assert not i
        GROUP = None
        pods = Pods.All()
        return
    if group == "":
        group = os.environ.get("EZPOD_GROUP", None)
    GROUP = group
    if group:
        pods = Pods.All(group=group)
    else:
        pods = Pods.All()
    assert pods is not None
    if i:
        if "-" in i:
            s = slice(*[None if n == "" else int(n) for n in i.split("-")])
            pods = pods[s]  # TODO


@cli.command()
def list():
    if pods.pods:
        for pod in pods.pods:
            print(pod)
    else:
        print("No pods.")


@cli.command()
def purge():
    Pods.All().purge()


@cli.command()
@click.argument("s")
def make(s):
    global pods
    pods.make_new_pods(int(s))


@cli.command()
@click.argument("s")
def ex(s):
    # nonlocal pods
    print("ex")

    pods.run_async(s)


@cli.command()
@click.argument("s")
def py(s):
    # nonlocal pods
    pods.runpy(s)


@cli.command()
@click.argument("s")
def ssh(s):
    # nonlocal pods
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
    name = input("Account name: ")
    api_key = input("API key: ")
    from .shell_local_data import Account, save_account

    account = Account(api_key=api_key)
    save_account(name, account)


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
