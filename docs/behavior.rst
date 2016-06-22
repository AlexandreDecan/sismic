Behavior-Driven Development (BDD)
=================================

This introduction is inspired by the documentation of `Behave <http://pythonhosted.org/behave/philosophy.html>`__, a Python
library for Behavior-Driven Development (BDD).
BDD is an agile software development technique that encourages collaboration between developers,
QA and non-technical or business participants in a software project.
It was originally named in 2003 by Dan North as a response to test-driven development (TDD),
including acceptance test or customer test driven development practices as found in extreme programming.

BDD focuses on obtaining a clear understanding of desired software behavior through discussion with stakeholders.
It extends TDD by writing test cases in a natural language that non-programmers can read.
Behavior-driven developers use their native language in combination with the language of
domain-driven design to describe the purpose and benefit of their code.
This allows developers to focus on why the code should be created, rather than the technical details,
and minimizes translation between the technical language in which the code is written and the domain language
spoken by the business, users, stakeholders, project management, etc.


The Gherkin language
--------------------

The Gherkin language is a business readable, domain specific language created to support behavior descriptions in BDD.
It lets you describe software’s behaviour without the need to know its implementation details.
Gherkin allows the user to describe a software feature or part of a feature by means of
representative scenarios of expected outcomes.
Like YAML or Python, Gherkin aims to be a human-readable line-oriented language.

Here is an example of a feature and scenario description with Gherkin,
describing part of the intended behaviour of the Unix ls command:

.. code-block:: gherkin

    Feature: ls
    In order to see the directory structure
    As a UNIX user
    I need to be able to list the current directory's contents

    Scenario: List 2 files in a directory
        Given I am in a directory "test"
        And I have a file named "foo"
        And I have a file named "bar"
        When I run "ls"
        Then I should get:
            """
            bar
            foo
            """

As can be seen above, Gherkin files should be written using natural language - ideally
by the non-technical business participants in the software project.
Such feature files serve two purposes: documentation and automated tests.
Using one of the available Gherkin parsers, it is possible to execute the described scenarios and check the expected outcomes.

.. seealso:: A quite complete overview of the Gherkin language is available `here <http://docs.behat.org/en/v2.5/guides/1.gherkin.html>`__.


BDD and Sismic
--------------

Since statecharts are executable pieces of software, it is desirable for
statechart users to be able to describe the intended behavior in terms of
feature and scenario descriptions. 
While it is possible to manually integrate the BDD process with any library or software,
Sismic is bundled with a command-line utility ``sismic-behave`` that automates the integration of BDD.
``sismic-behave`` relies on `Behave <http://pythonhosted.org/behave>`__,
a Python library for BDD with full support of the Gherkin language.

As an illustrative example, let us define the desired behavior of our elevator statechart.
We first create a feature file that contains several scenarios of interest.
By convention, this file has the extension *.feature*, but this is not mandatory.
The example illustrates that Sismic provides a set of predefined steps (e.g., `given`, `when`, `then`) to describe
common statechart behavior without having to write a single line of Python code.

.. literalinclude:: examples/elevator.feature
    :language: gherkin

Let us save this file as *elevator.feature* in the same directory as the statechart description, *elevator.yaml*.
We can then instruct ``sismic-behave``  to run on this statechart the scenarios described in the feature file:

.. code::

    sismic-behave elevator.yaml --features elevator.feature

.. note:: ``sismic-behave`` allows to specify the path to each file, so it is not mandatory to put all of them
    in the same directory. It also accepts multiple files for the ``--features`` parameter, and supports
    all the `command-line parameters of Behave <http://pythonhosted.org/behave/behave.html#command-line-arguments>`__.

``sismic-behave`` will translate the feature file into executable code,
compute the outcomes of the scenarios,
check whether they match what is expected,
and display as summary of all executed scenarios and encountered errors:

.. code::

    [...]

    1 feature passed, 0 failed, 0 skipped
    10 scenarios passed, 0 failed, 0 skipped
    22 steps passed, 0 failed, 0 skipped, 0 undefined
    Took 0m0.027s

Coverage data, including the states that were visited and the transitions that were processed, can be displayed
using the ``--coverage`` argument, as in ``sismic-behave statechart.yaml --feature tests.feature --coverage``:

.. code::

    [...]

    State coverage: 55.56%
    Entered states: floorSelecting (2) | floorListener (1) | doorsOpen (1) | active (1) | movingElevator (1)
    Remaining states: doorsClosed | moving | movingDown | movingUp
    Transition coverage: 12.50%
    Processed transitions: floorSelecting [floorSelected] -> floorSelecting (1)

    [...]



