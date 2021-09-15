.. Sismic documentation master file, created by
   sphinx-quickstart on Sun Dec  6 10:35:52 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Sismic user manual
==================

.. image:: https://github.com/AlexandreDecan/sismic/actions/workflows/test.yaml/badge.svg?branch=master
    :target: https://github.com/AlexandreDecan/sismic/actions/workflows/test.yaml
.. image:: https://coveralls.io/repos/AlexandreDecan/sismic/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/AlexandreDecan/sismic?branch=master
.. image:: https://badge.fury.io/py/sismic.svg
    :target: https://pypi.org/project/sismic/
.. image:: https://readthedocs.org/projects/sismic/badge/?version=latest
    :target: https://sismic.readthedocs.io/


About
-----

Statecharts are a well-known visual modeling language for specifying the executable behavior
of reactive event-based systems. The essential complexity of statechart models solicits the need for advanced model testing and validation techniques. Sismic is a statechart library for Python (version 3.5 or higher) providing a set of tools to define, validate, simulate, execute and test statecharts. *Sismic* is a recursive acronym that stands for *Sismic Interactive Statechart Model Interpreter and Checker*.

Sismic is mainly developed by Dr. Alexandre Decan as part of his research activities at the `Software Engineering Lab <http://informatique.umons.ac.be/genlog>`_ of the `University of Mons <http://www.umons.ac.be>`_. Sismic is released
as open source under the  `GNU Lesser General Public Licence version 3.0 (LGPLv3) <http://www.gnu.org/licenses/lgpl-3.0.html>`_.

The scientific article `A method for testing and validating executable statechart models <https://doi.org/10.1007/s10270-018-0676-3>`_, published in 2018 in the Springer Software & Systems Modeling journal, describes the method and techniques for modeling, testing and validating statecharts, as supported by Sismic.

Features
--------

Sismic provides the following features:

* An easy way to define and to import statecharts, based on the human-friendly YAML markup language
* A statechart interpreter offering a discrete, step-by-step, and fully observable simulation engine
* Fully controllable simulation clock, with support for real and simulated time
* Built-in support for expressing actions and guards using regular Python code, can be easily extended to other programming languages
* A design-by-contract approach for statecharts: contracts can be specified to express invariants, pre- and postconditions on states and transitions
* Runtime checking of behavioral properties expressed as statecharts
* Built-in support for behavior-driven development
* Support for communication between statecharts
* Synchronous and asynchronous executions
* Statechart visualization using `PlantUML <http://www.plantuml.com/plantuml>`__


The semantics of the statechart interpreter is based on the specification of the SCXML semantics (with a few exceptions),
but can be easily tuned to other semantics.
Sismic statecharts provides full support for the majority of the UML 2 statechart concepts:

* simple states, composite states, orthogonal (parallel) states, initial and final states, shallow and deep history states
* state transitions, guarded transitions, automatic (eventless) transitions, internal transitions and transition priorities
* statechart variables and their initialisation
* state entry and exit actions, transition actions
* internal and external events, parametrized events, delayed events


.. toctree::
    :caption: Overview
    :maxdepth: 2

    installation
    format
    visualization
    execution
    code

.. toctree::
    :caption: Statechart testing
    :maxdepth: 2

    contract
    properties
    behavior
    unittests

.. toctree::
    :caption: Advanced topics
    :maxdepth: 2

    time
    concurrent
    integration

.. toctree::
    :caption: Misc
    :maxdepth: 1

    authors
    changelog
    api


Credits
-------

The Sismic library for Python
is mainly developed by Alexandre Decan at the `University of Mons <http://www.umons.ac.be>`_ with the help
of `many contributors <http://sismic.readthedocs.io/en/latest/authors.html>`_.

Sismic is released publicly under the `GNU Lesser General Public Licence version 3.0 (LGPLv3)
<http://www.gnu.org/licenses/lgpl-3.0.html>`_.

The source code is available on GitHub:
https://github.com/AlexandreDecan/sismic

Use GitHub's integrated services to contribute suggestions and feature requests for this library or to report bugs.

You can cite the research article (`PDF <https://decan.lexpage.net/files/SOSYM-2018.pdf>`_) describing the method and techniques supported by Sismic using:

.. code::

    @article{sismic2018-sosym,
       author = {Mens, Tom and Decan, Alexandre and Spanoudakis, Nikolaos},
       journal = {Software and Systems Modeling},
       publisher = {Springer},
       year = 2018,
       title = {A method for testing and validating executable statechart models},
       doi = {10.1007/s10270-018-0676-3},
       url = {https://doi.org/10.1007/s10270-018-0676-3},
     }

You can cite the Sismic library itself using:

.. code::

    @article{sismic-article,
        title = "Sismic—A Python library for statechart execution and testing",
        journal = "SoftwareX",
        volume = "12",
        pages = "100590",
        year = "2020",
        issn = "2352-7110",
        doi = "10.1016/j.softx.2020.100590",
        url = "https://doi.org/10.1016/j.softx.2020.100590",
        author = "Alexandre Decan and Tom Mens",
    }

or

.. code::

    @software{sismic,
      author = {Decan, Alexandre},
      title = {Sismic Interactive Statechart Model Interpreter and Checker},
      url = {https://github.com/AlexandreDecan/sismic},
    }
