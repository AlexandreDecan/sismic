import tkinter as tk
import time

# The two following lines are NOT needed in a typical environment.
# These lines make sismic available in our testing environment
import sys
sys.path.append('..')

from sismic.io import import_from_yaml
from sismic.interpreter import Interpreter
from sismic.model import Event


# Create a tiny GUI
class StopwatchApplication(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        # Initialize widgets
        self.create_widgets()

        # Create a Stopwatch interpreter
        with open('stopwatch.yaml') as f:
            statechart = import_from_yaml(f)
        self.interpreter = Interpreter(statechart, initial_time=time.time())

        # Bind interpreter events to the GUI
        self.interpreter.bind(self.event_handler)

        # Run the interpreter
        self.starttime = time.time()
        self.run()

    def run(self):
        # This function does essentially the same job than ``sismic.interpreter.run_in_background``
        # but uses Tkinter's mainloop instead of a Thread, which is more adequate.

        # Update internal clock and execute interpreter
        self.interpreter.time = time.time()
        self.interpreter.execute()

        # Queue a call in 200ms on tk's mainloop
        self.after(200, self.run)

        # One could update widgets or objects here if needed.
        # For example, if "updated" event sending is removed from the statechart,
        # the text of self.w_timer has to be manually updated:
        #   self.w_timer['text'] = self.interpreter.context['display_time']
        # Here we update the widget that contains the list of active states.
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

        # Configuration label
        self.w_states = tk.Label(root)
        self.w_states.pack(side=tk.BOTTOM, fill=tk.X)

        # Timer label
        self.w_timer = tk.Label(root, font=("Helvetica", 16), pady=5)
        self.w_timer.pack(side=tk.BOTTOM, fill=tk.X)

    def event_handler(self, event):
        # Update text widget when timer value is updated
        if event.name == 'updated':
            self.w_timer['text'] = self.interpreter.context['display_time']

    def _start(self):
        self.interpreter.send(Event('start_button'))
        self.w_btn_start['state'] = tk.DISABLED
        self.w_btn_stop['state'] = tk.NORMAL

    def _stop(self):
        self.interpreter.send(Event('stop_button'))
        self.w_btn_start['state'] = tk.NORMAL
        self.w_btn_stop['state'] = tk.DISABLED

    def _reset(self):
        self.interpreter.send(Event('reset_button'))

    def _split(self):
        self.w_btn_split['state'] = tk.DISABLED
        self.w_btn_unsplit['state'] = tk.NORMAL
        self.interpreter.send(Event('split_button'))

    def _unsplit(self):
        self.w_btn_split['state'] = tk.NORMAL
        self.w_btn_unsplit['state'] = tk.DISABLED
        self.interpreter.send(Event('split_button'))

    def _quit(self):
        self.master.destroy()


if __name__ == '__main__':
    # Create GUI
    root = tk.Tk()
    root.wm_title('StopWatch')
    app = StopwatchApplication(master=root)

    app.mainloop()
