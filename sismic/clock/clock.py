import abc

from time import time


__all__ = ['BaseClock', 'SimulatedClock', 'WallClock']


class BaseClock(metaclass=abc.ABCMeta):
    """
    Abstract implementation of a clock, as used by an interpreter.

    The purpose of a clock instance is to provide a way for the interpreter
    to get the current time during the execution of a statechart. 

    There are two important properties that must be satisfied by any
    implementation: (1) time is expected to be monotonic; and (2) returned time 
    is expected to remain constant between calls to split() and unsplit().
    """
    @abc.abstractproperty
    def time(self):
        """
        Current time
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def split(self):
        """
        Freeze current time until unsplit() is called.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def unsplit(self):
        """
        Unfreeze current time.
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
        self._split = None

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

    def split(self):
        """
        Freeze current time until unsplit is called.
        """
        self._split = self.time

    def unsplit(self):
        """
        Unfreeze current time.
        """
        self._split = None

    @property
    def time(self):
        """
        Time value of this clock.
        """
        if self._split is None:
            return self._time + self._elapsed
        else:
            return self._split
        
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
    def __init__(self):
        self._split = None

    def split(self):
        self._split = time()

    def unsplit(self):
        self._split = None

    @property
    def time(self):
        if self._split is None:
            return time()
        else:
            return self._split

    def __repr__(self):
        return 'WallClock[{}]'.format(self.time)