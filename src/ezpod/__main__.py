import click
import os
from ezpod.pods import Pods
from ezpod.runproject import RunFolder, RunProject

pods: Pods = Pods.Nothing()
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
def print_create_config():
    from ezpod.create_pods import PodCreationConfig

    print(PodCreationConfig())


if __name__ == "__main__":
    cli()
