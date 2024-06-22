import libtmux as tm

import subprocess

serv = tm.Server()


try:
    sesh = serv.sessions.get(lambda session: session.name == "srun")
except:
    sesh = serv.new_session(session_name="srun")


class TMInstance:
    def __init__(self, i, inst):
        self.i = i
        self.inst = inst

    @property
    def win_name(self):
        return f"remote_{self.i}"

    @property
    def pane(self):
        return self.window.active_pane

    @property
    def window(self):
        try:
            return sesh.windows.get(lambda window: window.name == self.win_name)
        except:
            return sesh.new_window(window_name=self.win_name)

    def setup(self):
        self.window.active_pane.send_keys(
            f"vastrr; sid {self.i}; cd ~/code/ml/sae_components; rpy test --setup; do_vrr_logins"
        )

    def run(self, fname):
        self.pane.send_keys(f"rpy {fname}")
        self.window
