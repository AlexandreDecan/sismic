import tkinter as tk
from collections import OrderedDict
from tkinter import ttk
from tkinter import messagebox, filedialog

from . import helpers

from sismic.interpreter import Interpreter
from sismic.io import import_from_yaml
from sismic.model import Event, FinalState, OrthogonalState, HistoryStateMixin, DeepHistoryState
from sismic.exceptions import ContractError

H_SPACE = 4
V_SPACE = 4

# TODO: OpenDialog: preview YAML
# TODO: Eventlist with preconfigured events, and add/edit/remove buttons
# TODO: Sub windows?
# TODO: Refactor with no inner LabelFrame


class EventsFrame(ttk.Frame):
    def __init__(self, master, interpreter, **kwargs):
        super().__init__(master, **kwargs)
        self._events = []

        self._event_variable = tk.StringVar()
        self._reset_parameters = tk.BooleanVar(value=False)
        self._event_parameters_variable = tk.StringVar(value='{}')
        self._create_widgets()
        self.reset(interpreter)

    def _create_widgets(self):
        self._w_labelframe = ttk.LabelFrame(self, text='Events')
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

        ttk.Label(self._w_labelframe, text='suggested events').pack(side=tk.TOP)
        ttk.Frame(self._w_labelframe, height=V_SPACE).pack(side=tk.TOP)

        # Event list
        scrollable = helpers.ScrollableFrame(self._w_labelframe, tk.VERTICAL)
        self._w_eventlist = ttk.Treeview(scrollable, selectmode=tk.BROWSE, height=5, show='tree')
        self._w_eventlist.column('#0', width=100)
        scrollable.put_widget(self._w_eventlist).pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._w_event_parameter_btn = ttk.Button(self._w_labelframe, text='Set parameters', width=14, command=self._cmd_set_parameters)
        self._w_event_parameter_btn.pack(side=tk.TOP)

        ttk.Frame(self._w_labelframe, height=V_SPACE).pack(side=tk.TOP)

        # Send button
        self._w_btn_send = ttk.Button(self._w_labelframe, text='Queue event', width=14, command=self._cmd_btn_send)
        self._w_btn_send.pack(side=tk.TOP)

        # Reset parameters option
        ttk.Checkbutton(self._w_labelframe, text='reset after queueing', variable=self._reset_parameters).pack(side=tk.TOP)

        ttk.Frame(self._w_labelframe, height=V_SPACE).pack(side=tk.BOTTOM)

    def _cmd_set_parameters(self):
        top = tk.Toplevel()
        top.title('Enter parameters')

        frame = helpers.EditableDict(top, initial=self._event_parameters, padding=H_SPACE)
        frame.pack(fill=tk.BOTH, expand=1)

        def _validate():
            self._event_parameters = frame.get_dict()
            top.destroy()

        ttk.Button(top, text='Cancel', command=top.destroy).pack(side=tk.RIGHT)
        ttk.Button(top, text='Save', command=_validate).pack(side=tk.RIGHT)


    def _cmd_btn_send(self):
        item = self._w_eventlist.focus()
        if item == '':
            messagebox.showerror('No selected event', 'You must select an event first.')
            return
        event_name = self._w_eventlist.item(item, 'text')
        event_parameters = self._event_parameters

        self._interpreter.queue(Event(event_name, **event_parameters))

        # Reset selection and parameters
        if self._reset_parameters.get():
            self._event_parameters = {}
            self._w_eventlist.selection_remove(item)

        # Do something to inform that event is sent
        self._w_btn_send.config(state=tk.DISABLED)
        self.after(200, lambda: self._w_btn_send.config(state=tk.NORMAL))

    def reset(self, interpreter):
        self._events = []
        self._event_parameters = OrderedDict()
        self._interpreter = interpreter
        self._w_eventlist.delete(*self._w_eventlist.get_children())

        for event in self._interpreter.statechart.events_for():
            self._w_eventlist.insert('', tk.END, text=event)

    def update_content(self, steps=None):
        pass


