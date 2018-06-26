from time import time


class Clock:
    """
    A basic implementation of a clock to represent both simulated and real time. 

    The current time of the clock is exposed through the time attribute.

    By default, the clock follows simulated time. Methods start() and stop() can 
    be used to "synchronize" the clock based on real time. In that case, 
    clock speed can be adjusted with the speed attribute. A value strictly 
    greater than 1 increases clock speed while a value strictly lower than 1
    slows down the clock.

    The clock can also be manually adjusted by setting its time attribute. 
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
        Speed of the current clock. Only affects real time clock.
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
        return 'Clock[{:.2f},x{},{}]'.format(
            self.time,
            self._speed,
            '>' if self._play else '=',
        )

    