import argparse

import click

from ezpod import PodCreationConfig

from ezpod.pods import Pods
from ezpod.runproject import RunFolder, RunProject


@click.command()
@click.argument(
    "mode", type=click.Choice(["purge", "make", "ex", "py", "sync", "setup"])
)
# @click.argument("n", default=None, type=click.INT, required=False)
@click.argument("s", default=None, type=click.STRING, required=False)
def cli(mode, s):
    if mode == "purge":
        Pods.All().purge()
    elif mode == "make":
        pods = Pods.All()
        pods.make_new_pods(int(s))
    elif mode == "ex":
        pods = Pods.All()
        pods.run_async(s)
    elif mode == "py":
        pods = Pods.All()
        pods.runpy(s)
    elif mode == "sync":
        pods = Pods.All()
        pods.sync()
    elif mode == "setup":
        pods = Pods.All()
        pods.setup()

    print(s)


if __name__ == "__main__":
    cli()
