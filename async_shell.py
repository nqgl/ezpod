# %%
import asyncio
import time


async def co():
    print("hello")
    await asyncio.sleep(1)
    print("world")


# %%
async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    print(f"[{cmd!r} exited with {proc.returncode}]")
    if stdout:
        print(f"[stdout]\n{stdout.decode()}")
    if stderr:
        print(f"[stderr]\n{stderr.decode()}")


# loop = asyncio.get_event_loop()


def runall():
    tasks = set()
    cors = []
    for i in range(7):
        cor = run(f"echo {i}; sleep {i}; echo done {i}")
        cors.append(cor)
    return cors
    return asyncio.gather(*cors)


r = runall()

for i in range(3):
    print("ereeerkekkeke")
    time.sleep(1)
    print(f"dsbdbd{i}")
asyncio.wait(r)

from ezpod import Pod


class SubShell:
    def __init__(self, pod: Pod):
        self.pod = pod

    def run(self, cmd):
        cmd = self.pod.remote_command(cmd)

    async def exec(self, cmd):
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if stderr or proc.returncode:
            raise Exception(stderr.decode())


class Shells:
    def __init__(self, subshells):
        self.subshells = subshells


# print("made")
# time.sleep(2)
# for c in cors:
#     task = loop.create_task(c)
#     tasks.add(task)
#     task.add_done_callback(lambda t: tasks.remove(t))
# print("wait")
# time.sleep(2)
# print("sleepdone")
# asyncio.gather(list(tasks))
# print("done")
# loop.close()


# %%
