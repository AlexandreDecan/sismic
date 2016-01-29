import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from collections import OrderedDict


class EditableDict(ttk.Frame):
    """
    A frame that encompasses an editable dictionary widget.
    The dict can be retrieved using get_dict().

    :param master: parent frame
    :param initial: optional initial dict
    :param **kwargs: optional keyword arguments that are passed to ttk.Frame.__init__
    """
    def __init__(self, master, initial=None, **kwargs):
        super().__init__(master, **kwargs)
        self._initial = initial if initial else {}

        self._v_key = tk.StringVar(value='')
        self._v_value = tk.StringVar(value='')
        self._create_widgets()
        self.reset()

    def _create_widgets(self):
        treeview = ttk.Treeview(self, columns=('value',), selectmode=tk.BROWSE, height=5)
        treeview.heading('#0', text='key')
        treeview.heading('value', text='value')

        def _select_item(e):
            self._w_edit_btn.config(state=tk.NORMAL)
            self._w_remove_btn.config(state=tk.NORMAL)
            item = self._treeview.focus()
            self._v_key.set(self._treeview.item(item, 'text'))
            self._v_value.set(self._treeview.set(item, 'value'))

        treeview.bind('<<TreeviewSelect>>', _select_item, '+')
        treeview.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        add_frame = ttk.Frame(self)
        add_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
        ttk.Label(add_frame, text='key:').grid(row=0, column=0, sticky=tk.W)
        ttk.Label(add_frame, text='value:').grid(row=0, column=1, sticky=tk.W)
        ttk.Entry(add_frame, textvariable=self._v_key).grid(row=1, column=0, sticky=tk.E + tk.W)
        ttk.Entry(add_frame, textvariable=self._v_value).grid(row=1, column=1, sticky=tk.E + tk.W)
        self._w_add_btn = ttk.Button(add_frame, text='Add', command=self._add_item)
        self._w_add_btn.grid(row=1, column=2)
        self._w_edit_btn = ttk.Button(add_frame, text='Edit selected', state=tk.DISABLED, command=self._edit_item)
        self._w_edit_btn.grid(row=1, column=3)
        self._w_remove_btn = ttk.Button(add_frame, text='Remove selected', state=tk.DISABLED, command=self._remove_item)
        self._w_remove_btn.grid(row=1, column=4)
        add_frame.grid_columnconfigure(0, weight=1)
        add_frame.grid_columnconfigure(1, weight=1)

        self._treeview = treeview

    def _add_item(self):
        # Check key duplicate
        key = self._v_key.get()
        if key in self._dict:
            messagebox.showerror('Key already exists', 'Key "{}" already exists!'.format(key))
            return

        # Parse value
        value = self._v_value.get()
        try:
            value = eval(value)
        except Exception as e:
            messagebox.showerror('Value error', 'Unable to convert "{}" to a value.\n\n{}\n{}'.format(
                value, e.__class__.__name__, e
            ))
            return

        item = self._treeview.insert('', tk.END, text=key)
        self._treeview.set(item, 'value', self._v_value.get())

        self._dict[key] = value

        # Reset
        self._v_key.set('')
        self._v_value.set('')

        self._treeview.selection_set('')
        self._w_edit_btn.config(state=tk.DISABLED)
        self._w_remove_btn.config(state=tk.DISABLED)

    def _edit_item(self):
        # Check key duplicate
        key = self._v_key.get()

        # Parse value
        value = self._v_value.get()
        try:
            value = eval(value)
        except Exception as e:
            messagebox.showerror('Value error', 'Unable to convert "{}" to a value.\n\n{}\n{}'.format(
                value, e.__class__.__name__, e
            ))
            return

        # Existing items
        item = self._treeview.focus()
        old_key = self._treeview.item(item, 'text')

        if old_key != key:
            # Remove old item
            self._dict.pop(old_key)
            self._treeview.delete(item)

            # Add new item
            item = self._treeview.insert('', tk.END, text=key)

        # Set and save value
        self._treeview.set(item, 'value', value)
        self._dict[key] = value

        self._treeview.selection_set(item)

    def _remove_item(self):
        item = self._treeview.focus()
        key = self._treeview.item(item, 'text')

        # Remove item
        self._dict.pop(key)
        self._treeview.delete(item)

        # Reset buttons
        self._w_edit_btn.config(state=tk.DISABLED)
        self._w_remove_btn.config(state=tk.DISABLED)

    def get_dict(self):
        return self._dict

    def reset(self):
        self._v_key.set('')
        self._v_value.set('')
        self._dict = OrderedDict()
        self._treeview.delete(*self._treeview.get_children())

        for k, v in self._initial.items():
            self._dict[k] = v
            item = self._treeview.insert('', tk.END, text=k)
            self._treeview.set(item, 'value', v)


class ScrollableFrame(ttk.Frame):
    """
    A scrollable frame that expects a widget to be put into.
    Typical use:

    1. Create a scrollable = ScrollableFrame(parent)
    2. Create your widget using scrollable as parent, ie. Treeview(scrollable, ...)
    3. Register your widget using scrollable.put(widget)
    4. Declare the geometry to be used, eg. scrollable.pack()

    For convenience, put(widget) returns self, so steps 3 and 4 can be combined as:
    > scrollable.put(widget).pack()

    :param master: parent
    :param scrollbars: tk.VERTICAL, tk.HORIZONTAL or both
    :param **kwargs: additional parameters that are passed to Frame.__init__
    """
    def __init__(self, master, scrollbars=tk.VERTICAL, **kwargs):
        super().__init__(master, **kwargs)
        self._scrollbar_v = tk.VERTICAL in scrollbars
        self._scrollbar_h = tk.HORIZONTAL in scrollbars

    def put_widget(self, widget):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.widget = widget
        self.widget.grid(row=0, column=0, sticky=tk.N + tk.E + tk.S + tk.W)

        if self._scrollbar_v:
            self.scrollbar_v = ttk.Scrollbar(self, command=self.widget.yview)
            self.scrollbar_v.grid(row=0, column=1, sticky=tk.N + tk.S)
            self.widget.config(yscrollcommand=self.scrollbar_v.set)

        if self._scrollbar_h:
            self.scrollbar_h = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.widget.xview)
            self.scrollbar_h.grid(row=1, column=0, sticky=tk.E + tk.W)
            self.widget.config(xscrollcommand=self.scrollbar_h.set)
        return self

