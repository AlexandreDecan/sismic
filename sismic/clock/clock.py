import abc

from time import time


__all__ = ['BaseClock', 'SimulatedClock', 'WallClock', 'SynchronizedClock']


class BaseClock(metaclass=abc.ABCMeta):
    """
    Abstract implementation of a clock, as used by an interpreter.

    The purpose of a clock instance is to provide a way for the interpreter
    to get the current time during the execution of a statechart. 
    """
    @abc.abstractproperty
    def time(self):
        """
        Current time
        """
        raise NotImplementedError()


class SimulatedClock(BaseClock):
    """
    A simulated clock, starting from 0, that can be manually or automatically
    incremented. 

    Manual incrementation can be done by setting a new value to the time attribute.
    Automatic incrementation occurs when start() is called, until stop() is called.
    In that case, clock speed can be adjusted with the speed attribute. 
    A value strictly greater than 1 increases clock speed while a value strictly 
    lower than 1 slows down the clock.
    """
    def __init__(self):
        self._base = time()
        self._time = 0
        self._play = False
        self._speed = 1

    @property
    def _elapsed(self):
        return (time() - self._base) * self._speed if self._play else 0
    
    def start(self):
        """
        Clock will be automatically updated both based on real time and 
        its speed attribute.
        """
        if not self._play:
            self._base = time()
            self._play = True

    def stop(self):
        """
        Clock won't be automatically updated. 
        """
        if self._play:
            self._time += self._elapsed
            self._play = False

    @property
    def speed(self):
        """
        Speed of the current clock. Only affects time if start() is called.
        """
        return self._speed

    @speed.setter
    def speed(self, speed):
        self._time += self._elapsed
        self._base = time()
        self._speed = speed

    @property
    def time(self):
        """
        Time value of this clock.
        """
        return self._time + self._elapsed
        
    @time.setter
    def time(self, new_time):
        """
        Set the time of this clock.

        :param new_time: new time
        """
        current_time = self.time
        if new_time < current_time:
            raise ValueError('Time must be monotonic, cannot change time from {} to {}'.format(current_time, new_time))
        
        self._time = new_time
        self._base = time()

    def __str__(self):
        return '{:.2f}'.format(float(self.time))

    def __repr__(self):
        return 'SimulatedClock[{:.2f},x{},{}]'.format(
            self.time,
            self._speed,
            '>' if self._play else '=',
        )

    
class WallClock(BaseClock):
    """
    A clock that follows wall-clock time. 
    """
    
    @property
    def time(self):
        return time()
    
    def __repr__(self):
        return 'WallClock[{}]'.format(self.time)


class SynchronizedClock(BaseClock):
    """
    A clock that is synchronized with a given interpreter.

    The synchronization is based on the interpreter's internal time value, not 
    on its clock. As a consequence, the time value of a SynchronizedClock only
    changes when the underlying interpreter is executed.

    :param interpreter: an interpreter instance
    """
    def __init__(self, interpreter):
        self._interpreter = interpreter

    @property
    def time(self):
        return self._interpreter.time

    def __repr__(self):
        return 'SynchronizedClock[{}]'.format(self._interpreter.time)