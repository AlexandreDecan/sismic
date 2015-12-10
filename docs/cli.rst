Command-line interface
======================

PySS is expected to be imported as a Python module, but it also provides
a command-line interface. The CLI can be used by calling the ``pyss``
module (``python -m pyss``) or, if PySS is installed on your system
(e.g. using ``pip``), by directly calling ``pyss`` in your shell.

::

    (shell) pyss -h
    usage: pyss [-h] {execute,validate,test} ...

    Python Statechart Simulator v0.5.2 by Alexandre Decan

    optional arguments:
      -h, --help            show this help message and exit

    subcommands:
      {execute,validate,test}
        execute             execute a statechart
        validate            validate a statechart
        test                test a statechart


.. _cli_execute:

Subcommand: `execute`
---------------------

The CLI can used to execute statecharts.

::

    (shell) pyss execute -h
    usage: pyss execute [-h] [--no-code] [-v] [--events [EVENT [EVENT ...]]] infile

    positional arguments:
      infile                A YAML file describing a statechart

    optional arguments:
      -h, --help            show this help message and exit
      --no-code             Ignore code to be evaluated and executed in the
                            statechart
      -v, --verbosity       set output verbosity: -v displays transitions, -vv
                            displays events and configurations, and -vvv displays
                            states
      --events [EVENT [EVENT ...]]
                            send events to the statechart simulation, eg.
                            name[:key=value[:key=value]]




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


.. _cli_validate:

Subcommand: `validate`
----------------------

YAML statecharts can be validated against PySS format::

    (shell) pyss validate -h
    usage: pyss validate [-h] infile

    positional arguments:
      infile      A YAML file describing a statechart

    optional arguments:
      -h, --help  show this help message and exit


In case of error, a complete traceback will be shown.


.. _cli_test:

Subcommand: `test`
------------------

The CLI can be used to test statecharts using statechart testers.

::

    (shell) pyss test -h
    usage: pyss test [-h] --tests TESTS [TESTS ...] [--no-code] [-l MAXSTEPS]
                     [--events [EVENT [EVENT ...]]]
                     infile

    positional arguments:
      infile                A YAML file describing a statechart

    optional arguments:
      -h, --help            show this help message and exit
      --tests TESTS [TESTS ...]
                            YAML file describing a statechart tester
      --no-code             Ignore code to be evaluated and executed in the
                            statechart
      -l MAXSTEPS, --limit MAXSTEPS
                            limit the number of steps to given number, to prevent
                            infinite loops
      --events [EVENT [EVENT ...]]
                            send events to the statechart simulation, eg.
                            name[:key=value[:key=value]]


For example::

    (shell) python -m pyss test examples/concrete/elevator.yaml --events floorSelected:floor=4 --tests examples/tester/elevator/*.yaml
    All tests passed

The considered statechart is `examples/concrete/history.yaml <https://github.com/AlexandreDecan/PySS/blob/master/examples/concrete/history.yaml>`__.

.. _cli_events:

Parametrized events
-------------------

Events can be parametrized, meaning that you can specify a set of additional data that will be bundled
with the event. The syntax follows:

    event_name[:key=value[:key=value[...]]]

For example, the following call to *execute* subcommand sends an event ``floorSelected`` and passes
an additional parameter ``floor`` whose value is ``4``.

::

    (shell) pyss execute examples/concrete/elevator.yaml --events floorSelected:floor=4


The value is evaluated using Python's :py:func:`eval` function, meaning that you can pass nearly everything you
want to, including numbers, Boolean, string (enclosed by single or double quotes), etc.