Python Statechart Simulator
===========================

Python Statechart Simulator for Python >=3.4

.. image:: https://travis-ci.org/AlexandreDecan/PySS.svg
    :target: https://travis-ci.org/AlexandreDecan/PySS
.. image:: https://coveralls.io/repos/AlexandreDecan/PySS/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/AlexandreDecan/PySS?branch=master
.. image:: https://badge.fury.io/py/pyss.svg
    :target: https://pypi.python.org/pypi/PySS
.. image:: https://readthedocs.org/projects/pyss/badge
    :target: https://pyss.readthedocs.org/

PySS provides a set of tools related to statechart manipulation and
execution. In particular, PySS provides:

- An easy way to define and to import statecharts with YAML
- Discrete, step-by-step, fully observable statechart simulation following SCXML (inner-first/source-state) semantic
- Built-in support for Python code, can be easily extended to other languages
- A base framework for model-based testing

Installation
------------

PySS can be installed using ``pip`` as usual: ``pip install pyss``.
This will install the latest stable version.

You can also install PySS from this repository by cloning it.
The development occurs in the *master* branch, the latest stable distributed version is in the *stable* branch.


Documentation
-------------

The latest version of the documentation is available at http://pyss.readthedocs.org/
.

It can also be directly built from the ``docs/`` directory using Sphinx.

Credits
-------

Developed by Alexandre Decan at the University of Mons (Belgium).

GNU Lesser General Public License, version 3.

