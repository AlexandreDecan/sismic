.. PySS documentation master file, created by
   sphinx-quickstart on Sun Dec  6 10:35:52 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to PySS's documentation!
================================

Python Statechart Simulator for Python >=3.4

.. image:: https://travis-ci.org/AlexandreDecan/PySS.svg
    :target: https://travis-ci.org/AlexandreDecan/PySS
.. image:: https://coveralls.io/repos/AlexandreDecan/PySS/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/AlexandreDecan/PySS?branch=master
.. image:: https://badge.fury.io/py/pyss.svg
    :target: https://pypi.python.org/pypi/PySS
.. image:: https://readthedocs.org/projects/pyss/badge/?version=latest
    :target: https://pyss.readthedocs.org/en/latest

PySS provides a set of tools related to statechart manipulation and
execution. In particular, PySS provides:

- An easy way to define and to import statecharts with YAML
- Discrete, step-by-step, fully observable statechart simulation following SCXML semantic
- Built-in support for Python code, can be easily extended to other languages
- A base framework for model-based testing

Overview
--------

PySS has a complete support for simple state, composite state,
orthogonal (parallel) state, initial state, final state, history state
(including shallow and deep semantics), internal transition, guarded
transition, eventless transition, statechart entry action, state entry
action, state exit action, transition action, internal and external
events and parametrized events.

We aim to support the following features soon:

- Static visualization (export to GraphViz)
- Import statecharts from Yakindu
- Runtime dynamic visualization and manipulation

Contents
--------

This is the latest version of the documentation. The documentation for the stable version
can be found at http://pyss.readthedocs.org/en/stable/

.. toctree::
    :maxdepth: 2

    quickstart
    format
    execution
    evaluation
    cli


Source code
===========

The source code is available on GitHub:
https://github.com/AlexandreDecan/PySS

You can use GitHub integrated services to contribute or to report bugs and suggestions.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

