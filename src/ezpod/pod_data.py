from pydantic import BaseModel
import subprocess
from typing import Optional
import time


class AddrEntry(BaseModel):
    ip: str
    port: int
    dst_port: int
    pub: str
    proto: str

    def __init__(self, line: str):
        addrstuff, protostuff = line.split("\xa0(")
        pub, proto = protostuff.replace(")", "").split(",")
        ipport, dst_port = addrstuff.split("->")
        ip, port = ipport.split(":")
        super().__init__(
            ip=ip.strip(),
            port=port.strip(),
            dst_port=dst_port.strip(),
            pub=pub.strip(),
            proto=proto.strip(),
        )

    @property
    def sshcmd(self):
        return f"ssh -o StrictHostKeychecking=no -p {self.port} root@{self.ip} "

    @property
    def addr(self):
        return f"{self.host}:{self.port}"

    @property
    def host(self):
        return f"root@{self.ip}"


def runpod_info():
    r = subprocess.run("runpodctl get pod -a", shell=True, capture_output=True)
    return r.stdout.decode("utf-8")


class PodData(BaseModel):
    id: str
    name: str
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
    assigned_id: Optional[int] = None

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
        if "pod" in name:
            assigned_id = int((spl := name.split("pod"))[1])
            assert len(spl) == 2
        else:
            assigned_id = None
        pod = cls(
            id=podid.strip(),
            name=name.strip(),
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
                else [AddrEntry(addrstr.strip()) for addrstr in ipsandports.split("),")]
            ),
            assigned_id=assigned_id,
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

                pod = Pod(data=failpod)
                pod.remove()