class TimeFrame(ttk.Frame):
    def __init__(self, master, interpreter, **kwargs):
        super().__init__(master, **kwargs)

        self._automatic = tk.BooleanVar(value=True)
        self._time = tk.DoubleVar()

        self._create_widgets()
        self.reset(interpreter)

    @property
    def automatic(self):
        return self._automatic.get()

    @property
    def time(self):
        return self._time.get()

    def _create_widgets(self):
        self._w_labelframe = ttk.LabelFrame(self, text='Time')
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

        inner_frame = ttk.Frame(self._w_labelframe)
        inner_frame.pack(side=tk.TOP, anchor=tk.CENTER)

        time = tk.Entry(inner_frame, textvariable=self._time, width=5, justify=tk.RIGHT)
        checkbox = tk.Checkbutton(inner_frame, text='autoupdate', variable=self._automatic)

        time.pack(side=tk.LEFT, anchor=tk.CENTER)
        checkbox.pack(side=tk.LEFT, anchor=tk.CENTER)

    def reset(self, interpreter):
        self._time.set(interpreter.time)

    def update_content(self, steps):
        pass

    def elapse_time(self, delta):
        if self.automatic:
            self._time.set(round(self._time.get() + delta, 3))


class StatechartFrame(ttk.Frame):
    def __init__(self, master, interpreter, **kwargs):
        super().__init__(master, **kwargs)

        self._create_widgets()
        self.reset(interpreter)

    def _create_widgets(self):
        self._w_labelframe = ttk.LabelFrame(self, text='Statechart')
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

        # States
        scrollable = helpers.ScrollableFrame(self._w_labelframe)
        self._w_statelist = ttk.Treeview(scrollable, columns=('type',), selectmode=tk.BROWSE, show='tree')
        scrollable.put_widget(self._w_statelist).pack(fill=tk.BOTH, expand=True)

        self._w_statelist.column('#0', width=120, stretch=1)
        self._w_statelist.column('type', width=30, anchor=tk.CENTER, stretch=0)

        self._w_statelist.tag_configure('state_active', foreground='steel blue')
        self._w_statelist.tag_configure('state_entered', foreground='forest green')
        self._w_statelist.tag_configure('state_exited', foreground='red')
        self._w_statelist.tag_configure('state_entered_and_exited', foreground='dark orange')

        self._w_statelist.tag_configure('transition', foreground='gray')
        self._w_statelist.tag_configure('transition_active', foreground='dark orange')

    def _state_type(self, state_name):
        state = self._interpreter.statechart.state_for(state_name)
        if isinstance(state, OrthogonalState):
            return 'P'
        elif isinstance(state, HistoryStateMixin):
            return 'H*' if isinstance(state, DeepHistoryState) else 'H'
        elif isinstance(state, FinalState):
            return 'F'
        else:
            return ''

    def reset(self, interpreter):
        self._interpreter = interpreter
        self._w_statelist.delete(*self._w_statelist.get_children())
        self._state_items = {}
        self._transition_items = {}

        statechart = self._interpreter.statechart

        # top-level states:
        item = self._w_statelist.insert('', tk.END, statechart.root, text=statechart.root, open=True)
        self._w_statelist.set(item, 'type', self._state_type(statechart.root))
        self._state_items[statechart.root] = item
        # Descendants
        for descendant in statechart.descendants_for(statechart.root):
            parent = statechart.parent_for(descendant)
            item = self._w_statelist.insert(parent, tk.END, descendant, text=descendant, open=True)
            self._w_statelist.set(item, 'type', self._state_type(descendant))
            self._state_items[descendant] = item

        # Transitions
        for transition in statechart.transitions:
            source = transition.source
            target = transition.target if not transition.internal else '(internal)'
            event = transition.event if transition.event else ''
            guard = '[{}]'.format(transition.guard) if transition.guard else ''
            try:
                item = self._w_statelist.insert(source, 0, tags='transition',
                                                text='{}{} > {}'.format(event, guard, target))
                self._transition_items[transition] = item
            except tk.TclError:
                # Item already exists
                pass

    def update_content(self, steps):
        entered = []
        exited = []
        transitions = []

        for step in steps:
            entered += step.entered_states
            exited += step.exited_states
            transitions += step.transitions

        # Reset items
        for name, item in self._state_items.items():
            self._w_statelist.item(item, tags=tk.NONE)
            self._w_statelist.item(item, text=name)
        for name, item in self._transition_items.items():
            self._w_statelist.item(item, tags='transition')

        # Active states
        for state in self._interpreter.configuration:
            self._w_statelist.item(self._state_items[state], tags='state_active')

        # Entered states
        for state in entered:
            self._w_statelist.item(self._state_items[state], tags='state_entered')

        # Exited states
        for state in exited:
            self._w_statelist.item(self._state_items[state], tags='state_exited')

        # Both (may happen as we consider several MacroStep at once)
        for state in set(entered).intersection(exited):
            self._w_statelist.item(self._state_items[state], tags='state_entered_and_exited')

        # Transitions
        for transition in transitions:
            item = self._transition_items[transition]
            self._w_statelist.item(item, tags='transition_active')


