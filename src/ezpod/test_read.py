import asyncio
from ezpod import Pods

import signal


def input_with_timeout(prompt, timeout=1):
    """
    Prompt the user for input, but raise a TimeoutError if no
    input is received within `timeout` seconds.
    """

    def handler(signum, frame):
        raise TimeoutError("Input timed out after {} seconds".format(timeout))

    # Set the signal handler and a timer
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)

    try:
        user_input = input(prompt)
    finally:
        # Disable the alarm after input is received or an exception occurred
        signal.alarm(0)

    return user_input


async def monitor(pods: "Pods"):
    running = pods.get_running_pods()
    selected_pod = running[0] if running else None
    selected_stream = "both"
    user_input = ""
    while not user_input == "quit":
        try:
            await asyncio.sleep(1)
            user_input = input_with_timeout("command: ")
        except TimeoutError:
            user_input = ""
        running = pods.get_running_pods()
        if user_input:
            if user_input[:3] == "sel":
                if user_input == "sel":
                    print(f"active pods: {[pod.data.name for pod in running]}")
                    select = input("select pod: ")
                else:
                    select = user_input.split(" ")[1]
                try:
                    selected_pod = pods.by_name[select]
                except KeyError:
                    print(f"Pod '{select}' not found")
                    matches = [pod for pod in pods.pods if select in pod.data.name]
                    if matches:
                        if len(matches) == 1:
                            print(f"Found match: {matches[0].data.name}")
                            selected_pod = matches[0]
                        else:
                            print("Multiple matches found:")
                            for pod in matches:
                                print(pod.data.name)
            elif user_input == "std":
                selected_stream = "stdout"
            elif user_input == "err":
                selected_stream = "stderr"
            elif user_input == "both":
                selected_stream = "both"
            if user_input == "cmd":
                print(selected_pod.get_output().command)
        else:
            ...
        if selected_pod:

            if selected_stream in ("stdout", "both"):
                print("vvv=======STDOUT=======vvv")
                for line in selected_pod.get_output().stdout:
                    print(line, end="")
                print("^^^^^^^^^^STDOUT^^^^^^^^^^")
            print()
            if selected_stream in ("stderr", "both"):
                print("vvv=======STDERR=======vvv")
                for line in selected_pod.get_output().stderr:
                    print(line, end="")
                print("^^^^^^^^^^STDERR^^^^^^^^^^")
            print()

            # print(selected_pod.output)
        print(f"active pods: {[pod.data.name for pod in running]}")
        print(f"selected pod: {selected_pod.data.name}")


async def challenge_monitor(pods: "Pods", stop_after_n_complete: int | None):
    running = pods.get_running_pods()
    selected_pod = running[0] if running else None
    selected_stream = "both"
    user_input = ""
    while not user_input == "quit":
        try:
            await asyncio.sleep(1)
            user_input = input_with_timeout("command: ")
        except TimeoutError:
            user_input = ""
        running = pods.get_running_pods()
        if user_input:
            if user_input[:3] == "sel":
                if user_input == "sel":
                    print(f"active pods: {[pod.data.name for pod in running]}")
                    select = input("select pod: ")
                else:
                    select = user_input.split(" ")[1]
                selected_pod = pods.by_name[select]
            elif user_input == "std":
                selected_stream = "stdout"
            elif user_input == "err":
                selected_stream = "stderr"
            elif user_input == "both":
                selected_stream = "both"
        else:
            ...
        if selected_pod:

            if selected_stream in ("stdout", "both"):
                print("vvv=======STDOUT=======vvv")
                for line in selected_pod.get_output().stdout:
                    print(line, end="")
                print("^^^^^^^^^^STDOUT^^^^^^^^^^")
            print()
            if selected_stream in ("stderr", "both"):
                print("vvv=======STDERR=======vvv")
                for line in selected_pod.get_output().stderr:
                    print(line, end="")
                print("^^^^^^^^^^STDERR^^^^^^^^^^")
            print()

            # print(selected_pod.output)
        print(f"active pods: {[pod.data.name for pod in running]}")
        print(f"selected pod: {selected_pod.data.name}")


if __name__ == "__main__":
    pods = Pods.All()

    N = 5
    long_command = " ".join([f"echo {i}; sleep 1;" for i in range(N)])

    pods.run_async_with_monitor(long_command, monitor(pods))
