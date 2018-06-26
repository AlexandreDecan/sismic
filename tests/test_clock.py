import pytest

from time import sleep
from sismic.interpreter import Clock


class TestClock:
    @pytest.fixture()
    def clock(self):
        return Clock()

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

    