"Given" and "when" steps
------------------------

Given/when I do nothing
    This step should be used to explicitly state that nothing is done.

Given/when I reproduce "{scenario}"
    Allows to reproduce the steps of given scenario.

    .. literalinclude:: examples/elevator.feature
      :language: gherkin
      :lines: 7-10, 18-23
      :emphasize-lines: 6

Given/when I repeat step "{step}" {repeat} times
    Repeat a given step a certain number of times.

Given I disable automatic execution
    Some steps trigger an automatic execution of the statechart (like sending an event or
    awaiting). With this step, one can turn of the automatic execution.

Given I enable automatic execution
    Enable the automatic execution of the statechart (it is enabled by default).

Given/when I import a statechart from {path}
    Import a statechart from a `yaml` file.
    This step is implicitly executed when using ``sismic-behave``.
    It is only needed when calling ``behave`` directly.

Given/when I execute the statechart
    This step executes the statechart.
    It is equivalent to :py:meth:`~sismic.interpreter.Interpreter.execute`.
    It should only be used when automatic execution is disabled.

Given/when I execute once the statechart
    This step executes the statechart once.
    It is equivalent to :py:meth:`~sismic.interpreter.Interpreter.execute_once`.
    It should only be used when automatic execution is disabled.

Given/when I send event {event_name}
    This step sends an event to the statechart,
    and executes the statechart (if automatic execution is enabled).

Given/when I send event {event_name} with {parameter}={value}
    This step sends an event to the statechart with the given parameter.
    The value of the parameter is evaluated as Python code.
    The statechart is executed after this step.
    Additional parameters can be specified using a table, as follows.

    .. literalinclude:: examples/elevator.feature
      :language: gherkin
      :lines: 11-16
      :emphasize-lines: 3-5

Given/when I wait {seconds} seconds
    Increment the internal clock of the statechart, and perform a single execution of the statechart.
    As the execution uses a simulated clock, if the statechart relies on a relative time delta,
    you should consider using the *repeated* version of this step.

Given/when I wait {seconds} seconds {repeat} times
    Repeatedly increment the internal clock of the statechart,
    and execute the statechart after each increment.

    .. literalinclude:: examples/microwave.feature
      :language: gherkin
      :lines: 14-18
      :emphasize-lines: 3

Given I set variable {variable} to {value}
    Set the value of a variable in the internal context of a statechart.
    The value will be evaluated as Python code.


"Then" steps
------------

Then state {state_name} should be active
    Assert that a given state *state_name* is active.

Then state {state_name} should not be active
    Assert that a given state *state_name* is inactive.

Then event {event_name} should be fired
    Assert that a given event *event_name* is the most recently fired event.

    .. literalinclude:: examples/microwave.feature
      :language: gherkin
      :lines: 27-30
      :emphasize-lines: 3

Then event {event_name} should be fired with {parameter}={value}
    Assert that a given event *event_name* was fired during the last execution,
    and that it had an attribute *parameter*
    with given *value*, evaluated as Python code.
    Additional parameters can be specified using a table.

Then event {event_name} should not be fired
    Assert that no event of given name was fired during the last execution.

Then no event should be fired
    Assert that no event was fired by the statechart during the last execution.

Then variable {variable_name} should be defined
    Assert that given variable *variable_name* is defined in the context of the statechart.

Then the value of variable {variable_name} should be {value}
    Assert that given variable *variable_name* is defined and has given *value* in the context of the statechart.
    The value is evaluated as Python code.

Then expression {expression} should hold
    Assert that a given *expression* evaluates to true.
    The expression is evaluated as Python code inside the context of the statechart.

Then the statechart is in a final configuration
    Assert that the statechart is in a final configuration.


.. warning:: The list of steps documented hereabove could be incomplete or contain slight variations.
    An up-to-date list of all the available steps can be found using the ``--steps`` arguments,
    as in ``sismic-behave elevator.yaml --features elevator.feature --steps``.

.. note:: If you do not want to rely on Sismic and want to use *behave* command-line interface, you can easily
    import the predefined steps using ``from sismic.testing.steps import *``.
    This will also import *behave* and all the needed objects to define and use new steps.
    See `Python Step Implementations <http://pythonhosted.org/behave/tutorial.html#python-step-implementations>`__ for more information.
