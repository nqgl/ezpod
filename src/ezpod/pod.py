import os
import subprocess
from pathlib import Path
from typing import Optional

import asyncssh
import asyncssh.connection
from fabric import Connection
from patchwork.transfers import rsync

from ezpod.runproject import RunFolder, RunProject
from ezpod.tmux import TMInstance
from .create_pods import create_pod

# from ezpod.tmux import TMInstance
from .pod_data import PodData, PURGED_POD_IDS


class Pod:
    def __init__(
        self,
        data: PodData,
        project: Optional[RunProject] = None,
    ):
        self.project = project or RunProject(folder=RunFolder.cwd())
        self.data: PodData = data
        self.tmi = TMInstance(project=project, data=data)

    @property
    def folder(self):
        return Path(self.project.folder.local_path)

    def sync_folder(self, folder: Optional[RunFolder] = None):
        folder = folder or self.project.folder
        exclude = []
        if ".gitignore" in os.listdir(self.folder):
            exclude = open(folder.local / ".gitignore").read().split("\n")
        exclude += [".git"]

        connection = Connection(self.data.sshaddr.addr, connect_kwargs={"timeout": 10})
        rsync(
            c=connection,
            source=self.project.folder.local_path,
            target=f"/root/",
            exclude=exclude,
            rsync_opts="-L",
            ssh_opts="-o StrictHostKeyChecking=no",
        )
        connection.close()

    def sync_folder_async(self, folder: Optional[RunFolder] = None):
        from ezpod.sync import asyncrsync

        folder = folder or self.project.folder
        exclude = []
        if ".gitignore" in os.listdir(self.folder):
            exclude = open(folder.local / ".gitignore").read().split("\n")
        exclude += [".git"]

        connection = Connection(self.data.sshaddr.addr, connect_kwargs={"timeout": 10})
        promise = asyncrsync(
            c=connection,
            source=self.project.folder.local_path,
            target=f"/root/" + self.project.folder.remote_name,
            exclude=exclude,
            rsync_opts="-L",
            ssh_opts="-o StrictHostKeyChecking=no",
        )
        return promise, connection

    def command_extras(self, cmd, in_folder=True):
        cmd = f"source /etc/rp_environment; {cmd}"
        if in_folder:
            cmd = f"cd {self.project.folder.remote_name}; {cmd}"
        return cmd

    def remote_command(self, cmd, in_folder=True) -> str:
        assert "'" not in cmd, "Support for single quotes not implemented yet."
        return self.as_bash_ssh_command(self.command_extras(cmd, in_folder))

    def as_bash_ssh_command(self, cmd):
        return f"{self.data.sshaddr.sshcmd} -t '{cmd}'"

    def run(self, cmd, in_folder=True):
        return self.tmi.run(self.remote_command(cmd, in_folder))

    async def async_ssh_exec(self, cmd):

        opts = asyncssh.SSHClientConnectionOptions(username="root")
        async with asyncssh.connect(
            self.data.sshaddr.ip,
            self.data.sshaddr.port,
            options=opts,
        ) as conn:

            result = await conn.run(cmd, check=False)
            print(self.data.name, result.stdout, end="")
            if result.stderr:
                print("Error:", self.data.name, result.stderr)

    async def run_async(self, cmd, in_folder=True, purge_after=False):
        try:
            await self.async_ssh_exec(self.command_extras(cmd, in_folder))
        except asyncssh.connection.HostKeyNotVerifiable as e:
            print(e)
            print(f"Unable to verify pod. removing pod {self.data.name}")
            self.remove()
            return
        if purge_after:
            self.remove()

    def setup(self):
        if "setup.py" in os.listdir(self.folder):
            return self.run(f"{self.project.pyname} -m pip install -e .")
        elif "requirements.txt" in os.listdir(self.folder):
            return self.run(f"{self.project.pyname} -m pip install -r requirements.txt")
        raise Exception("No setup.py or requirements.txt found.")

    def setup_async(self):
        if "setup.py" in os.listdir(self.folder):
            return self.run_async(f"{self.project.pyname} -m pip install -e .")
        elif "requirements.txt" in os.listdir(self.folder):
            return self.run_async(
                f"{self.project.pyname} -m pip install -r requirements.txt"
            )
        raise Exception("No setup.py or requirements.txt found.")

    def remove(self):
        r = subprocess.run(
            f"runpodctl remove pod {self.data.id}", shell=True, check=True
        )
        if r.stderr:
            print(r.stderr)
            print("Error removing pod. Retrying")
            r = subprocess.run(
                f"runpodctl remove pod {self.data.id}", shell=True, check=True
            )
            if r.stderr:
                raise Exception("Error removing pod.")
        if r.stdout:
            print(f"{self.data.name}: {r.stdout}")
        PURGED_POD_IDS.append(self.data.id)
        # if self.tmi.proj:
        #     self.tmi.pane.send_keys("exit")

    def update(self, data: PodData):
        if self.data != data:
            print(f"Pod {self.data.name} data changed.")
        if self.data.id != data.id:
            raise Exception("Wrong pod id.")
        if self.data.name != data.name:
            raise Exception("Pod name changed.")
        self.data = data
        self.tmi.data = data
