from pathlib import Path


from pydantic import BaseModel
import os


class RunFolder(BaseModel):
    local_path: str = "."

    @classmethod
    def cwd(cls):
        return cls(local_path=".")

    @property
    def remote_name(self):
        path = self.local_path if self.local_path != "." else os.getcwd()
        return os.path.basename(path)

    @property
    def local(self) -> Path:
        return Path(self.local_path)


class RunProject(BaseModel):
    folder: RunFolder
    pyname: str = "/bin/python3"
