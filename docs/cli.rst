Command-line interface
======================

Sismic is expected to be imported as a Python module, but it also provides
a command-line interface. The CLI can be used by calling the ``sismic``
module (``python -m sismic``) or, if PySS is installed on your system
(e.g. using ``pip``), by directly calling ``sismic`` in your shell.

::

    (shell) sismic -h
    usage: sismic [-h] {execute,validate,test} ...

    Sismic Interactive State Machine Interpreter and Checker v0.9.0 (by Alexandre
    Decan -- https://github.com/AlexandreDecan/sismic/)

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

    (shell) sismic execute -h
    usage: sismic execute [-h] [-v] [--no-code] [--silent-contract] [-l MAXSTEPS]
                          [--events [EVENT [EVENT ...]]]
                          infile

    positional arguments:
      infile                A YAML file describing a statechart

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbosity       set output verbosity: -v displays transitions, -vv
                            displays events and configurations, and -vvv displays
                            states
      --no-code             Ignore code to be evaluated and executed in the
                            statechart
      --silent-contract     Do not raise exception if a contract is not satisfied
      -l MAXSTEPS, --limit MAXSTEPS
                            limit the number of steps to given number, to prevent
                            infinite loops
      --events [EVENT [EVENT ...]]
                            send events to the statechart simulation, eg.
                            name[:key=value[:key=value]]


For example::

    (shell) sismic execute -vvv  examples/concrete/history.yaml --events next pause
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

The considered statechart is `examples/concrete/history.yaml <https://github.com/AlexandreDecan/sismic/blob/master/examples/concrete/history.yaml>`__.


.. _cli_validate:

Subcommand: `validate`
----------------------

YAML statecharts can be validated against Sismic format::

    (shell) sismic validate -h
    usage: sismic validate [-h] infile

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

    (shell) sismic test -h
    usage: sismic test [-h] --tests TESTS [TESTS ...] [--no-code]
                       [--silent-contract] [-l MAXSTEPS]
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
      --silent-contract     Do not raise exception if a contract is not satisfied
      -l MAXSTEPS, --limit MAXSTEPS
                            limit the number of steps to given number, to prevent
                            infinite loops
      --events [EVENT [EVENT ...]]
                            send events to the statechart simulation, eg.
                            name[:key=value[:key=value]]



For example::

    (shell) sismic test examples/concrete/elevator.yaml --events floorSelected:floor=4 --tests examples/tester/elevator/*.yaml
    All tests passed

The considered statechart is `examples/concrete/history.yaml <https://github.com/AlexandreDecan/sismic/blob/master/examples/concrete/history.yaml>`__.

.. _cli_events:

Parametrized events
-------------------

Events can be parametrized, meaning that you can specify a set of additional data that will be bundled
with the event. The syntax follows:

    event_name[:key=value[:key=value[...]]]

For example, the following call to *execute* subcommand sends an event ``floorSelected`` and passes
an additional parameter ``floor`` whose value is ``4``.

::

    (shell) sismic execute examples/concrete/elevator.yaml --events floorSelected:floor=4


The value is evaluated using Python's :py:func:`eval` function, meaning that you can pass nearly everything you
want to, including numbers, Boolean, string (enclosed by single or double quotes), etc.