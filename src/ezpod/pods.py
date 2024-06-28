from ezpod.runproject import RunFolder, RunProject
from ezpod.create_pods import PodCreationConfig
from ezpod.pod import Pod
from ezpod.pod_data import PodData
from typing import Optional
import asyncio
import time


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

    def run(self, cmd, in_folder=True, purge_after=False):
        self.run_async(cmd, in_folder, purge_after)
        return

        self.wait_pending()
        print(f"running {cmd} on all pods")
        joins = [pod.run(cmd, in_folder) for pod in self.pods]
        print("waiting for commands to finish...")
        for join in joins:
            join()
        print("joining done.")

    def run_async(self, cmd, in_folder=True, purge_after=False):
        self.wait_pending()
        loop = asyncio.get_event_loop()
        tasks = [
            loop.create_task(pod.run_async(cmd, in_folder, purge_after))
            for pod in self.pods
        ]
        loop.run_until_complete(asyncio.gather(*tasks))

    def runpy(self, cmd, in_folder=True, purge_after=False):
        self.run(f"{self.project.pyname} {cmd}", in_folder, purge_after)

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
        # # self.wait_pending()
        # print(f"setting up all pods")
        # joins = [pod.setup() for pod in self.pods]
        # print("waiting for setups to finish...")
        # for join in joins:
        #     join()
        # print("setups done.")
        loop = asyncio.get_event_loop()
        tasks = [loop.create_task(pod.setup_async()) for pod in self.pods]
        print("beginning setups, waiting for them to complete...")
        loop.run_until_complete(asyncio.gather(*tasks))
        print("setups complete")

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
