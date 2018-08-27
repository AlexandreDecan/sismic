import time
import tkinter as tk

from sismic.interpreter import Interpreter
from sismic.io import import_from_yaml
from stopwatch import Stopwatch


# The two following lines are NOT needed in a typical environment.
# These lines make sismic available in our testing environment
import sys
sys.path.append('../../..')




# Create a tiny GUI
class StopwatchApplication(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        # Initialize widgets
        self.create_widgets()

        # Create a Stopwatch interpreter
        with open('stopwatch_external.yaml') as f:
            statechart = import_from_yaml(f)

        # Create a stopwatch object and pass it to the interpreter
        self.stopwatch = Stopwatch()
        self.interpreter = Interpreter(statechart, initial_context={'stopwatch': self.stopwatch})
        self.interpreter.clock.start()
        
        # Run the interpreter
        self.run()

        # Update the stopwatch every 100ms
        self.after(100, self.update_stopwatch)

    def update_stopwatch(self):
        self.stopwatch.update(delta=0.1)
        self.after(100, self.update_stopwatch)

        # Update timer label
        self.w_timer['text'] = self.stopwatch.display()

    def run(self):
        # Queue a call every 100ms on tk's mainloop
        self.interpreter.execute()
        self.after(100, self.run)
        self.w_states['text'] = 'active states: ' + ', '.join(self.interpreter.configuration)

    def create_widgets(self):
        self.pack()

        # Add buttons
        self.w_btn_start = tk.Button(self, text='start', command=self._start)
        self.w_btn_stop = tk.Button(self, text='stop', command=self._stop)
        self.w_btn_split = tk.Button(self, text='split', command=self._split)
        self.w_btn_unsplit = tk.Button(self, text='unsplit', command=self._unsplit)
        self.w_btn_reset = tk.Button(self, text='reset', command=self._reset)
        self.w_btn_quit = tk.Button(self, text='quit', command=self._quit)

        # Initial button states
        self.w_btn_stop['state'] = tk.DISABLED
        self.w_btn_unsplit['state'] = tk.DISABLED

        # Pack
        self.w_btn_start.pack(side=tk.LEFT,)
        self.w_btn_stop.pack(side=tk.LEFT,)
        self.w_btn_split.pack(side=tk.LEFT,)
        self.w_btn_unsplit.pack(side=tk.LEFT,)
        self.w_btn_reset.pack(side=tk.LEFT,)
        self.w_btn_quit.pack(side=tk.LEFT,)

        # Active states label
        self.w_states = tk.Label(root)
        self.w_states.pack(side=tk.BOTTOM, fill=tk.X)

        # Timer label
        self.w_timer = tk.Label(root, font=("Helvetica", 16), pady=5)
        self.w_timer.pack(side=tk.BOTTOM, fill=tk.X)

    def _start(self):
        self.interpreter.queue('start')
        self.w_btn_start['state'] = tk.DISABLED
        self.w_btn_stop['state'] = tk.NORMAL

    def _stop(self):
        self.interpreter.queue('stop')
        self.w_btn_start['state'] = tk.NORMAL
        self.w_btn_stop['state'] = tk.DISABLED

    def _reset(self):
        self.interpreter.queue('reset')

    def _split(self):
        self.interpreter.queue('split')
        self.w_btn_split['state'] = tk.DISABLED
        self.w_btn_unsplit['state'] = tk.NORMAL

    def _unsplit(self):
        self.interpreter.queue('split')
        self.w_btn_split['state'] = tk.NORMAL
        self.w_btn_unsplit['state'] = tk.DISABLED

    def _quit(self):
        self.master.destroy()


if __name__ == '__main__':
    # Create GUI
    root = tk.Tk()
    root.wm_title('StopWatch (external)')
    app = StopwatchApplication(master=root)

    app.mainloop()
