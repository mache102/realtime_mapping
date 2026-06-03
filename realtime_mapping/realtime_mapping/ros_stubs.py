"""Minimal rclpy stubs so the mapper runs without ROS installed.

When ``--dummy-data`` is passed, the mapper imports these stubs instead
of real ``rclpy``, removing the need to install ROS 2 on the machine.
The stubs are deliberately small — only the surface area used by
``realtime_mapper.py``.
"""

import time as _time
import logging as _logging
from typing import Any as _Any

_logging.basicConfig(level=_logging.INFO)


# ── rclpy module stub ──────────────────────────────────────────────────────

class _RclpyStub:
    """Drop-in stub for the ``rclpy`` top-level module."""

    @staticmethod
    def init(*_args: _Any, **_kwargs: _Any) -> None:
        pass

    @staticmethod
    def shutdown(*_args: _Any, **_kwargs: _Any) -> None:
        pass

    @staticmethod
    def spin(_node: _Any) -> None:
        """No-op: dummy data generator drives updates on its own thread."""
        pass


rclpy = _RclpyStub()


# ── Logger stub ────────────────────────────────────────────────────────────

class _LoggerStub:
    """Drop-in stub for ``rclpy.logging.Logger``."""

    def __init__(self, name: str = "realtime_mapper") -> None:
        self._logger = _logging.getLogger(name)

    def info(self, msg: str) -> None:
        self._logger.info(msg)

    def warn(self, msg: str) -> None:
        self._logger.warning(msg)

    def error(self, msg: str) -> None:
        self._logger.error(msg)

    def debug(self, msg: str) -> None:
        self._logger.debug(msg)


# ── Clock stub ─────────────────────────────────────────────────────────────

class _TimeMsg:
    """Drop-in stub for ``builtin_interfaces.msg.Time``."""

    def __init__(self) -> None:
        t = _time.time()
        self.sec = int(t)
        self.nanosec = int((t % 1) * 1e9)


class _ClockStub:
    """Drop-in stub for ``rclpy.clock.Clock``."""

    @staticmethod
    def now() -> "_ClockStub":
        return _ClockStub()

    @staticmethod
    def to_msg() -> _TimeMsg:
        return _TimeMsg()


# ── Node stub ──────────────────────────────────────────────────────────────

class Node:
    """Drop-in stub for ``rclpy.node.Node``.

    Provides just enough of the Node API for ``RealtimeMapper`` to
    instantiate and run without a real ROS 2 middleware.
    """

    def __init__(self, node_name: str = "stub_node") -> None:
        self._logger = _LoggerStub(node_name)
        self._clock = _ClockStub()

    def get_logger(self) -> _LoggerStub:
        return self._logger

    def get_clock(self) -> _ClockStub:
        return self._clock

    def create_subscription(
        self, _msg_type: _Any, _topic: str, _callback: _Any, _qos: int
    ) -> None:
        """No-op: subscriptions are never created in dummy-data mode."""
        return None
