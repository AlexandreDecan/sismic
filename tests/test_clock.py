import pytest

from time import sleep
from sismic.clock import SimulatedClock, WallClock


class TestSimulatedClock:
    @pytest.fixture()
    def clock(self):
        return SimulatedClock()

    def test_initial_value(self, clock):
        assert clock.time == 0

    def test_manual_increment(self, clock):
        clock.time += 1
        assert clock.time == 1

    def test_automatic_increment(self, clock):
        clock.start()
        sleep(0.1)
        assert clock.time >= 0.1

        clock.stop()
        value = clock.time
        sleep(0.1)
        assert clock.time == value

    def test_increment(self, clock):
        clock.start()
        sleep(0.1)
        assert clock.time >= 0.1
        clock.time = 10
        assert 10 <= clock.time < 10.1
        clock.stop()
        clock.time = 20
        assert clock.time == 20

    def test_speed_with_manual(self, clock):
        clock.speed = 2
        clock.time += 10
        assert clock.time == 10

    def test_speed_with_automatic(self, clock):
        clock.speed = 2
        clock.start()
        sleep(0.1)
        assert clock.time >= 0.2

        clock.stop()
        clock.time = 10
        clock.speed = 0.1
        
        clock.start()
        sleep(0.1)
        clock.stop()
        
        assert 10 < clock.time < 10.1

    def test_start_stop(self, clock):
        clock.start()
        sleep(0.1)
        clock.stop()
        sleep(0.1)
        clock.start()
        sleep(0.1)
        clock.stop()

        assert 0.2 <= clock.time < 0.3

    def test_split(self, clock):
        clock.split()
        clock.time = 10
        assert clock.time == 0
        clock.unsplit()
        assert clock.time == 10

    def test_split_with_automatic(self, clock):
        clock.start()
        sleep(0.1)
        assert clock.time >= 0.1
        
        clock.split()
        current_time = clock.time
        sleep(0.1)
        assert clock.time == current_time

        clock.unsplit()
        assert clock.time > current_time
    

class TestWallClock:
    @pytest.fixture()
    def clock(self):
        return WallClock()

    def test_increase(self, clock):
        current_time = clock.time
        sleep(0.1)
        assert clock.time > current_time

    def test_split(self, clock):
        clock.split()
        current_time = clock.time
        sleep(0.1)
        assert clock.time == current_time
        clock.unsplit()
        assert clock.time > current_time
        