import subprocess
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
import time
from patchwork.transfers import rsync
from fabric import Connection
from .pod_data import PodData
from .create_pods import create_pod, PodCreationConfig
import os
import libtmux as tm


class RunFolder(BaseModel):
    local_path: str = "."
    # remote_n
    # ame: Optional[str] = None

    @classmethod
    def cwd(cls):
        return cls(remote_name=os.path.basename(os.getcwd()), local_path=".")

    @property
    def remote_name(self):
        path = self.local_path if self.local_path != "." else os.getcwd()
        return os.path.basename(path)

    @property
    def local(self):
        return Path(self.local_path)

    @property
    def remote(self): ...


serv = tm.Server()


class RunProject(BaseModel):
    folder: RunFolder
    pyname: str = "/bin/python3"
    seshname: str = "srun"

    @property
    def sesh(self):
        try:
            return serv.sessions.get(lambda session: session.name == "srun")
        except:
            return serv.new_session(session_name="srun")


class TMInstance:
    def __init__(self, project: RunProject, data: PodData):
        self.proj = project
        self.data = data

    @property
    def win_name(self):
        return self.data.name

    @property
    def pane(self):
        return self.window.active_pane

    @property
    def window(self):
        try:
            return self.proj.sesh.windows.get(
                lambda window: window.name == self.win_name
            )
        except:
            return self.proj.sesh.new_window(window_name=self.win_name)

    def setup(self):
        self.window.active_pane.send_keys(
            f"vastrr; sid {self.i}; cd ~/code/ml/sae_components; rpy test --setup; do_vrr_logins"
        )

    def run(self, cmd):
        self.pane.send_keys(cmd)
        self.window


class Pod:
    def __init__(self, project: RunProject, data: PodData):
        self.project = project
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
            target=f"/root/",
            exclude=exclude,
            rsync_opts="-L",
            ssh_opts="-o StrictHostKeyChecking=no",
        )
        return promise, connection

    def run(self, cmd, in_folder=True):
        if in_folder:
            cmd = f"cd {self.project.folder.remote_name}; {cmd}"
        assert "'" not in cmd, "Support for single quotes not implemented yet."
        s = self.data.sshaddr.sshcmd
        self.tmi.run(f"{s} -t '{cmd}'")

    def setup(self):
        if "setup.py" in os.listdir(self.folder):
            self.run(f"{self.project.pyname} -m pip install -e .")
        elif "requirements.txt" in os.listdir(self.folder):
            self.run(f"{self.project.pyname} -m pip install -r requirements.txt")

    def remove(self):
        r = subprocess.run(
            f"runpodctl remove pod {self.data.id}", shell=True, check=True
        )
        if r.stderr:
            print(r.stderr)
            raise Exception("Error removing pod.")
        if r.stdout:
            print(f"{self.data.name}: {r.stdout}")
        self.tmi.pane.send_keys("exit")

    def update(self, data: PodData):
        if self.data != data:
            print(f"Pod {self.data.name} data changed.")
        if self.data.id != data.id:
            raise Exception("Wrong pod id.")
        if self.data.name != data.name:
            raise Exception("Pod name changed.")
        self.data = data
        self.tmi.data = data


class Pods:
    def __init__(
        self,
        project: RunProject,
        pods: list[Pod],
        new_pods_config: Optional[PodCreationConfig] = None,
    ):
        self.project = project
        self.pending = []
        self.pods = pods
        self.by_id = {pod.data.id: pod for pod in pods}
        self.by_name = {pod.data.name: pod for pod in pods}
        self.new_pods_config = new_pods_config or PodCreationConfig()
        assert len(self.by_id) == len(self.pods)
        assert len(self.by_name) == len(self.pods)

    def run(self, cmd, in_folder=True):
        self.wait_pending()
        for pod in self.pods:
            pod.run(cmd, in_folder)

    def sync(self):  # todo do this async
        self.sync_async()
        return
        self.wait_pending()
        for pod in self.pods:
            pod.sync_folder()

    def sync_async(self):
        self.wait_pending()
        print("syncing...")
        promises = []
        connections = []
        for pod in self.pods:
            promise, connection = pod.sync_folder_async()
            promises.append(promise)
            connections.append(connection)
        print("all syncs started, waiting")
        for promise in promises:
            promise.join()
        print("all syncs completed, closing connections")
        for connection in connections:
            connection.close()
        print("done")

    def setup(self):
        self.sync()
        self.wait_pending()
        for pod in self.pods:
            pod.setup()

    def add_pod(self, pod):
        if pod.data.id in self.by_id:
            raise Exception(f"Pod with id {pod.data.id} already exists.")
        if pod.data.name in self.by_name:
            raise Exception(f"Pod with name {pod.data.name} already exists.")
        self.pods.append(pod)
        self.by_id[pod.data.id] = pod
        self.by_name[pod.data.name] = pod
        if pod.data.id in self.pending:
            self.pending.remove(pod.data.id)
            print(
                f"Pod {pod.data.name} initialized. {len(self.pending)} still pending."
            )

    def wait_pending(self):
        if self.pending:
            print(f"Waiting for {len(self.pending)} pods to initialize...")
        while self.pending:
            self.update()
            time.sleep(0.1)

    def update(self):
        datas = PodData.get_all()
        by_id = {data.id: data for data in datas}
        had = set(self.by_id.keys())
        got = set(by_id.keys())
        pend = set(self.pending)
        if got - had - pend:
            print("Warning: unrecognized pods appeared.")
        disappeared = had - got
        if disappeared:
            print("Warning: pods disappeared.")
            for id in disappeared:
                print(f"Warning: {self.by_id[id].data.name} with id {id} disappeared.")
                # self.by_id.pop(id)
        for id, pod in self.by_id.items():
            if id not in by_id:
                continue
            pod.update(by_id[id])
        finished_init = pend & got
        if finished_init:
            for id in finished_init:
                self.add_pod(self.pod_from_data(by_id[id]))

    def pod_from_data(self, data: PodData) -> Pod:
        return Pod(
            project=self.project,
            data=data,
        )

    @classmethod
    def All(
        cls,
        project: Optional[RunProject] = None,
        new_pods_config: Optional[PodCreationConfig] = None,
    ) -> "Pods":
        if project is None:
            project = RunProject(folder=RunFolder.cwd())

        poddatas = PodData.get_all()
        pods = [Pod(project=project, data=pd) for pd in poddatas]
        return cls(project=project, pods=pods, new_pods_config=new_pods_config)

    def make_new_pods(self, n):
        allpods = self.All()
        current_largest_n = max(
            map(
                lambda x: int(x.replace("pod", "")),
                allpods.by_name.keys(),
            ),
            default=-1,
        )
        for i in range(n):
            r = self.new_pods_config.create_pod(f"pod{current_largest_n + i + 1}")
            pod_id = str(r.stdout).split('pod "')[1].split('" created')[0]
            self.pending.append(pod_id)

    def purge(self):
        for pod in self.pods:
            pod.remove()
        self.pods = []
        self.by_id = {}
        self.by_name = {}
        self.wait_pending()
        for pod in self.pods:
            pod.remove()
        self.pods = []
        self.by_id = {}
        self.by_name = {}
        assert len(PodData.get_all()) == 0