class ContextFrame(ttk.Frame):
    def __init__(self, master, interpreter, **kwargs):
        super().__init__(master, **kwargs)

        self._create_widgets()
        self.reset(interpreter)

    def _create_widgets(self):
        self._w_labelframe = ttk.LabelFrame(self, text='Context')
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

        # Context
        scrollable = helpers.ScrollableFrame(self._w_labelframe)
        self._w_context = ttk.Treeview(scrollable, columns=('value',), selectmode=tk.BROWSE)
        scrollable.put_widget(self._w_context).pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._w_context.column('#0', width=100)
        self._w_context.heading('#0', text='variable')
        self._w_context.column('value', width=100)
        self._w_context.heading('value', text='value')

        ttk.Button(self._w_labelframe, text='edit context', command=self._edit_context).pack(side=tk.TOP, fill=tk.X)

    def _edit_context(self):
        window = tk.Toplevel()

        window.title('Edit execution context')
        editable = helpers.EditableDict(window, self._interpreter.context, padding=H_SPACE)
        editable.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        def save_context():
            self._interpreter._evaluator._context = editable.get_dict()
            self.update_content([])
            window.destroy()

        ttk.Button(window, text='Cancel', command=window.destroy).pack(side=tk.RIGHT)
        ttk.Button(window, text='Save', command=save_context).pack(side=tk.RIGHT)

    def reset(self, interpreter):
        self._interpreter = interpreter
        self._w_context.delete(*self._w_context.get_children())

    def update_content(self, steps):
        for variable, value in self._interpreter.context.items():
            try:
                self._w_context.set(variable, 'value', value)
            except tk.TclError:
                self._w_context.insert('', tk.END, iid=variable, text=variable, values=(value,))


class LogsFrame(ttk.Frame):
    def __init__(self, master, interpreter, **kwargs):
        super().__init__(master, **kwargs)

        self._autoscroll_variable = tk.BooleanVar(value=True)
        self._create_widgets()
        self.reset(interpreter)

    def _create_widgets(self):
        self._w_labelframe = ttk.LabelFrame(self, text='Logs')
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

        # Reset and autoscroll
        option_frame = ttk.Frame(self._w_labelframe)
        option_frame.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Frame(option_frame, height=V_SPACE).pack(side=tk.TOP)

        self._w_clear_btn = ttk.Button(option_frame, text='Clear', command=self._cmd_btn_clear)
        self._w_clear_btn.pack(side=tk.RIGHT, anchor=tk.E)

        self._w_autoscroll = ttk.Checkbutton(option_frame, variable=self._autoscroll_variable, text='automatic scrolling')
        self._w_autoscroll.pack(side=tk.LEFT, anchor=tk.W)

        # Log panel
        scrollable = helpers.ScrollableFrame(self._w_labelframe, tk.HORIZONTAL + tk.VERTICAL)
        self._w_content = tk.Text(scrollable, height=6, wrap=tk.NONE)
        scrollable.put_widget(self._w_content).pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def reset(self, interpreter):
        self._interpreter = interpreter
        self._cmd_btn_clear()

    def _cmd_btn_clear(self):
        self._w_content.delete('1.0', tk.END)

    def update_content(self, steps):
        for step in steps:
            self._w_content.insert(tk.END, str(step) + '\n')
        if self._autoscroll_variable.get():
            self._w_content.see(tk.END)


