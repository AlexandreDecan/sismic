import time
import threading

from typing import List

from ..interpreter import Interpreter
from ..model import MacroStep


__all__ = ['AsyncRunner']


class AsyncRunner:
    """
    An asynchronous runner that repeatedly execute given interpreter.

    The runner tries to call its `execute` method every `interval` seconds, assuming
    that a call to that method takes less time than `interval`.
    If not, subsequent call is queued and will occur as soon as possible with
    no delay. The runner stops as soon as the underlying interpreter reaches
    a final configuration.

    The execution must be started with the `start` method, and can be (definitively)
    stopped with the `stop` method. An execution can be temporarily suspended
    using the `pause` and `unpause` methods. A call to `wait` blocks until
    the statechart reaches a final configuration.

    The current state of a runner can be obtained using its `running` and
    `paused` properties.

    While this runner can be used "as is", it is designed to be subclassed and
    as such, proposes several hooks to control the execution and additional
    behaviours:

     - before_run: called (only once !) when the runner is started. By default, do nothing.
     - after_run: called (only once !) when the interpreter reaches a final configuration.
       configuration of the underlying interpreter is reached. By default, do nothing.
     - execute: called at each step of the run. By default, call the `execute_once`
       method of the underlying interpreter and returns a *list* of macro steps.
     - before_execute: called right before the call to `execute()`. By default, do nothing.
     - after_execute: called right after the call to `execute()` with the returned value
       of `execute()`. By default, do nothing.

    By default, this runner calls the interpreter's `execute_once` method only once per cycle
    (meaning at least one macro step is processed during each cycle). If `execute_all` is
    set to True, then `execute_once` is repeatedly called until no macro step can be
    processed in the current cycle.

    :param interpreter: interpreter instance to run.
    :param interval: interval between two calls to `execute`
    :param execute_all: Repeatedly call interpreter's `execute_once` method at each step.
    """
    def __init__(self, interpreter: Interpreter, interval: float=0.1, execute_all=False) -> None:
        self._unpaused = threading.Event()
        self._stop = threading.Event()

        self.interpreter = interpreter
        self.interval = interval
        self._execute_all = execute_all
        self._thread = threading.Thread(target=self._run)

    @property
    def running(self):
        """
        Holds if execution is currently running (even if it's paused).
        """
        return self._thread.is_alive()

    @property
    def paused(self):
        """
        Holds if execution is running but paused.
        """
        return self.running and not self._unpaused.is_set()

    def start(self):
        """
        Start the execution.
        """
        if self._stop.is_set():
            raise RuntimeError('Cannot restart a stopped runner.')
        elif self._thread.isAlive():
            raise RuntimeError('Runner is already started')
        else:
            self._unpaused.set()
            self._thread.start()

    def stop(self):
        """
        Stop the execution.
        """
        self._stop.set()
        self._unpaused.set()
        self.wait()

    def pause(self):
        """
        Pause the execution.
        """
        self._unpaused.clear()

    def unpause(self):
        """
        Unpause the execution.
        """
        self._unpaused.set()

    def wait(self):
        """
        Wait for the execution to finish.
        """
        if self._thread.isAlive():
            self._thread.join()

    def execute(self) -> List[MacroStep]:
        """
        Called each time the interpreter has to be executed.
        """
        steps = []
        step = self.interpreter.execute_once()

        while step:
            steps.append(step)
            step = self.interpreter.execute_once()

            if not self._execute_all:
                break

        return steps

    def before_execute(self):
        """
        Called before each call to `execute()`.
        """
        pass

    def after_execute(self, steps: List[MacroStep]):
        """
        Called after each call to self.execute().
        Receives the return value of self.execute().

        :param steps: List of macrosteps returned by self.execute()
        """
        pass

    def before_run(self):
        """
        Called before running the execution.
        """
        pass

    def after_run(self):
        """
        Called after a final configuration is reached.
        """
        pass

    def _run(self):
        self.before_run()
        self._unpaused.wait()

        while not self.interpreter.final and not self._stop.is_set():
            starttime = time.time()
            self.before_execute()
            r = self.execute()
            self.after_execute(r)

            elapsed = time.time() - starttime
            time.sleep(max(0, self.interval - elapsed))
            self._unpaused.wait()

        # Ensure that self._stop is set if self.interpreter.final holds
        self._stop.set()

        self.after_run()

    def __del__(self):
        self.stop()

