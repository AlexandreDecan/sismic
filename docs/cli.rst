Command-line interface
======================

PySS is expected to be imported as a Python module, but it also provides
a command-line interface. The CLI can be used by calling the ``pyss``
module (``python -m pyss``) or, if PySS is installed on your system
(e.g. using ``pip``), by directly calling ``pyss`` in your shell.

::

    (shell) pyss -h
    usage: pyss [-h] {execute} ...

    Python Statechart Simulator v0.3.2 by Alexandre Decan

    optional arguments:
      -h, --help  show this help message and exit

    subcommands:
      {execute}
        execute   execute a statechart

.. _cli_execute:

Subcommand: `execute`
---------------------

::

    (shell) pyss execute -h
    usage: pyss execute [-h] [--python] [-v] [--events [EVENT [EVENT ...]]] infile

    positional arguments:
      infile                A YAML file describing a statechart

    optional arguments:
      -h, --help            show this help message and exit
      --python              use Python to execute and evaluate the actions and
                            conditions.
      -v, --verbosity       set output verbosity: -v displays transitions, -vv
                            displays events and configurations, and -vvv displays
                            states
      --events [EVENT [EVENT ...]]
                            send events to the statechart simulation


For example::

    (shell) pyss execute -vvv  examples/concrete/history.yaml --events next pause
    Initial configuration: loop, s1
    Events sent: next, pause
    Step 1 - Considered event: next
    Transition: s1+next -> s2
    Exited states: s1
    Entered states: s2
    Configuration: loop, s2
    Step 2 - Considered event: pause
    Transition: loop+pause -> pause
    Exited states: s2, loop
    Entered states: pause
    Configuration: pause
    Final: False

The considered statechart is `examples/concrete/history.yaml <https://github.com/AlexandreDecan/PySS/blob/master/examples/concrete/history.yaml>`__.