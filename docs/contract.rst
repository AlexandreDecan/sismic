Design by Contract for statecharts
==================================

About Design by Contract
------------------------

Design by Contract (DbC) was introduced by Bertrand Meyer and popularised through his object-oriented Eiffel programming language.
Several other programming languages also provide support for DbC.
The main idea is that the specification of a software component (e.g., a method, function or class) is
extended with a so-called *contract* that needs to be respected when using this component.
Typically, the contract is expressed in terms of preconditions, postconditions and invariants.
We have additionally added so-called sequential conditions on top of this.

    Design by contract (DbC), also known as contract programming, programming by contract and
    design-by-contract programming, is an approach for designing software. It prescribes that
    software designers should define formal, precise and verifiable interface specifications for
    software components, which extend the ordinary definition of abstract data types with
    **preconditions, postconditions and invariants**. These specifications are referred to as
    "contracts", in accordance with a conceptual metaphor with the conditions and obligations
    of business contracts.
    --- `Wikipedia <https://en.wikipedia.org/wiki/Design_by_contract>`__


DbC for statechart models
-------------------------

While DbC has gained some amount of acceptance at the programming level,
there is hardly any support for it at the modeling level.

Sismic aims to change this, by integrating support for Design by Contract for statecharts.
The basic idea is that contracts can be defined on statechart componnents (states or transitions),
by specifying preconditions, postconditions, invariants and sequential conditions (i.e. conditions that must be
sequentially satisfied) on them.
At runtime, Sismic will verify the conditions specified by the constracts.
If a condition is not satisfied, a :py:exc:`~sismic.exceptions.ContractError` will be raised.
More specifically, one of the following 4 error types wil be raised: :py:exc:`~sismic.exceptions.PreconditionError`,
:py:exc:`~sismic.exceptions.PostconditionError`, :py:exc:`~sismic.exceptions.InvariantError`,
or :py:exc:`~sismic.exceptions.SequentialConditionError`.

Contracts can be specified for any state contained in the statechart, and for any transition contained in the statechart.
A state contract can contain preconditions, postconditions, invariants and/or sequential conditions.
At transition level, sequential conditions are not allowed.
The semantics for evaluating a contract is as follows:

 - For states:
    - state preconditions are checked before the state is entered (i.e., **before** executing *on entry*), in the order of occurrence of the preconditions.
    - state postconditions are checked after the state is exited (i.e., **after** executing *on exit*), in the order of occurrence of the postconditions.
    - state invariants are checked at the end of each *macro step*, in the order of occurrence of the invariants. The state must be in the active configuration.
    - sequential conditions on a state are initialized after a state is entered (i.e., **after** executing *on entry*), and
      evaluated before the state is exited (i.e., **before** executing *on exit*).
      The evaluation of the sequential condition is updated at each step as long as the state remains in the active configuration.
 - For transitions:
    - the preconditions are checked before starting the process of the transition (and **before** executing the optional transition action).
    - the postconditions are checked after finishing the process of the transition (and **after** executing the optional transition action).
    - the invariants are checked twice: one before starting and a second time after finishing the process of the transition.


Defining contracts in YAML
--------------------------

Contracts can easily be added to the YAML definition of a statechart (see :ref:`yaml_statecharts`) through the use of the *contract* property.
Preconditions, postconditions, invariants and sequential conditions are defined as nested items of the *contract* property.
The name of these optional contractual conditions is respectively *before* (for preconditions), *after* (for postconditions),
*always* (for invariants), and *sequentially* (for sequential conditions):

.. code:: yaml

    contract:
     - before: ...
     - after: ...
     - always: ...
     - sequentially: ...

Obviously, more than one condition of each type can be specified:

.. code:: yaml

    contract:
     - before: ...
     - before: ...
     - before: ...
     - after: ...

A condition is an expression that will be evaluated by an :py:class:`~sismic.evaluator.Evaluator`
instance (see :doc:`code`).

.. code:: yaml

    contract:
     - before: x > 0
     - before: y > 0
     - after: x + y == 0
     - always: x + y >= 0

Here is an example of a contracts defined at state level:

.. code:: yaml

    statechart:
      name: example
      initial state:
        name: root
        contract:
         - always: x >= 0
         - always: not active('initial') or x > 0

If the default :py:class:`~sismic.code.PythonEvaluator` is used,
it is possible to refer to the old value of some variable used in the statechart, by prepending ``__old__``.
This is particularly useful when specifying postconditions and invariants:

.. code:: yaml

    contract:
      always: d > __old__.d
      after: (x - __old__.x) < d

See the documentation of :py:class:`~sismic.code.PythonEvaluator` for more information.


Sequential conditions
*********************

Sequential conditions can be used to describe what should happen when residing in a particular state, and in which order.
A sequential condition makes use of some logical and temporal operators, and of *classical* conditions that
will be evaluated by an :py:class:`~sismic.code.Evaluator` instance (by default, a :py:class:`~sismic.code.PythonEvaluator` one).

Refer to the documentation of :py:func:`~sismic.code.sequence.build_sequence` for more information about the
supported operators. You will never call this function directly, but the documentation explains the implemented
mini-language and the supported operators and their semantics.

.. autofunction:: sismic.code.sequence.build_sequence

Please be warned: the syntax allowed in sequential conditions may conflict with YAML's one.
Protect your sequential conditions by using quotes or by using the multi-line marker "|".

Example
*******

The following example shows some contract specifications added
to the `Elevator example <https://github.com/AlexandreDecan/sismic/blob/master/examples/elevator/elevator.yaml>`__.

.. literalinclude:: /examples/elevator/elevator_contract.yaml
   :language: yaml


Executing statecharts containing contracts
------------------------------------------

The execution of a statechart that contains contracts does not essentially differ
from the execution of a statechart that does not.
The only difference is that conditions of each contract are checked
at runtime (as explained above) and may raise a subclass of :py:exc:`~sismic.exceptions.ContractError`.

.. testcode::

    from sismic.model import Event
    from sismic.interpreter import Interpreter
    from sismic.io import import_from_yaml

    with open('examples/elevator/elevator_contract.yaml') as f:
        statechart = import_from_yaml(f)

        # Make the run fails
        statechart.state_for('movingUp').preconditions[0] = 'current > destination'

        interpreter = Interpreter(statechart)
        interpreter.queue(Event('floorSelected', floor=4))
        interpreter.execute()

Here we manually changed one of the preconditions such that it failed at runtime.
The exception displays some relevant information to help debug:

.. testoutput::
    :options: +ELLIPSIS

    Traceback (most recent call last):
     ...
    sismic.exceptions.PreconditionError: Precondition not satisfied!
    Object: BasicState(movingUp)
    Assertion: current > destination
    Configuration: ['active', 'floorListener', 'movingElevator', 'floorSelecting']
    Step: MicroStep(None, doorsClosed -> movingUp, >['moving', 'movingUp'], <['doorsClosed'])
    Evaluation context:
     - destination = 4
     - doors = <Doors object at ...>
     - current = 0
     - Doors = <class 'Doors'>


If you do not want the execution to be interrupted by such exceptions, you can set the ``ignore_contract``
parameter to ``True`` when constructing an ``Interpreter``.
This way, no contract checking will be done during the execution.



