Sismic for Python
=================

.. image:: https://travis-ci.org/AlexandreDecan/sismic.svg?branch=master
    :target: https://travis-ci.org/AlexandreDecan/sismic
.. image:: https://coveralls.io/repos/AlexandreDecan/sismic/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/AlexandreDecan/sismic?branch=master
.. image:: https://api.codacy.com/project/badge/grade/10d0a71b01c144859db571ddf17bb7d4
    :target: https://www.codacy.com/app/alexandre-decan/sismic
.. image:: https://badge.fury.io/py/sismic.svg
    :target: https://pypi.python.org/pypi/sismic
.. image:: https://readthedocs.org/projects/sismic/badge/?version=stable
    :target: https://sismic.readthedocs.org/en/stable

Sismic Interactive State Machine Interpreter and Checker
--------------------------------------------------------

Statecharts are a well-known visual language for modeling the executable behavior of complex reactive event-based systems.
The Sismic library for Python >= 3.4 provides a set of tools to define, validate, simulate, execute and debug statecharts.
More specifically, Sismic provides:

- An easy way to define and to import statecharts, based on the human-friendly YAML markup language
- A statechart interpreter offering a discrete, step-by-step, and fully observable simulation engine
- Synchronous and asynchronous simulation, in real time or simulated time
- Support for communication between statecharts and co-simulation
- Built-in support for expressing actions and guards using regular Python code
- A design-by-contract approach for statecharts
- A unit testing framework for statecharts, including generation of test scenarios


Installation
------------

Sismic can be installed using ``pip`` as usual: ``pip install sismic``.
This will install the latest stable version.

You can also install Sismic from this repository by cloning it.
The development occurs in the *master* branch, the latest stable distributed version is in the *stable* branch.

Sismic requires Python >=3.4

Documentation
-------------

The documentation for the latest distributed version is available at `sismic.readthedocs.org <http://sismic.readthedocs.org/>`_.

Many examples are available in `docs/examples <https://github.com/AlexandreDecan/sismic/tree/master/docs/examples>`_.

The documentation can also be directly built from the `docs <https://github.com/AlexandreDecan/sismic/tree/master/docs>`_ directory using Sphinx.


Changelog
---------

See documentation's `changelog <http://sismic.readthedocs.org/en/stable/changelog.html>`_.
Unreleased changes are visible `here <CHANGELOG.rst>`_.

Credits
-------

The Sismic library for Python
is developed at the `Software Engineering Lab <http://informatique.umons.ac.be/genlog>`_
of the `University of Mons <http://www.umons.ac.be>`_
as part of an ongoing software modeling research project.

Sismic is released publicly under the `GNU Lesser General Public Licence version 3.0 (LGPLv3)
<http://www.gnu.org/licenses/lgpl-3.0.html>`_.
