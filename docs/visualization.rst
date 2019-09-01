Statecharts visualization
=========================

Sismic is not bundle with any graphical tool that can be used to edit or even view a statechart.
Module :py:mod:`sismic.io` contains routines that can be used to (import and) export statecharts to other formats,
some of them being used by third-party tools that support visualising (or editing) statecharts.

Notably, module :py:mod:`sismic.io` contains a function :py:func:`~sismic.io.export_to_plantuml` that exports a given statechart to
`PlantUML <http://plantuml.com/>`__, a tool based on graphviz that can automatically render statecharts (to some extent).
An online version of PlantUML can be found `here <http://www.plantuml.com/plantuml/>`__.

Function :py:func:`~sismic.io.export_to_plantuml` can be directly called from the command-line 
without having to run a Python interpreter, through the ``sismic-plantuml`` (or ``python -m sismic.io.plantuml``)
command-line interface. 

.. code-block:: none

    usage: sismic-plantuml [-h] [--based-on based] [--show-description]
                        [--show-preamble] [--show-state-contracts]
                        [--show-transition-contracts] [--hide-state-action]
                        [--hide-name] [--hide-transition-action]
                        statechart

    Command-line utility to export Sismic statecharts to plantUML. 
    See sismic.io.export_to_plantuml for more informations.

    positional arguments:
    statechart                      A YAML file describing a statechart

    optional arguments:
    -h, --help                      show this help message and exit
    --based-on based                A previously exported PlantUML representation 
                                        for this statechart
    --show-description              Show statechart description
    --show-preamble                 Show statechart preamble
    --show-state-contracts          Show state contracts
    --show-transition-contracts     Show transition contracts
    --hide-state-action             Hide state action
    --hide-name                     Hide statechart name
    --hide-transition-action        Hide transition action


For example, the elevator statechart presented in the previous section can be exported to the following PlantUML excerpt.

.. literalinclude:: /examples/elevator/elevator.plantuml

This PlantUML description can automatically be converted to the following statechart representation 
using the PlantUML tool (an online version can be found `here <http://www.plantuml.com/plantuml/>`__).

.. image:: /examples/elevator/elevator.png
    :align: center




.. seealso:: PlantUML's rendering can be modified to some extent by adjusting the notation used for transitions.
    By default, ``-->`` transitions correspond to downward transitions of good length.

    A transition can be shortened by using ``->`` instead of ``-->``, and the direction of a transition can be
    changed by using ``-up->``, ``-right->``, ``-down->`` or ``-left->``. Both changes can be applied at the same time
    using ``-u->``, ``-r->``, ``-d->`` or ``-l->``.
    See `PlantUML documentation <http://plantuml.com/state-diagram>`__ for more information.

If you already exported a statechart to PlantUML and made some changes to the direction or length of the
transitions, it is likely that you want to keep these changes when exporting again the (possibly modified)
statechart to PlantUML.

The :py:func:`~sismic.io.export_to_plantuml` function accepts two optional (mutually exclusive) parameters ``based_on``
and ``based_on_filepath`` that can be used to provide an earlier version of a PlantUML text representation
(or a path to such a version if ``based_on_filepath`` is used).
This will then be used to incorporate as much as possible the changes made on transitions.

.. autofunction:: sismic.io.export_to_plantuml
    :noindex:


