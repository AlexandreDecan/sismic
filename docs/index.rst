.. PySS documentation master file, created by
   sphinx-quickstart on Sun Dec  6 10:35:52 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Sismic's documentation!
==================================

Sismic Interactive State Machine Interpreter and Checker, for Python >= 3.4

.. image:: https://travis-ci.org/AlexandreDecan/sismic.svg
    :target: https://travis-ci.org/AlexandreDecan/sismic
.. image:: https://coveralls.io/repos/AlexandreDecan/sismic/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/AlexandreDecan/sismic?branch=master
.. image:: https://badge.fury.io/py/sismic.svg
    :target: https://pypi.python.org/pypi/sismic
.. image:: https://readthedocs.org/projects/sismic/badge
    :target: https://sismic.readthedocs.org/


About statecharts
-----------------

Statecharts are a well-known visual language for modeling the executable behavior of complex reactive event-based systems.
They were invented in the 1980s by David Harel, and have gained a more widespread adoption since they became part of
the UML modeling standard.

Statecharts offer more sophisticated modeling concepts than the more classical state diagrams of finite state machines.
For example, they support hierarchical composition of states, orthogonal regions
to express parallel execution, guarded transitions, and actions on transitions or states. Different flavours of
executable semantics for statecharts have been proposed in the literature and in existing tools.


Overview
--------

The Sismic library for Python provides a set of tools to define, simulate, execute and debug statecharts. More specifically, Sismic provides:

 - An easy way to define and to import statecharts, based on the human-friendly YAML markup language
 - A statechart simulator offering discrete, step-by-step, and fully observable simulation engine
 - Built-in support for expressing actions and guards using regular Python code
 - A unit testing framework for statecharts

Sismic provides full support for the majority of the concepts of UML statecharts:

 - simple states, composite states, orthogonal (parallel) states, initial and final states, shallow and deep history states
 - state transitions, guarded transitions, automatic (eventless) transitions
 - statechart variables and their initialisation
 - state entry and exit actions, transition actions
 - internal and external events, parametrized events

The Sismic library is written in a modular way:

 - The semantics of the statechart simulator is based on the specification of the SCXML semantics (with a few exceptions),
   and can be easily tuned to other semantics.
 - While currently, guards and actions are expressed in Python, this support can be easily extended to other languages.

Contents
--------

.. toctree::
    :maxdepth: 2

    quickstart
    format
    execution
    evaluation
    testing
    cli


Source code
===========

The source code is available on GitHub:
https://github.com/AlexandreDecan/sismic

Use GitHub's integrated services to contribute suggestions and feature requests for this library or to report bugs.




