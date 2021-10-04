Sismic for Python
=================

.. image:: https://github.com/AlexandreDecan/sismic/actions/workflows/test.yaml/badge.svg?branch=master
    :target: https://github.com/AlexandreDecan/sismic/actions/workflows/test.yaml
.. image:: https://coveralls.io/repos/AlexandreDecan/sismic/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/AlexandreDecan/sismic?branch=master
.. image:: https://badge.fury.io/py/sismic.svg
    :target: https://pypi.org/project/sismic/
.. image:: https://readthedocs.org/projects/sismic/badge/?version=latest
    :target: https://sismic.readthedocs.io/

Sismic Interactive Statechart Model Interpreter and Checker
-----------------------------------------------------------

*Sismic* is a recursive acronym that stands for *Sismic Interactive Statechart Model Interpreter and Checker*.

Statecharts are a well-known visual modeling language for representing the executable behavior
of complex reactive event-based systems. Sismic library for Python (version 3.5 or higher) provides a set of
tools to define, validate, simulate, execute and test statecharts.
More specifically, Sismic provides:

- An easy way to define and to import statecharts, based on the human-friendly YAML markup language
- A statechart interpreter offering a discrete, step-by-step, and fully observable simulation engine
- Fully controllable simulation clock, with support for real and simulated time
- Built-in support for expressing actions and guards using regular Python code, can be easily extended to other programming languages
- Support for Design by Contract (DbC) for statecharts: contracts can be specified to express invariants, pre- and postconditions on states and transitions
- Runtime monitoring of behavioral properties expressed as statecharts
- Built-in support for behavior-driven development (BDD)
- Support for communication between statecharts
- Synchronous and asynchronous executions
- Statechart visualization using `PlantUML <http://www.plantuml.com/plantuml>`__


Installation
------------

Sismic requires Python >=3.5.
Sismic can be installed using ``pip`` as usual: ``pip install sismic``.
This will install the latest stable version.

You can also install Sismic from this repository by cloning it.

Starting from release 1.0.0, Sismic adheres to a `semantic versioning <https://semver.org>`__ scheme.


Documentation
-------------

The documentation for the latest distributed version is available on `sismic.readthedocs.io <http://sismic.readthedocs.io/>`_.

Many examples are available in `docs/examples <https://github.com/AlexandreDecan/sismic/tree/master/docs/examples>`_.

The documentation can also be directly built from the `docs <https://github.com/AlexandreDecan/sismic/tree/master/docs>`_ directory using Sphinx.

The scientific article `A method for testing and validating executable statechart models <https://doi.org/10.1007/s10270-018-0676-3>`_ presenting the method and techniques supported by Sismic for validating and testing statecharts, is published in Springer's Software and Systems modeling journal in 2018.


Changelog
---------

See documentation's `changelog <https://sismic.readthedocs.io/en/latest/changelog.html>`_.


Credits
-------

The Sismic library for Python is mainly developed by Alexandre Decan at the
`Software Engineering Lab <http://informatique.umons.ac.be/genlog>`_ of the `University of Mons <http://www.umons.ac.be>`_ with the help of `many contributors <http://sismic.readthedocs.io/en/latest/authors.html>`_.

Sismic is released as open source software under the `GNU Lesser General Public Licence version 3.0 (LGPLv3)
<http://www.gnu.org/licenses/lgpl-3.0.html>`_.


You can cite the Sismic library using:

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


You can cite the associated research article (`PDF <https://decan.lexpage.net/files/SOSYM-2018.pdf>`_) using:

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


External Resources
------------------

The following resources provide additional information about statecharts that may be of use, even if it is not immediately related to Sismic.

* `Yakindu Statechart tools <https://www.itemis.com/en/yakindu/state-machine/>`__: commercial software for visual simulation, debugging, testing and code generation from statecharts. A free academic licence can be obtained for universities.
* A `YouTube playlist <https://www.youtube.com/playlist?list=PLmHMvhX5wK_aohX5sOeAMogFDwlc3gJYR>`__ providing a set of introductory tutorials about statechart modeling and simulation (based on the aforementioned Yakindu tool).

(If some of the links provided above turn out to be dead, or if you know other relevant resources that should be added here, please contact us.)
