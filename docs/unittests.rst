Statechart unit testing
=======================

About unit testing
------------------

Like any executable software artefacts, statecharts can and should be tested during their development.
Like most other software libraries, the execution of Sismic can be checked with unit tests, including the execution of statecharts with Sismic. 

There are many unit testing frameworks in Python. 
Internally, Sismic relies on `pytest <https://docs.pytest.org/en/latest/>`__ to check its own implementation
as well as the execution of the statecharts provided as examples in the documentation.

Sismic API (especially the interpreter API) is open enough to make advanced unit testing possible.
To ease the writing of unit tests, Sismic is bundled with :py:mod:`sismic.testing` module providing a set of common test primitives that can be used independently of a specific test framework. 

Of course, these primitives do not cover all use cases, but cover the most frequent assertions that can be expected when the execution of a statechart has to be checked. 
Also, because some primitives are very easy to implement using the existing API, they are not included
with this module. 

For example:

 * State 'name' is active: ``'name' in interpreter.configuration``;
 * Variable 'x' has value y: ``interpreter.context['x'] = y``;
 * Statechart is in a final configuration: ``interpreter.final``;
 * ...


Primitives for unit testing
---------------------------

.. automodule:: sismic.testing
    :noindex:
    :members:
    :member-order: bysource
    :show-inheritance:
    :inherited-members:
    :imported-members:


