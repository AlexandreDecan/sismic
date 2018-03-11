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
by specifying preconditions, postconditions, and invariants on them.
At runtime, Sismic will verify the conditions specified by the constracts.
If a condition is not satisfied, a :py:exc:`~sismic.exceptions.ContractError` will be raised.
More specifically, one of the following 4 error types wil be raised: :py:exc:`~sismic.exceptions.PreconditionError`,
:py:exc:`~sismic.exceptions.PostconditionError`, :py:exc:`~sismic.exceptions.InvariantError`,
or :py:exc:`~sismic.exceptions.SequentialConditionError`.

Contracts can be specified for any state contained in the statechart, and for any transition contained in the statechart.
A state contract can contain preconditions, postconditions, and/or invariants.
The semantics for evaluating a contract is as follows:

 - For states:
    - state preconditions are checked before the state is entered (i.e., **before** executing *on entry*), in the order of occurrence of the preconditions.
    - state postconditions are checked after the state is exited (i.e., **after** executing *on exit*), in the order of occurrence of the postconditions.
    - state invariants are checked at the end of each *macro step*, in the order of occurrence of the invariants. The state must be in the active configuration.
 - For transitions:
    - the preconditions are checked before starting the process of the transition (and **before** executing the optional transition action).
    - the postconditions are checked after finishing the process of the transition (and **after** executing the optional transition action).
    - the invariants are checked twice: one before starting and a second time after finishing the process of the transition.


Defining contracts in YAML
--------------------------

Contracts can easily be added to the YAML definition of a statechart (see :ref:`yaml_statecharts`) through the use of the *contract* property.
Preconditions, postconditions, and invariants are defined as nested items of the *contract* property.
The name of these optional contractual conditions is respectively *before* (for preconditions), *after* (for postconditions),
and *always* (for invariants):

.. code:: yaml

    contract:
     - before: ...
     - after: ...
     - always: ...

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
      root state:
        name: root
        contract:
         - always: x >= 0
         - always: not active('other state') or x > 0

If the default :py:class:`~sismic.code.PythonEvaluator` is used,
it is possible to refer to the old value of some variable used in the statechart, by prepending ``__old__``.
This is particularly useful when specifying postconditions and invariants:

.. code:: yaml

    contract:
      always: d > __old__.d
      after: (x - __old__.x) < d

See the documentation of :py:class:`~sismic.code.PythonEvaluator` for more information.


Executing statecharts containing contracts
------------------------------------------

The execution of a statechart that contains contracts does not essentially differ
from the execution of a statechart that does not.
The only difference is that conditions of each contract are checked
at runtime (as explained above) and may raise a subclass of :py:exc:`~sismic.exceptions.ContractError`.

.. testcode::

    from sismic.interpreter import Interpreter, Event
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
    sismic.exceptions.PreconditionError: PreconditionError
    Object: BasicState('movingUp')
    Assertion: current > destination
    Configuration: ['active', 'floorListener', 'movingElevator', 'floorSelecting', 'moving']
    Step: MicroStep(transition=Transition('doorsClosed', 'movingUp', event=None), entered_states=['moving', 'movingUp'], exited_states=['doorsClosed'])
    Context:
     - current = 0
     - destination = 4
     - doors_open = False




If you do not want the execution to be interrupted by such exceptions, you can set the ``ignore_contract``
parameter to ``True`` when constructing an ``Interpreter``.
This way, no contract checking will be done during the execution.



