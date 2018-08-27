import pytest

from time import sleep 

from sismic.runner import AsyncRunner
from sismic.interpreter import Interpreter


class TestAsyncRunner:
    INTERVAL = 0.02

    @pytest.fixture()
    def interpreter(self, simple_statechart):
        return Interpreter(simple_statechart)

    @pytest.fixture()
    def runner(self, interpreter):
        r = AsyncRunner(interpreter, interval=0)
        yield r
        r.stop()

    @pytest.fixture()
    def mocked_runner(self, interpreter, mocker):
        class MockedRunner(AsyncRunner):
            before_run = mocker.MagicMock()
            before_execute = mocker.MagicMock()
            after_execute = mocker.MagicMock()
            after_run = mocker.MagicMock()
        
        r = MockedRunner(interpreter, interval=0)
        yield r
        r.stop()
        
    def test_not_yet_started(self, runner):
        assert runner.interpreter.configuration == []

        runner.interpreter.queue('goto s2')
        sleep(self.INTERVAL)
        assert runner.interpreter.configuration == []

        runner.start()
        sleep(self.INTERVAL)
        assert runner.interpreter.configuration == ['root', 's3']

    def test_start(self, runner):
        runner.start()
        sleep(self.INTERVAL)
        assert runner.interpreter.configuration == ['root', 's1']
        
        runner.interpreter.queue('goto s2')
        sleep(self.INTERVAL)
        assert runner.interpreter.configuration == ['root', 's3']

    def test_restart_stopped(self, runner):
        runner.start()
        runner.stop()

        with pytest.raises(RuntimeError, match='Cannot restart'):
            runner.start()
        
        assert not runner.running

    def test_start_again(self, runner):
        runner.start()

        with pytest.raises(RuntimeError, match='already started'):
            runner.start()
        
        assert runner.running
        runner.stop()
        assert not runner.running

    def test_hooks(self, mocked_runner):

        assert len(mocked_runner.before_run.call_args_list) == 0
        assert len(mocked_runner.before_execute.call_args_list) == 0
        assert len(mocked_runner.after_execute.call_args_list) == 0

        mocked_runner.start()
        sleep(self.INTERVAL)
        assert len(mocked_runner.before_run.call_args_list) == 1
        
        sleep(self.INTERVAL)
        
        assert len(mocked_runner.before_execute.call_args_list) > 0
        assert len(mocked_runner.after_execute.call_args_list) > 0

        assert len(mocked_runner.after_run.call_args_list) == 0
        mocked_runner.stop()
        sleep(self.INTERVAL)
        assert len(mocked_runner.after_run.call_args_list) == 1

            
    def test_final(self, runner):
        runner.start()
        runner.interpreter.queue('goto s2')
        runner.interpreter.queue('goto final')
        sleep(self.INTERVAL)
        sleep(self.INTERVAL)
        assert runner.interpreter.final
        assert not runner.running
        sleep(self.INTERVAL)  # Wait for the thread to finish
        assert not runner._thread.isAlive()

    def test_pause(self, runner):
        runner.start()
        assert not runner.paused

        sleep(self.INTERVAL)
        runner.pause()
        assert runner.paused
        assert runner.running
        assert runner.interpreter.configuration == ['root', 's1']
        
        runner.interpreter.queue('goto s2')
        sleep(self.INTERVAL)
        assert runner.interpreter.configuration == ['root', 's1']

        runner.unpause()
        assert not runner.paused
        assert runner.running
        sleep(self.INTERVAL)
        assert runner.interpreter.configuration == ['root', 's3']

        
    def test_state(self, runner):
        assert not runner.running
        assert not runner.paused
        runner.start()
        assert runner.running
        assert not runner.paused
        runner.pause()
        assert runner.running
        assert runner.paused
        runner.unpause()
        assert runner.running
        assert not runner.paused
        runner.stop()
        assert not runner.running
        assert not runner.paused

    def test_join_stopped(self, runner):
        runner.start()
        runner.stop()
        runner.wait()
