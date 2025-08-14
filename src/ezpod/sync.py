"""Utilities for syncing directories to remote pods using pyinfra."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Optional

from pyinfra.api import Config, Inventory, State


# A single thread pool used to perform rsync operations asynchronously.
_RSYNC_EXECUTOR = ThreadPoolExecutor()


@dataclass
class _JoinHandle:
    """Simple wrapper that exposes a ``join`` method for compatibility.

    The previous implementation returned a ``Promise`` from patchwork which
    exposed a ``join`` method.  To minimise changes in callers we provide the
    same API by wrapping a ``concurrent.futures.Future``.
    """

    future: Future

    def join(self) -> None:
        """Block until the underlying future is complete."""

        # ``Future.result`` will raise any exceptions from the worker thread
        # which matches the behaviour of the previous ``Promise.join``.
        self.future.result()


def _rsync(
    host: str,
    user: str,
    port: int,
    key_path: Optional[str],
    src: str,
    dest: str,
    exclude: List[str],
) -> None:
    """Perform the actual rsync using pyinfra's SSH connector."""

    data = {
        "ssh_user": user,
        "ssh_port": port,
        "ssh_strict_host_key_checking": "no",
    }
    if key_path:
        data["ssh_key"] = key_path

    inventory = Inventory(([host], data), {})
    state = State(inventory, Config())
    host_obj = inventory.get_host(host)

    # Replicate the patchwork defaults and follow symlinks like the previous
    # implementation (rsync_opts="-L").  Also forward any exclude patterns.
    flags = ["-pthrvz", "-L"] + [f"--exclude={pattern}" for pattern in exclude]
    host_obj.rsync(src, dest, flags=flags)

    # ``Host.rsync`` uses the ``ssh`` binary directly and does not maintain a
    # persistent connection, so there is nothing to clean up here.  The call is
    # kept to mirror the previous behaviour and future proof the code.
    host_obj.disconnect()


def asyncrsync(
    *,
    host: str,
    user: str,
    port: int,
    key_path: Optional[str],
    src: str,
    dest: str,
    exclude: Optional[List[str]] = None,
) -> _JoinHandle:
    """Start an asynchronous rsync to ``host`` using pyinfra.

    The returned object exposes a ``join`` method which blocks until the sync completes.
    """

    if exclude is None:
        exclude = []

    future = _RSYNC_EXECUTOR.submit(
        _rsync,
        host,
        user,
        port,
        key_path,
        src,
        dest,
        exclude,
    )
    return _JoinHandle(future)
