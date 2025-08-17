import time
from typing import Optional

from pydantic import BaseModel, computed_field

from ezpod.AddrEntry import AddrEntry
from ezpod.backend_aws_env_var import BACKEND_AWS
from ezpod.pod_group_info import PodGroupInfo

from ezpod.PodDataProtocol import BMPMeta, InstanceData

from ezpod.runpodctl_executor import runpod_info, runpod_run

PURGED_POD_IDS = []


class PodData(BaseModel):
    id: str
    podname: PodGroupInfo  # TODO Rename to group_info
    gpu_qty: int
    gpu_type: str
    imgname: str
    status: str
    podtype: str
    vcpu: int
    mem: int
    container: int
    volume: int
    cost: float
    addrs: list[AddrEntry]
    source_file: str = "/etc/rp_environment"
    # assigned_id: Optional[int] = None

    @computed_field
    @property
    def name(self) -> str:
        return str(self.podname)

    @classmethod
    def fromline(cls, line, skip_addrs=False):
        (
            podid,
            name,
            gpu,
            imgname,
            status,
            podtype,
            vcpu,
            mem,
            container,
            volume,
            cost,
            ipsandports,
            nothing,
        ) = line.split("\t")
        assert nothing == ""
        # if "pod" in name:
        #     assigned_id = int((spl := name.split("pod"))[1])
        #     assert len(spl) == 2
        # else:
        #     assigned_id = None
        pod = cls(
            id=podid.strip(),
            podname=PodGroupInfo.from_str(name.strip()),
            gpu_qty=gpu.split(" ")[0],
            gpu_type=" ".join(gpu.split(" ")[1:]),
            imgname=imgname,
            status=status,
            podtype=podtype,
            vcpu=vcpu,
            mem=mem,
            container=container,
            volume=volume,
            cost=cost,
            addrs=(
                []
                if skip_addrs
                else [
                    AddrEntry.from_line(addrstr.strip())
                    for addrstr in ipsandports.split("),")
                ]
            ),
            # assigned_id=assigned_id,
        )

        return pod

    @property
    def sshaddr(self) -> AddrEntry:
        addr = list(
            filter(
                lambda x: x.pub == "pub" and x.proto == "tcp" and x.dst_port == 22,
                self.addrs,
            )
        )
        assert len(addr) == 1
        return addr[0]

    @classmethod
    def get_all(cls) -> list["PodData"]:
        if BACKEND_AWS:
            from .ec2_data import EC2Data
            import os

            region = os.environ.get("EZPOD_AWS_REGION", None)
            return EC2Data.get_all_pods(region)
        for i in range(100):
            try:
                return cls._get_all()
            except Exception as e:
                print(f"Error in parsing pods info, on try {i + 1}/100", e)
                if i == 99:
                    raise e
                time.sleep(1)
                if i > 30:
                    print("purging failing pods")
                    cls._purge_failing()

    @classmethod
    def _get_all(cls) -> list["PodData"]:
        info = runpod_info()
        sp = info.split("\tPORTS")[1:]
        assert len(sp) == 1
        sp = sp[0]
        datas = [PodData.fromline(p) for p in sp.split("\n")[1:-1]]
        for pod in datas:
            try:
                _ = pod.sshaddr  # check if assigned
            except Exception as e:
                print(f"Pod {pod.name} not yet assigned address")
                raise e
        return datas

    @classmethod
    def _purge_failing(cls) -> list["PodData"]:
        if BACKEND_AWS:
            raise NotImplementedError("Purging failing pods not implemented for AWS")
        info = runpod_info()
        sp = info.split("\tPORTS")[1:]
        assert len(sp) == 1
        sp = sp[0]

        for p in sp.split("\n")[1:-1]:
            try:
                pod = cls.fromline(p)
                try:
                    _ = pod.sshaddr  # check if assigned
                except Exception as e:
                    print(f"Pod {pod.name} not yet assigned address")
                    raise e
            except:
                failpod = cls.fromline(p, skip_addrs=True)
                from ezpod import Pod

                # PURGED_POD_IDS.append(failpod.id)
                pod = Pod(data=failpod)
                pod.remove()

    def remove_pod(self):
        return runpod_run(f"remove pod {self.id}")

    @property
    def is_running(self) -> bool:
        return self.status.lower() == "running"


def main():
    import ezpod

    ezpod.login("markov")
    for pod in PodData.get_all():
        print(pod.name)


if __name__ == "__main__":
    main()
