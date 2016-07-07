import tkinter as tk

# The two following lines are NOT needed in a typical environment.
# These lines make sismic available in our testing environment
import sys
sys.path.append('../../..')

from functools import partial

from sismic.io import import_from_yaml
from sismic.interpreter import Interpreter
from sismic.model import Event


####################################################

# Create a tiny GUI
class MicrowaveApplication(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        # Initialize widgets
        self.create_widgets()

        # Create a Stopwatch interpreter
        with open('microwave.yaml') as f:
            statechart = import_from_yaml(f)
        self.interpreter = Interpreter(statechart)

        # Bind interpreter events to the GUI
        self.interpreter.bind(self.event_handler)

        self.execute()

    def execute(self):
        self.interpreter.execute()

        # Update the widget that contains the list of active states.
        self.w_states['text'] = '\n'.join(self.interpreter.configuration)
        self.w_timer['text'] = 'M.timer: %d' % self.interpreter._evaluator.context_for('controller')['timer']
        self.w_power['text'] = 'M.power: %d' % self.interpreter.context['POWER_VALUES'][self.interpreter._evaluator.context_for('controller')['power']]

    def create_widgets(self):
        self.pack(fill=tk.BOTH)

        left_frame = tk.Frame(self)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH)

        # Input frame
        input_frame = tk.LabelFrame(left_frame, text='INPUT BUTTONS')
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(8, 8))

        # Sensor frame
        sensors_frame = tk.LabelFrame(left_frame, text='SENSORS')
        sensors_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(8, 8))

        # Add buttons
        self.w_input_power_inc = tk.Button(input_frame, text='power +', command=partial(self.send_event, event_name='input_power_inc'))
        self.w_input_power_dec = tk.Button(input_frame, text='power -', command=partial(self.send_event, event_name='input_power_dec'))
        self.w_input_power_reset = tk.Button(input_frame, text='power 0', command=partial(self.send_event, event_name='input_power_reset'))

        self.w_input_timer_inc = tk.Button(input_frame, text='timer +', command=partial(self.send_event, event_name='input_timer_inc'))
        self.w_input_timer_dec = tk.Button(input_frame, text='timer -', command=partial(self.send_event, event_name='input_timer_dec'))
        self.w_input_timer_reset = tk.Button(input_frame, text='timer 0', command=partial(self.send_event, event_name='input_timer_reset'))

        self.w_input_cooking_start = tk.Button(input_frame, text='start', command=partial(self.send_event, event_name='input_cooking_start'))
        self.w_input_cooking_stop = tk.Button(input_frame, text='stop', command=partial(self.send_event, event_name='input_cooking_stop'))

        self.w_tick = tk.Button(sensors_frame, text='tick', command=partial(self.send_event, event_name='timer_tick'))

        self.w_item_placed = tk.Button(sensors_frame, text='place item', command=partial(self.send_event, event_name='item_placed'))
        self.w_item_removed = tk.Button(sensors_frame, text='remove item', command=partial(self.send_event, event_name='item_removed'))

        self.w_door_opened = tk.Button(sensors_frame, text='open door', command=partial(self.send_event, event_name='door_opened'))
        self.w_door_closed = tk.Button(sensors_frame, text='close door', command=partial(self.send_event, event_name='door_closed'))

        # Pack
        self.w_input_power_inc.pack(side=tk.TOP, fill=tk.X)
        self.w_input_power_dec.pack(side=tk.TOP, fill=tk.X)
        self.w_input_power_reset.pack(side=tk.TOP, fill=tk.X)

        self.w_input_timer_inc.pack(side=tk.TOP, fill=tk.X, pady=(8, 0))
        self.w_input_timer_dec.pack(side=tk.TOP, fill=tk.X)
        self.w_input_timer_reset.pack(side=tk.TOP, fill=tk.X)

        self.w_input_cooking_start.pack(side=tk.TOP, fill=tk.X, pady=(8, 0))
        self.w_input_cooking_stop.pack(side=tk.TOP, fill=tk.X)

        self.w_tick.pack(side=tk.TOP, fill=tk.X)

        self.w_item_placed.pack(side=tk.TOP, fill=tk.X, pady=(8, 0))
        self.w_item_removed.pack(side=tk.TOP, fill=tk.X)

        self.w_door_opened.pack(side=tk.TOP, fill=tk.X, pady=(8, 0))
        self.w_door_closed.pack(side=tk.TOP, fill=tk.X)

        right_frame = tk.LabelFrame(self, text='COMPONENTS')
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(8, 8))


        # Display component
        component_frame = tk.LabelFrame(right_frame, text='Display')
        component_frame.pack(side=tk.TOP, fill=tk.BOTH)
        self.w_display = tk.Label(component_frame)
        self.w_display.pack(side=tk.TOP)

        # Lamp component
        lamp_frame = tk.LabelFrame(right_frame, text='Lamp')
        lamp_frame.pack(side=tk.TOP, fill=tk.BOTH)
        self.w_lamp = tk.Label(lamp_frame)
        self.w_lamp.pack(side=tk.TOP)

        # Heating component
        heating_frame = tk.LabelFrame(right_frame, text='Heating')
        heating_frame.pack(side=tk.TOP, fill=tk.BOTH)
        self.w_heating_power = tk.Label(heating_frame)
        self.w_heating_status = tk.Label(heating_frame)
        self.w_heating_power.pack(side=tk.TOP)
        self.w_heating_status.pack(side=tk.TOP)

        # Beeper component
        beep_frame = tk.LabelFrame(right_frame, text='Beeper')
        beep_frame.pack(side=tk.TOP, fill=tk.BOTH)
        self.w_beep = tk.Label(beep_frame)
        self.w_beep.pack(side=tk.TOP)

        # Turntable component
        turntable_frame = tk.LabelFrame(right_frame, text='Turntable')
        turntable_frame.pack(side=tk.TOP, fill=tk.BOTH)
        self.w_turntable = tk.Label(turntable_frame)
        self.w_turntable.pack(side=tk.TOP)

        # Statechart status
        statechart_frame = tk.LabelFrame(right_frame, text='Controller')
        statechart_frame.pack(side=tk.TOP, fill=tk.BOTH)

        self.w_states = tk.Label(statechart_frame)
        self.w_states.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))

        self.w_timer = tk.Label(statechart_frame)
        self.w_timer.pack(side=tk.BOTTOM, fill=tk.X)

        self.w_power = tk.Label(statechart_frame)
        self.w_power.pack(side=tk.BOTTOM, fill=tk.X)

    def event_handler(self, event):
        name = event.name

        if name == 'lamp_switch_on':
            self.w_lamp['text'] = 'on'
        elif name == 'lamp_switch_off':
            self.w_lamp['text'] = 'off'
        elif name == 'display_set':
            self.w_display['text'] = event.text
        elif name == 'display_clear':
            self.w_display['text'] = ''
        elif name == 'heating_set_power':
            self.w_heating_power['text'] = event.power
        elif name == 'heating_on':
            self.w_heating_status['text'] = 'on'
        elif name == 'heating_off':
            self.w_heating_status['text'] = 'off'
        elif name == 'beep':
            self.w_beep['text'] = event.number
        elif name == 'turntable_start':
            self.w_turntable['text'] = 'on'
        elif name == 'turntable_stop':
            self.w_turntable['text'] = 'off'
        else:
            raise ValueError('Unknown event %s' % event)

    def send_event(self, event_name):
        self.interpreter.queue(Event(event_name))
        self.execute()

    def _quit(self):
        self.master.destroy()


if __name__ == '__main__':
    # Create GUI
    root = tk.Tk()
    root.wm_title('Microwave')
    app = MicrowaveApplication(master=root)

    app.mainloop()
