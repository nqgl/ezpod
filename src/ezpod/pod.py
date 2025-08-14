import asyncio
import os
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Deque, Dict, Optional

import asyncssh
import asyncssh.connection

from ezpod.PodDataProtocol import InstanceData

from .pod_data import PodData, PURGED_POD_IDS

from .runproject import RunFolder, RunProject


@dataclass
class PodOutput:
    command: str
    stdout: Deque[str]
    stderr: Deque[str]
    is_running: bool
    start_time: datetime
    end_time: Optional[datetime] = None
    return_code: Optional[asyncssh.SSHCompletedProcess] = None


class Pod:
    def __init__(
        self,
        data: InstanceData,
        project: Optional[RunProject] = None,
    ):
        self.project = project or RunProject(folder=RunFolder.cwd())
        self.data: InstanceData = data
        # self.tmi = TMInstance(project=project, data=data)
        self.output: Optional[PodOutput] = None
        self._max_lines = 1000  # Could make this configurable in __init__ if needed

    @property
    def folder(self):
        return Path(self.project.folder.local_path)

    # def sync_folder(self, folder: Optional[RunFolder] = None):
    #     folder = folder or self.project.folder
    #     exclude = []
    #     if ".gitignore" in os.listdir(self.folder):
    #         exclude += [
    #             ist
    #             for i in open(folder.local / ".gitignore").read().split("\n")
    #             if not (ist := i.strip()).startswith("#") and ist
    #         ]
    #     if ".ezpodignore" in os.listdir(self.folder):
    #         exclude += [
    #             ist
    #             for i in open(folder.local / ".ezpodignore").read().split("\n")
    #             if not (ist := i.strip()).startswith("#") and ist
    #         ]
    #     print("exclude", exclude)
    #     if ".ezpodinclude" in os.listdir(self.folder):
    #         include = [
    #             ist
    #             for i in open(folder.local / ".ezpodinclude").read().split("\n")
    #             if not (ist := i.strip()).startswith("#") and ist
    #         ]
    #         print("include", include)
    #         try:
    #             for i in include:
    #                 exclude.remove(i)
    #         except ValueError as e:
    #             raise Exception(
    #                 ".ezpodinclude contains entries that are not ignored", e
    #             )
    #     print("exclude", exclude)
    #     exclude += [".git"]

    #     connection = Connection(self.data.sshaddr.addr, connect_kwargs={"timeout": 10})
    #     rsync(
    #         c=connection,
    #         source=self.project.folder.local_path,
    #         target=f"/root/",
    #         exclude=exclude,
    #         rsync_opts="-L",
    #         ssh_opts="-o StrictHostKeyChecking=no",
    #     )
    #     connection.close()

    def sync_folder_async(self, folder: Optional[RunFolder] = None):
        from ezpod.sync import asyncrsync

        folder = folder or self.project.folder
        exclude = []
        exclude += [".git"]
        if ".gitignore" in os.listdir(self.folder):
            exclude += [
                ist
                for i in open(folder.local / ".gitignore").read().split("\n")
                if not (ist := i.strip()).startswith("#") and ist
            ]
        if ".ezpodignore" in os.listdir(self.folder):
            exclude += [
                ist
                for i in open(folder.local / ".ezpodignore").read().split("\n")
                if not (ist := i.strip()).startswith("#") and ist
            ]
        print("exclude", exclude)
        if ".ezpodinclude" in os.listdir(self.folder):
            include = [
                ist
                for i in open(folder.local / ".ezpodinclude").read().split("\n")
                if not (ist := i.strip()).startswith("#") and ist
            ]
            print("include", include)
            try:
                for i in include:
                    exclude.remove(i)
            except ValueError as e:
                raise Exception(
                    ".ezpodinclude contains entries that are not ignored", e
                )
        print("exclude", exclude)
        exclude += [".git"]
        print("syncing to", self.data.sshaddr)
        promise = asyncrsync(
            host=self.data.sshaddr.ip,
            user=self.data.sshaddr.user,
            port=int(self.data.sshaddr.port),
            key_path=self.data.sshaddr.key_path or None,
            src=self.project.folder.local_path,
            dest=f"{self.data.sshaddr.homedir}/{self.project.folder.remote_name}",
            exclude=exclude,
        )
        return promise

    def command_extras(self, cmd, in_folder=True):
        print("source_file", self.data.source_file, type(self.data))
        cmd = f"source {self.data.source_file}; {self.activate_venv_cmd()}; {cmd}"

        if in_folder:
            cmd = f"cd {self.project.folder.remote_name}; {cmd}"
        return cmd

    def remote_command(self, cmd, in_folder=True) -> str:
        assert "'" not in cmd, "Support for single quotes not implemented yet."
        return self.as_bash_ssh_command(self.command_extras(cmd, in_folder))

    def as_bash_ssh_command(self, cmd):
        return f"{self.data.sshaddr.sshcmd} -t '{cmd}'"

    # def run(self, cmd, in_folder=True):
    #     return self.tmi.run(self.remote_command(cmd, in_folder))

    async def async_ssh_exec(self, cmd, output: PodOutput | None = None):
        # Initialize new output buffer for this command
        output = output or PodOutput(
            command=cmd,
            stdout=deque(maxlen=self._max_lines),
            stderr=deque(maxlen=self._max_lines),
            start_time=datetime.now(),
            is_running=True,
        )
        self.output = output

        opts = asyncssh.SSHClientConnectionOptions(
            username=self.data.sshaddr.user,
            **(
                dict(client_keys=[Path(self.data.sshaddr.key_path)])  # type: ignore
                if self.data.sshaddr.key_path
                else {}
            ),
        )
        async with asyncssh.connect(
            self.data.sshaddr.ip,
            self.data.sshaddr.port,
            options=opts,
        ) as conn:
            async with conn.create_process(cmd) as process:

                async def read_stdout():
                    assert self.output is not None
                    async for line in process.stdout:
                        self.output.stdout.append(line)
                        # print("2", line)

                async def read_stderr():
                    assert self.output is not None
                    async for line in process.stderr:
                        self.output.stderr.append(line)

                # print(1)
                # while process.returncode is None:
                #     line = await process.stdout.readline()
                #     print(line, end="")
                # print(2)
                await asyncio.gather(read_stdout(), read_stderr())
                # print(3)
                self.output.return_code = await process.wait()
                self.output.end_time = datetime.now()
                self.output.is_running = False
        return output

    def get_output(self) -> Optional[PodOutput]:
        """Get the current output buffer for this pod"""
        return self.output

    async def run_async(
        self, cmd, in_folder=True, purge_after=False, output: PodOutput | None = None
    ):
        try:
            output = await self.async_ssh_exec(
                self.command_extras(cmd, in_folder), output
            )
        except asyncssh.connection.HostKeyNotVerifiable as e:  # type: ignore
            print(e)
            print(f"Unable to verify pod. removing pod {self.data.name}")
            self.remove()
            return
        if purge_after:
            self.remove()
        return output

    def activate_venv_cmd(self):
        if self.project.use_venv:
            return f"cd ~; {self.project.pyname} -m venv --system-site-packages .venv; source .venv/bin/activate; cd -;"
        return "echo skipping venv activation"

    def setup_async(self, output: PodOutput):
        if "setup.py" in os.listdir(self.folder):
            return self.run_async(
                f"{self.project.pyname} -m pip install --ignore-installed blinker ;"  # TODO MAKE GENERAL DIRECTORY SPECIFIC SETUP RULES OPTION
                + f"{self.project.pyname} -m pip install -e .",
                output,
            )
        elif "requirements.txt" in os.listdir(self.folder):
            return self.run_async(
                f"{self.project.pyname} -m pip install -r requirements.txt",
                output,
            )
        raise Exception("No setup.py or requirements.txt found.")

    def remove(self):
        r = self.data.remove_pod()
        # r = remove_pod(self.data.id)
        if r.stderr:
            print(r.stderr)
            print("Error removing pod. Retrying")
            r = self.data.remove_pod()
            if r.stderr:
                raise Exception("Error removing pod.")
        if r.stdout:
            print(f"{self.data.name}: {r.stdout}")
        PURGED_POD_IDS.append(self.data.id)
        # if self.tmi.proj:
        #     self.tmi.pane.send_keys("exit")

    def update(self, data: InstanceData):
        if self.data != data:
            print(f"Pod {self.data.name} data changed.")
        if self.data.id != data.id:
            raise Exception("Wrong pod id.")
        if self.data.name != data.name:
            raise Exception("Pod name changed.")
        self.data = data

    def __repr__(self):
        return f"{self.data.name} ({self.data.id}, {self.data.gpu_type}, {self.data.status})"
