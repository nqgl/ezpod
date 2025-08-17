from pydantic import BaseModel


class AddrEntry(BaseModel):
    ip: str
    port: int
    dst_port: int
    pub: str
    proto: str
    user: str = "root"
    opts: str = "-o StrictHostKeychecking=no"
    homedir: str = "/root"
    key_path: str = ""

    @property
    def full_opts(self):
        keys = f"-i {self.key_path}" if self.key_path else ""
        return f"{self.opts} {keys}"

    @classmethod
    def from_line(cls, line: str):
        addrstuff, protostuff = line.split("\xa0(")
        pub, proto = protostuff.replace(")", "").split(",")
        ipport, dst_port = addrstuff.split("->")
        ip, port = ipport.split(":")
        return cls(
            ip=ip.strip(),
            port=port.strip(),
            dst_port=dst_port.strip(),
            pub=pub.strip(),
            proto=proto.strip(),
        )

    @property
    def sshcmd(self):
        return f"ssh {self.full_opts} -p {self.port} {self.user}@{self.ip} "

    @property
    def addr(self):
        return f"{self.host}:{self.port}"

    @property
    def host(self):
        return f"{self.user}@{self.ip}"
