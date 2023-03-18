# https://github.com/nchazin/pycon2019/blob/master/code/loop_runner.py

import asyncio
import threading
from asyncio import AbstractEventLoop


class LoopRunner(threading.Thread):
    loop: AbstractEventLoop

    def __init__(self, loop, name="runner"):
        threading.Thread.__init__(self, name=name)
        self.loop = loop

    def run(self):
        asyncio.set_event_loop(self.loop)   
        try:
            self.loop.run_forever()
        finally:
            if self.loop.is_running():
                self.loop.close()

    def run_coroutine(self, coroutine):
        # yield run(coroutine)
        result = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        return result.result()

    def _stop(self):
        self.loop.stop()

    def run_in_thread(self, callback, *args):
        return self.loop.call_soon_threadsafe(callback, *args)

    def stop(self):
        return self.run_in_thread(self._stop)

    def stop_if_running(self):
        if self.loop.is_running():
            self.stop()
