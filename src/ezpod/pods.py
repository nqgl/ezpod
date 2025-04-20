import asyncio
from collections import deque
import os
import time
from datetime import datetime
from typing import Any, Coroutine, Optional

from ezpod.create_pods import PodCreationConfig
from ezpod.pod import Pod, PodOutput
from ezpod.pod_data import PodData, PURGED_POD_IDS
from ezpod.runproject import RunFolder, RunProject
from functools import cached_property
class Pods:
    def __init__(
        self,
        project: RunProject,
        pods: list[Pod],
        group: Optional[str],
        new_pods_config: Optional[PodCreationConfig] = None,
    ):
        self.project = project
        self.pending = []
        self.pods = pods
        self.by_id = {pod.data.id: pod for pod in pods}
        self.by_name = {pod.data.name: pod for pod in pods}
        self._new_pods_config = new_pods_config
        assert len(self.by_id) == len(self.pods)
        assert len(self.by_name) == len(self.pods)
        self.EZPOD_MIN_COMPLETE_TO_CONTINUE = None
        self._output_max_lines = 1000
        self.group = group

    @cached_property
    def new_pods_config(self) -> Optional[PodCreationConfig]:
        return self._new_pods_config or PodCreationConfig.from_profile()

    def run(self, cmd: str | list[str], in_folder=True, purge_after=False):
        self.run_async(cmd, in_folder, purge_after)
        return

        self.wait_pending()
        print(f"running {cmd} on all pods")
        joins = [pod.run(cmd, in_folder) for pod in self.pods]
        print("waiting for commands to finish...")
        for join in joins:
            join()
        print("joining done.")

    def run_async(
        self,
        cmd: str | list[str],
        outputs: dict[Pod, PodOutput] | None = None,
        in_folder=True,
        purge_after=False,
    ):
        self.wait_pending()
        loop = asyncio.get_event_loop()
        outputs = outputs if outputs is not None else self.make_outputs(cmd)
        if isinstance(cmd, str):
            tasks = [
                loop.create_task(pod.run_async(cmd, in_folder, purge_after))
                for pod in self.pods
            ]
        elif isinstance(cmd, list) and all(isinstance(c, str) for c in cmd):
            assert len(cmd) == len(self.pods)
            tasks = [
                loop.create_task(pod.run_async(c, in_folder, purge_after))
                for pod, c in zip(self.pods, cmd)
            ]
        else:
            raise ValueError(f"Invalid command type: {type(cmd)}")
        loop.run_until_complete(asyncio.gather(*tasks))

    def to_py_cmd(
        self, cmd: str | list[str], challenge_file: str | None = None, prefix_vars=None
    ):
        if isinstance(cmd, list):
            return [
                self.to_py_cmd(c, challenge_file, prefix_vars=prefix_vars) for c in cmd
            ]
        cmd = f"{self.project.pyname} {cmd}"
        if prefix_vars:
            cmd = f"{prefix_vars} {cmd}"
        if challenge_file:
            cmd = f"{self.project.pyname} {challenge_file}; {cmd}"
        return cmd

    def runpy(
        self,
        cmd: str | list[str],
        in_folder=True,
        purge_after=False,
        challenge_file=None,
    ):
        self.run(
            self.to_py_cmd(cmd, challenge_file=challenge_file),
            in_folder=in_folder,
            purge_after=purge_after,
        )

    def run_manual_challenge_file(
        self, challenge_file: str, stop_after_n_complete: int | None = None
    ):
        loop = asyncio.get_event_loop()
        cmd = self.to_py_cmd(challenge_file)
        loop.run_until_complete(
            self.run_async_with_monitor_and_timeout(
                cmd, num_done_threshold=stop_after_n_complete
            )
        )

    def prune(
        self, n: int, challenge_file: str, stop_after_n_complete: int | None = None
    ):
        self.run_manual_challenge_file(challenge_file, stop_after_n_complete)
        assert not any(p.output is None for p in self.pods)
        for p in self.pods:
            if p.output.end_time is None:
                p.remove()
        speeds = [
            (p.output.end_time - p.output.start_time, p)
            for p in self.pods
            if p.output is not None
            and p.output.end_time is not None
            and p.output.start_time is not None
        ]
        speeds.sort()
        sorted_pods = [p for _, p in speeds]
        keep, toss = sorted_pods[:n], sorted_pods[n:]
        for badpod in toss:
            badpod.remove()

        return speeds

    def run_async_with_monitor(
        self, cmd: str | list[str], monitor=None, in_folder=True, purge_after=False
    ):
        self.wait_pending()
        if monitor is None:
            from ezpod.test_read import monitor

            monitor = monitor(self)
        loop = asyncio.get_event_loop()
        tasks: list[asyncio.Task | Coroutine[Any, Any, None]] = []
        if isinstance(cmd, str):
            tasks = [
                loop.create_task(
                    pod.run_async(cmd, in_folder=in_folder, purge_after=purge_after)
                )
                for pod in self.pods
            ]
        elif isinstance(cmd, list) and all(isinstance(c, str) for c in cmd):
            assert len(cmd) == len(self.pods), f"{len(cmd)} != {len(self.pods)}"
            tasks = [
                loop.create_task(
                    pod.run_async(c, in_folder=in_folder, purge_after=purge_after)
                )
                for pod, c in zip(self.pods, cmd)
            ]
        else:
            raise ValueError(f"Invalid command type: {type(cmd)}")
        tasks.append(monitor)
        loop.run_until_complete(asyncio.gather(*tasks))

    async def run_async_with_monitor_and_timeout(
        self,
        cmd: str | list[str],
        monitor=None,
        in_folder=True,
        purge_after=False,
        timeout=1,
        num_done_threshold: int | None = None,
    ):
        self.wait_pending()
        if monitor is None:
            from ezpod.test_read import monitor

            monitor = monitor(self)

        loop = asyncio.get_event_loop()
        tasks: list[asyncio.Task] = []

        if isinstance(cmd, str):
            tasks = [
                loop.create_task(pod.run_async(cmd, in_folder, purge_after))
                for pod in self.pods
            ]
        elif isinstance(cmd, list) and all(isinstance(c, str) for c in cmd):
            assert len(cmd) == len(self.pods), f"{len(cmd)} != {len(self.pods)}"
            tasks = [
                loop.create_task(pod.run_async(c, in_folder, purge_after))
                for pod, c in zip(self.pods, cmd)
            ]
        else:
            raise ValueError(f"Invalid command type: {type(cmd)}")

        monitor_task = loop.create_task(monitor)
        all_tasks = tasks + [monitor_task]

        while True:
            # Wait for either the timeout or some tasks to complete
            done, pending = await asyncio.wait(
                all_tasks, timeout=timeout, return_when=asyncio.ALL_COMPLETED
            )

            # Check if we've reached our completion threshold (excluding the monitor)
            cmd_tasks_done = [t for t in done if t in tasks]
            if (
                num_done_threshold is not None
                and len(cmd_tasks_done) >= num_done_threshold
            ):
                print(
                    f"Reached completion threshold: {len(cmd_tasks_done)}/{len(tasks)} tasks done"
                )
                break

            # Check if all tasks are done
            if len(pending) == 0:
                print("All tasks completed")
                break

            # Optional: Check task status or do something with completed tasks
            print(f"{len(done)} tasks completed, {len(pending)} tasks pending")
        # Cancel any remaining tasks if needed
        for task in all_tasks:
            if not task.done():
                task.cancel()

        # Wait for cancellation to complete
        try:
            await asyncio.gather(*all_tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass

    def runpy_with_monitor(
        self,
        cmd,
        monitor=None,
        in_folder=True,
        purge_after=False,
        challenge_file=None,
        prefix_vars=None,
    ):
        return self.run_async_with_monitor(
            self.to_py_cmd(cmd, challenge_file=challenge_file, prefix_vars=prefix_vars),
            monitor=monitor,
            in_folder=in_folder,
            purge_after=purge_after,
        )

    def sync(self):  # todo do this async
        self.sync_async()
        return
        self.wait_pending()
        for pod in self.pods:
            pod.sync_folder()

    def sync_async(self, prev_failed=False):
        self.wait_pending()
        print("syncing...")
        promises = []
        connections = []
        for pod in self.pods:
            promise, connection = pod.sync_folder_async()
            promises.append(promise)
            connections.append(connection)
        print("all syncs started, waiting")
        try:
            for promise in promises:
                promise.join()
        except Exception as e:
            if prev_failed:
                raise e
            print(f"failed sync with exception: {e}, retrying in 5 seconds...")
            time.sleep(5)
            self.sync_async(prev_failed=True)
        print("all syncs completed, closing connections")
        for connection in connections:
            connection.close()
        print("done")

    def make_outputs(self, command: str):
        return {
            p: PodOutput(
                command=command,
                stdout=deque(maxlen=self._output_max_lines),
                stderr=deque(maxlen=self._output_max_lines),
                start_time=datetime.now(),
                is_running=True,
            )
            for p in self.pods
        }

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
        timeout = os.environ.get("EZPOD_SETUP_TIMEOUT", None)
        min_complete_to_continue = (
            self.EZPOD_MIN_COMPLETE_TO_CONTINUE
            or os.environ.get("EZPOD_MIN_COMPLETE_TO_CONTINUE", None)
        )
        if isinstance(min_complete_to_continue, str):
            min_complete_to_continue = int(min_complete_to_continue)
        wait_extra = 10
        outputs = self.make_outputs("<run setup>")
        tasks = [
            loop.create_task(pod.setup_async(outputs[pod]), name=str(i))
            for i, pod in enumerate(self.pods)
        ]
        print("beginning setups, waiting for them to complete...")
        dones = set()
        t = 0
        wips = None
        while min_complete_to_continue is None or (
            len(dones) < min_complete_to_continue or wait_extra > 0
        ):
            dones, wips = loop.run_until_complete(
                asyncio.wait(tasks, timeout=3),
            )
            t += 3
            if len(wips) == 0:
                break
            if min_complete_to_continue and len(dones) > min_complete_to_continue:
                wait_extra -= 3

            print(
                f"waiting for {len(wips)} pods to finish setup. {len(dones)} complete."
            )
        assert wips is not None
        to_cancel: set[Pod] = set()
        for wip in wips:
            i = int(wip.get_name())
            print(f"Pod {i} setup timed out.")
            to_cancel.add(self.pods[i])
            wip.cancel()
        for pod in to_cancel:
            self._remove_pod(pod)
            pod.remove()

    def add_pod(self, pod: Pod):
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

    def _remove_pod(self, pod: Pod):
        rm = [pod]
        if pod.data.id in self.by_id:
            rm.append(self.by_id[pod.data.id])
            del self.by_id[pod.data.id]
        if pod.data.name in self.by_name:
            rm.append(self.by_name[pod.data.name])
            del self.by_name[pod.data.name]
        for rmpod in rm:
            if pod in self.pods:
                self.pods.remove(rmpod)
        if pod.data.id in self.pending:
            self.pending.remove(pod.data.id)
            print(f"Pod {pod.data.name} removed. {len(self.pending)} still pending.")

    def wait_pending(self):
        if self.pending:
            print(f"Waiting for {len(self.pending)} pods to initialize...")
        while self.pending:
            for purged in PURGED_POD_IDS:
                if purged in self.pending:
                    self.pending.remove(purged)
            self.update()
            time.sleep(0.1)
        for purged in PURGED_POD_IDS:
            if purged in self.by_id:
                self._remove_pod(self.by_id[purged])

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
        group: Optional[str] = None,
    ) -> "Pods":
        if project is None:
            project = RunProject(folder=RunFolder.cwd())

        poddatas = PodData.get_all()
        if group is not None:
            poddatas = [pd for pd in poddatas if pd.podname.group == group]
        pods = [Pod(project=project, data=pd) for pd in poddatas]
        return cls(
            project=project, pods=pods, new_pods_config=new_pods_config, group=group
        )

    @classmethod
    def Nothing(
        cls,
        project: Optional[RunProject] = None,
        new_pods_config: Optional[PodCreationConfig] = None,
        group: Optional[str] = None,
    ) -> "Pods":
        if project is None:
            project = RunProject(folder=RunFolder.cwd())

        pods = []
        return cls(
            project=project, pods=pods, new_pods_config=new_pods_config, group=group
        )

    @classmethod
    def Range(
        cls,
        min: int,
        max: int,
        project: Optional[RunProject] = None,
        new_pods_config: Optional[PodCreationConfig] = None,
    ) -> "Pods":
        assert False  # TODO
        if project is None:
            project = RunProject(folder=RunFolder.cwd())
        poddatas = PodData.get_all()
        pods = [Pod(project=project, data=pd) for pd in poddatas]
        return cls(project=project, pods=pods, new_pods_config=new_pods_config)

    def make_new_pods(self, n):
        allpods = self.All(group=self.group)
        group = self.group or "pod"
        assert "_" not in group
        group = f"{group}_"
        current_largest_n = max(
            map(
                lambda x: int(x.replace(group, "")),
                allpods.by_name.keys(),
            ),
            default=-1,
        )
        for i in range(n):
            r = self.new_pods_config.create_pod(f"{group}{current_largest_n + i + 1}")
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

    def get_running_pods(self) -> list[Pod]:
        """Get list of pods that are currently running commands"""
        return [pod for pod in self.pods if pod.output and pod.output.is_running]

    def get_pod_status(self, name: str | None = None) -> str:
        """Get a formatted status string for a specific pod or all pods"""
        if name:
            pod = self.by_name.get(name)
            if not pod:
                return f"Pod {name} not found"
            output = pod.get_output()
            if not output:
                return f"Pod {name}: No command running"
            status = (
                "RUNNING"
                if output.is_running
                else f"FINISHED (code: {output.return_code})"
            )
            runtime = datetime.now() - output.start_time
            return f"Pod {name}: {status} (runtime: {runtime})"

        return "\n".join(self.get_pod_status(pod.data.name) for pod in self.pods)

    def tail_pod(self, name: str, lines: int = 10) -> str:
        """Get the last N lines of output from a specific pod"""
        pod = self.by_name.get(name)
        if not pod:
            return f"Pod {name} not found"

        output = pod.get_output()
        if not output:
            return f"No output available for pod {name}"

        result = []
        if output.stdout:
            result.append("=== STDOUT ===")
            result.extend(list(output.stdout)[-lines:])
        if output.stderr:
            result.append("=== STDERR ===")
            result.extend(list(output.stderr)[-lines:])

        return "\n".join(result)

    def __getitem__(self, key):
        if isinstance(key, int):
            pods_l = [self.pods[key]]
        elif isinstance(key, slice):
            pods_l = self.pods[key]
        elif isinstance(key, str):
            pods_l = [self.by_name[key]]
        else:
            raise TypeError("Invalid key type")
        return Pods(
            self.project, pods_l, group=self.group, new_pods_config=self.new_pods_config
        )
