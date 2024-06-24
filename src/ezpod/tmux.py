from ezpod.runproject import RunProject
from ezpod.pod_data import PodData


import subprocess


class TMInstance:
    def __init__(self, project: RunProject, data: PodData):
        self.proj = project
        self.data = data
        self.cmd_n = 0

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

    def run(self, cmd):
        assert False
        signal = f"{self.data.name}sig{self.cmd_n}"
        cmd = f"{cmd}; tmux wait-for -S {signal}"
        self.cmd_n += 1
        self.pane.send_keys(cmd)
        self.window
        join = lambda: subprocess.run(f"tmux wait-for {signal}", shell=True, check=True)
        return join
