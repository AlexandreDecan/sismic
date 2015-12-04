# Use the command-line interface to execute statechart

PySS is expected to be imported as a Python module, but it also provides
a command-line interface. The CLI can be used by calling the ``pyss``
module (``python -m pyss``) or, if PySS is installed on your system
(e.g. using ``pip``), by directly calling ``pyss`` in your shell.

::

    (shell) pyss -h
    usage: pyss [-h] [--evaluator {python,dummy}] [-v]
                [--events [EVENTS [EVENTS ...]]]
                infile

    Python Statechart Simulator v0.2.0 by Alexandre Decan

    positional arguments:
      infile                A YAML file describing a statechart

    optional arguments:
      -h, --help            show this help message and exit
      --evaluator {python,dummy}
                            Evaluator to use for code
      -v                    Level of details, -v ads configurations, -vv adds
                            events, -vvv adds transitions
      --events [EVENTS [EVENTS ...]]
                            A list of event names


An example of a call:

::

    (shell) pyss examples/concrete/history.yaml --evaluator=dummy --events next pause continue next pause stop -v
    Initial configuration: ['s1', 'loop']
    -- Configuration: ['s2', 'loop']
    -- Configuration: ['pause']
    -- Configuration: ['s2', 'loop']
    -- Configuration: ['s3', 'loop']
    -- Configuration: ['pause']
    -- Configuration: ['stop']
    Final: True