class ExecuteInterpreterFrame(ttk.Frame):
    def __init__(self, master, statechart, ignore_contract=False, initial_context=None):
        super().__init__(master)

        self._statechart = statechart
        self._ignore_contract =ignore_contract
        self._initial_context = initial_context

        self._interpreter = Interpreter(self._statechart,
                                        ignore_contract=self._ignore_contract,
                                        initial_context=self._initial_context)
        self._autorun = False
        self._v_autorun_delay = tk.IntVar(value=200)  # in ms
        self._v_multiple_checkbox = tk.BooleanVar(value=False)

        self._create_widgets()
        self.update_content([])

    def _create_widgets(self):
        # Vertical pane
        vertical_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        vertical_pane.pack(fill=tk.BOTH, expand=True)

        main_frame = ttk.Frame(vertical_pane)
        self._w_logs_frame = LogsFrame(vertical_pane, self._interpreter)
        vertical_pane.add(main_frame, weight=3)
        vertical_pane.add(self._w_logs_frame, weight=1)

        # Statechart & context
        horizontal_pane = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        horizontal_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._w_statechart_frame = StatechartFrame(horizontal_pane, self._interpreter)
        horizontal_pane.add(self._w_statechart_frame, weight=1)

        self._w_context_frame = ContextFrame(horizontal_pane, self._interpreter)
        horizontal_pane.add(self._w_context_frame, weight=1)

        # Events, time and execution
        left_column_frame = ttk.Frame(main_frame, relief=tk.RAISED, borderwidth=3, padding=H_SPACE)
        left_column_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._w_events_frame = EventsFrame(left_column_frame, self._interpreter)
        self._w_time_frame = TimeFrame(left_column_frame, self._interpreter)
        execution_frame = ttk.LabelFrame(left_column_frame, text='Execution')

        self._w_events_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._w_time_frame.pack(side=tk.TOP, fill=tk.X)
        execution_frame.pack(side=tk.TOP, fill=tk.X)

        interval_frame = ttk.Frame(execution_frame)
        interval_frame.pack(side=tk.TOP, anchor=tk.CENTER)
        interval_label = ttk.Label(interval_frame, text='step interval: ')
        interval_entry = ttk.Entry(interval_frame, width=5, justify=tk.RIGHT, textvariable=self._v_autorun_delay)
        interval_label_ms = ttk.Label(interval_frame, text='ms')
        interval_label.pack(side=tk.LEFT, anchor=tk.E)
        interval_entry.pack(side=tk.LEFT)
        interval_label_ms.pack(side=tk.LEFT, anchor=tk.W)

        ttk.Frame(execution_frame, height=V_SPACE).pack(side=tk.TOP)

        self._w_execute_btn = ttk.Button(execution_frame, text='Execute step', width=14, command=self.execute)
        self._w_run_btn = ttk.Button(execution_frame, text='Run statechart', width=14, command=self._cmd_run_btn)
        self._w_reset_btn = ttk.Button(execution_frame, text='Reset statechart', width=14, command=self.reset)
        self._w_multiple_checkbox = ttk.Checkbutton(execution_frame, text='force step by step', variable=self._v_multiple_checkbox)

        self._w_execute_btn.pack(side=tk.TOP)
        self._w_run_btn.pack(side=tk.TOP)
        self._w_reset_btn.pack(side=tk.TOP)
        self._w_multiple_checkbox.pack(side=tk.TOP)

    def execute(self):
        # Update time
        if self._w_time_frame.automatic:
            self._w_time_frame.elapse_time(self._v_autorun_delay.get() / 1000)

        self._interpreter.time = round(self._w_time_frame.time, 3)  # Interpreter's clock is in second
        try:
            if self._v_multiple_checkbox.get():
                step = self._interpreter.execute_once()
                steps = [step] if step else []
            else:
                steps = self._interpreter.execute()
            self.update_content(steps)
        except ContractError as e:
            if self._autorun:
                self._w_run_btn.invoke()
            messagebox.showwarning('Contrat not satisfied', '{}\n\n{}'.format(str(e.__class__.__name__), str(e)))
            self.update_content([])
        except Exception as e:
            if self._autorun:
                self._w_run_btn.invoke()
            messagebox.showerror('An error has occured', '{}\n\n{}'.format(str(e.__class__.__name__), str(e)))
            self.update_content([])

        # Autorun?
        if self._autorun:
            self.after(self._v_autorun_delay.get(), self.execute)

    def update_content(self, steps):
        self._w_events_frame.update_content(steps)
        self._w_time_frame.update_content(steps)
        self._w_statechart_frame.update_content(steps)
        self._w_context_frame.update_content(steps)
        self._w_logs_frame.update_content(steps)

    def _cmd_run_btn(self):
        if self._autorun:
            self._autorun = False
            self._w_run_btn.config(text='Run')
            self._w_execute_btn.config(state=tk.NORMAL)
        else:
            self._autorun = True
            self._w_run_btn.config(text='Stop')
            self._w_execute_btn.config(state=tk.DISABLED)
            self.execute()

    def reset(self):
        # confirm?
        if messagebox.askyesno('Confirmation', 'Reset current simulation?'):
            self._interpreter = Interpreter(self._statechart,
                                            ignore_contract=self._ignore_contract,
                                            initial_context=self._initial_context)
            if self._autorun:
                self._w_run_btn.invoke()
            self._w_events_frame.reset(self._interpreter)
            self._w_time_frame.reset(self._interpreter)
            self._w_statechart_frame.reset(self._interpreter)
            self._w_context_frame.reset(self._interpreter)
            self._w_logs_frame.reset(self._interpreter)

            self.update_content([])


class ChooseInterpreterFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.create_widgets()

    def create_widgets(self):
        # File chooser
        file_frame = ttk.LabelFrame(self, text='Statechart')
        file_frame.pack(side=tk.TOP, fill=tk.X, pady=V_SPACE)
        file_label = ttk.LabelFrame(file_frame, text='Select a .yaml statechart')
        file_label.pack(side=tk.TOP)
        file_chosen = ttk.Entry(file_frame)
        file_chosen.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Frame(file_frame, width=H_SPACE).pack(side=tk.LEFT)
        file_button = ttk.Button(file_frame, text='Choose', command=self._cmd_choose)
        file_button.pack(side=tk.LEFT)

        # Contracts
        contract_frame = ttk.LabelFrame(self, text='Contracts')
        contract_frame.pack(side=tk.TOP, fill=tk.X, pady=V_SPACE)
        contract_check = ttk.Checkbutton(contract_frame, text='check contracts during execution')
        contract_check.invoke()
        contract_check.pack()

        # Context
        context_frame = ttk.LabelFrame(self, text='Context')
        context_frame.pack(side=tk.TOP, fill=tk.BOTH, pady=V_SPACE)

        context_dictframe = helpers.EditableDict(context_frame, initial={}, padding=H_SPACE)
        context_dictframe.pack(fill=tk.BOTH, expand=1)

        # Button
        button = ttk.Button(self, text='Next', command=self._cmd_start)
        button.pack(side=tk.TOP, pady=V_SPACE)

        # Expose some of them
        self._w_file_chosen = file_chosen
        self._w_contract_check = contract_check
        self._w_contextdict_frame = context_dictframe

    def _cmd_choose(self):
        choice = filedialog.askopenfilename(filetypes=[('YAML files', '.yaml'), ('All files', '*')])

        if choice:
            self._w_file_chosen.delete(0, tk.END)
            self._w_file_chosen.insert(0, choice)

    def _cmd_start(self):
        # Check chosen file
        chosen_file = self._w_file_chosen.get()
        try:
            with open(chosen_file) as f:
                statechart = import_from_yaml(f)
        except Exception as e:
            messagebox.showerror('Error', 'Unable to use "{}" as a statechart.\n\n{}\n{}'.format(
                chosen_file, e.__class__.__name__, e
            ))
            return

        # Check contract
        ignore_contract = (tuple() == self._w_contract_check.state())

        # Check context
        context = self._w_contextdict_frame.get_dict()

        self.destroy()
        self.master.wm_minsize(800, 600)
        app = ExecuteInterpreterFrame(self.master,
                                      statechart=statechart,
                                      ignore_contract=ignore_contract,
                                      initial_context=context)
        app.pack(fill=tk.BOTH, expand=True, padx=H_SPACE, pady=V_SPACE)



def main():
    root = tk.Tk()
    root.wm_title('Sismic-ui')

    style = ttk.Style()
    style.configure('TLabelframe', padding=H_SPACE)

    app = ChooseInterpreterFrame(root)
    app.pack(fill=tk.BOTH, expand=True, padx=H_SPACE, pady=V_SPACE)

    root.mainloop()


if __name__ == '__main__':
    main()