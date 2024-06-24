from pathlib import Path


import libtmux as tm
from pydantic import BaseModel
import os


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
