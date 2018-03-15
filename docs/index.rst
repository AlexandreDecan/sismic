.. Sismic documentation master file, created by
   sphinx-quickstart on Sun Dec  6 10:35:52 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Sismic user manual
==================

.. image:: https://travis-ci.org/AlexandreDecan/sismic.svg?branch=devel
    :target: https://travis-ci.org/AlexandreDecan/sismic
.. image:: https://coveralls.io/repos/AlexandreDecan/sismic/badge.svg?branch=devel&service=github
    :target: https://coveralls.io/github/AlexandreDecan/sismic?branch=devel
.. image:: https://api.codacy.com/project/badge/grade/10d0a71b01c144859db571ddf17bb7d4
    :target: https://www.codacy.com/app/alexandre-decan/sismic
.. image:: https://badge.fury.io/py/sismic.svg
    :target: https://pypi.python.org/pypi/sismic
.. image:: https://readthedocs.org/projects/sismic/badge/?version=master
    :target: https://sismic.readthedocs.io/s

About
-----

*Sismic* is a recursive acronym that stands for *Sismic Interactive Statechart Model Interpreter and Checker*.

Statecharts are a well-known visual modeling language for representing the executable behavior
of complex reactive event-based systems. Sismic library for Python (version 3.4 or higher) provides a set of
tools to define, validate, simulate, execute and test statecharts.

Sismic is mainly developed by Alexandre Decan at the `University of Mons <http://www.umons.ac.be>`_ and released
publicly under the  `GNU Lesser General Public Licence version 3.0 (LGPLv3) <http://www.gnu.org/licenses/lgpl-3.0.html>`_.


Features
--------

Sismic provides the following features:

- An easy way to define and to import statecharts, based on the human-friendly YAML markup language
- A statechart interpreter offering a discrete, step-by-step, and fully observable simulation engine
- Built-in support for expressing actions and guards using regular Python code, can be easily extended to other programming languages
- A design-by-contract approach for statecharts: contracts can be specified to express invariants, pre- and postconditions on states and transitions
- Runtime checking of behavioral properties expressed as statecharts
- Built-in support for behavior-driven development
- Synchronous and asynchronous simulation, in real time or simulated time
- Support for communication between statecharts and co-simulation
- Statechart visualization using `PlantUML <http://www.plantuml.com/plantuml>`__

Some experimental features are also available as `feature branches <https://github.com/AlexandreDecan/sismic/issues?q=is%3Aopen+is%3Aissue+label%3A%22feature+branch%22>`__.

The semantics of the statechart interpreter is based on the specification of the SCXML semantics (with a few exceptions),
but can be easily tuned to other semantics.
Sismic statecharts provides full support for the majority of the UML 2 statechart concepts:

- simple states, composite states, orthogonal (parallel) states, initial and final states, shallow and deep history states
- state transitions, guarded transitions, automatic (eventless) transitions, internal transitions
- statechart (scoped) variables and their initialisation
- state entry and exit actions, transition actions
- internal and external parametrized events


.. toctree::
    :caption: Overview
    :maxdepth: 2

    installation
    format
    execution
    code

.. toctree::
    :caption: Statechart testing
    :maxdepth: 2

    contract
    properties
    behavior

.. toctree::
    :caption: Advanced topics
    :maxdepth: 2

    time
    integration
    communication
    semantics

.. toctree::
    :caption: Misc
    :maxdepth: 1

    authors
    changelog
    api


Source code
-----------

The source code is available on GitHub:
https://github.com/AlexandreDecan/sismic

Use GitHub's integrated services to contribute suggestions and feature requests for this library or to report bugs.




