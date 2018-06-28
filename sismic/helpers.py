import threading
import time
import warnings

from collections import Counter
from functools import wraps
from typing import Any, Callable, List, Mapping, Optional

from .interpreter import Interpreter
from .model import MacroStep

__all__ = ['log_trace', 'run_in_background', 'AsyncRunner', 'coverage_from_trace']


def log_trace(interpreter: Interpreter) -> List[MacroStep]:
    """
    Return a list that will be populated by each value returned by the *execute_once* method
    of given interpreter.

    :param interpreter: an *Interpreter* instance
    :return: a list of *MacroStep*
    """
    func = interpreter.execute_once
    trace = []

    @wraps(func)
    def new_func():
        step = func()
        if step:
            trace.append(step)
        return step

    interpreter.execute_once = new_func  # type: ignore
    return trace


def coverage_from_trace(trace: List[MacroStep]) -> Mapping[str, Counter]:
    """
    Given a list of macro steps considered as the trace of a statechart execution, return *Counter* objects
    that counts the states that were entered, the states that were exited and the transitions that were processed.

    :param trace: A list of macro steps
    :return: A dict whose keys are "entered states", "exited states" and "processed transitions" and whose values are Counter object.
    """
    entered_states = []
    exited_states = []
    processed_transitions = []

    for macrostep in trace:
        for microstep in macrostep.steps:
            entered_states.extend(microstep.entered_states)
            exited_states.extend(microstep.exited_states)
            if microstep.transition:
                processed_transitions.append(microstep.transition)

    return {
        'entered states': Counter(entered_states),
        'exited states': Counter(exited_states),
        'processed transitions': Counter(processed_transitions)
    }


# TODO: Test
class AsyncRunner:
    """
    An asynchronous runner that repeatedly call the `execute` method of an 
    interpreter. 

    The execution can be controlled with the `start` and `stop` methods.
    
    The runner tries to call `execute` every `interval` amount
    of time, assuming that a call to `execute` takes less than `interval`
    amount of time. The runner stops as soon as the underlying interpreter 
    reaches a final configuration.

    Methods `before_execute` and `after_execute` are hooks that are called
    right before and right after the call to underlying interpreter's 
    `execute()` method. They are meant to be overridden as by default, they
    do nothing. 

    :param interpreter: interpreter instance to run.
    :param interval: interval between two calls to `execute`
    """
    def __init__(self, interpreter: Interpreter, interval: float=0.05) -> None:
        self._running = threading.Event()
        self.interpreter = interpreter
        self.interval = interval
        self._thread = None

    def start(self):
        """
        Start the execution.
        """
        self._running.set()
        self._run()

    def stop(self):
        """
        Stop the execution.
        """
        self._running.clear()
        if self._thread is not None:
            self._thread.cancel()

    def wait(self):
        """
        Wait for the execution.
        """
        # TODO: Not working, don't know why!
        if self._thread is not None:
            self._thread.join()

    def before_execute(self):
        """
        Called before each call to `execute()`. 
        """
        pass

    def after_execute(self, steps: Optional[MacroStep]):
        """
        Called after each call to `execute()` with the resulting steps.

        :return: Steps returned by `execute()`.
        """
        pass

    def _run(self):
        starttime = time.time()
        
        self.before_execute()
        steps = self.interpreter.execute()
        self.after_execute(steps)

        # TODO: Not thread-safe!!!
        if self.interpreter.final:
            self.stop()

        if self._running.is_set():
            elapsed = time.time() - starttime

            self._thread = threading.Timer(max(0, self.interval - elapsed), self._run)
            self._thread.start()


def run_in_background(interpreter: Interpreter,
                      delay: float=0.05,
                      callback: Callable[[List[MacroStep]], Any]=None) -> threading.Thread:
    """
    Run given interpreter in background. The time is updated according to
    *time.time() - starttime*. The interpreter is ran until it reaches a final configuration.
    You can manually stop the thread using the added *stop* of the returned Thread object.
    This is for convenience only and should be avoided, because a call to *stop* puts the interpreter in
    an empty (and thus final) configuration, without properly leaving the active states.

    :param interpreter: an interpreter
    :param delay: delay between each call to *execute()*
    :param callback: a function that accepts the result of *execute*.
    :return: started thread (instance of *threading.Thread*)
    :deprecated: since 1.3.0.
    """
    warnings.warn('Deprecated since 1.3.0. Use AsyncRunner instead.', DeprecationWarning)

    def _task():
        starttime = time.time()
        while not interpreter.final:
            interpreter.time = time.time() - starttime
            steps = interpreter.execute()
            if callback:
                callback(steps)
            time.sleep(delay)
    thread = threading.Thread(target=_task)

    def stop_thread():
        interpreter._configuration = set()

    thread.stop = stop_thread  # type: ignore

    thread.start()
    return thread

