Contract programming for statecharts
====================================

Sismic has a built-in support for contract programming for statecharts.

    Design by contract (DbC), also known as contract programming, programming by contract and
    design-by-contract programming, is an approach for designing software. It prescribes that
    software designers should define formal, precise and verifiable interface specifications for
    software components, which extend the ordinary definition of abstract data types with
    **preconditions, postconditions and invariants**. These specifications are referred to as
    "contracts", in accordance with a conceptual metaphor with the conditions and obligations
    of business contracts.
    --- `Wikipedia <https://en.wikipedia.org/wiki/Design_by_contract>`__


Preconditions, postconditions and invariants can be defined for statecharts, and Sismic
will check these conditions at runtime. If a condition is not satisfied, an ``AssertionError``
will be raised. More specifically, one of the three following subclasses will be raised:

.. autoexception:: sismic.model.PreconditionFailed

.. autoexception:: sismic.model.PostconditionFailed

.. autoexception:: sismic.model.InvariantFailed


The three exceptions inherit from the following subclass of ``AssertionError``:

.. autoexception:: sismic.model.ConditionFailed
    :members:


Including conditions in YAML
----------------------------

A YAML definition of a statechart (see :ref:`yaml_statecharts`) can embed the contract definitions.
Preconditions, postconditions and invariants are defined as nested items of a ``contract`` property,
as follows:

.. code:: yaml

    contract:
     - pre: ...
     - post: ...
     - inv: ...

Obviously, more than one condition of each type can be specified:

.. code:: yaml

    contract:
     - pre: ...
     - pre: ...
     - pre: ...
     - post: ...

A condition is an expression that will be evaluated by method :py:meth:`~sismic.evaluator.Evaluator.evaluate_condition`
of an :py:class:`~sismic.evaluator.Evaluator` instance (see :doc:`evaluation`).
..
The following example expects a :py:class:`~sismic.evaluator.PythonEvaluator`, which is the default one.

.. code:: yaml

    contract:
     - pre: x > 0
     - pre: y > 0
     - post: x + y == 0
     - inv: x + y >= 0

While a ``contract`` can be defined both for states and transitions, a contract for a transition can only contain
preconditions (``pre``) and postconditions (``post``) but no invariant (``inv``).

.. code:: yaml

    states:
     - name: s1
       on entry: x = x - 1
       contract:
         - pre: x > 0
       transitions:
         - event: tick
           target: s2
           contract:
            - pre: x >= 0

The semantic is quite intuitive:

 - For states:
    - the preconditions are checked before the state is entered (and before executing the ``on entry`` property).
    - the postconditions are checked after the state is exited (and after executing the ``on exit`` property).
    - the invariants are checked at the end of each micro step. The state must be in the active configuration.
 - For transitions:
    - the preconditions are checked before the process of the transition (and before executing the ``action`` property).
    - the postconditions are checked after the process of the transition (and after executing the ``action`` property).

Example
-------

