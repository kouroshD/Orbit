# Copyright (c) 2022, NVIDIA CORPORATION & AFFILIATES, ETH Zurich, and University of Toronto
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Defines timer class for performance measurements."""


import time
from contextlib import ContextDecorator
from typing import Any, Optional


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""

    pass


class Timer(ContextDecorator):
    """A timer for performance measurements.

    A class to keep track of time for performance measurement.
    It allows timing via context managers and decorators as well.

    As a regular object:

    .. code-block:: python

        import time

        from omni.isaac.orbit.utils.timer import Timer

        timer = Timer()
        timer.start()
        time.sleep(1)
        print(1 <= timer.time_elapsed <= 2)  # Output: True

        time.sleep(1)
        timer.stop()
        print(2 <= stopwatch.total_run_time)  # Output: True

    As a context manager:

    .. code-block:: python

        import time

        from omni.isaac.orbit.utils.timer import Timer

        with Timer() as timer:
            time.sleep(1)
            print(1 <= timer.time_elapsed <= 2)  # Output: True

    Reference: https://gist.github.com/sumeet/1123871
    """

    def __init__(self, msg: Optional[str] = None):
        """
        Initializes the class variables
        """
        self._msg = msg
        self._start_time = None
        self._stop_time = None
        self._elapsed_time = None

    def __str__(self) -> str:
        """
        Returns:
            str -- String representation of the class object.
        """
        return f"{self.time_elapsed:0.6f} seconds"

    """
    Properties
    """

    @property
    def time_elapsed(self) -> float:
        """The number of seconds that have elapsed since this timer started timing.

        Note:
            This is used for checking how much time has elapsed while the timer is still running.
        """
        return time.perf_counter() - self._start_time

    @property
    def total_run_time(self) -> float:
        """The number of seconds that elapsed from when the timer started to when it ended."""
        return self._elapsed_time

    """
    Operations
    """

    def start(self):
        """Start timing."""
        if self._start_time is not None:
            raise TimerError("Timer is running. Use .stop() to stop it")

        self._start_time = time.perf_counter()

    def stop(self):
        """Stop timing"""
        if self._start_time is None:
            raise TimerError("Timer is not running. Use .start() to start it")

        self._stop_time = time.perf_counter()
        self._elapsed_time = self._stop_time - self._start_time
        self._start_time = None

    """
    Context managers
    """

    def __enter__(self) -> "Timer":
        """Start timing and return this `Timer` instance."""
        self.start()
        return self

    def __exit__(self, *exc_info: Any):
        """Stop timing."""
        self.stop()
        # print message
        if self._msg is not None:
            print(self._msg, f": {self._elapsed_time:0.6f} seconds")
