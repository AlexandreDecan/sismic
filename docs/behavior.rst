Behavior-driven development
===========================

This introduction is borrowed from `Behave documentation <http://pythonhosted.org/behave/philosophy.html>`__.

Behavior-driven development (or BDD) is an agile software development technique that encourages collaboration between developers, QA and non-technical or business participants in a software project.
It was originally named in 2003 by Dan North as a response to test-driven development (TDD), including acceptance test or customer test driven development practices as found in extreme programming.
It has evolved over the last few years.

On the “Agile specifications, BDD and Testing eXchange” in November 2009 in London, Dan North gave the following definition of BDD:

    BDD is a second-generation, outside–in, pull-based, multiple-stakeholder, multiple-scale, high-automation, agile methodology.
    It describes a cycle of interactions with well-defined outputs, resulting in the delivery of working, tested software that matters.

BDD focuses on obtaining a clear understanding of desired software behavior through discussion with stakeholders.
It extends TDD by writing test cases in a natural language that non-programmers can read.
Behavior-driven developers use their native language in combination with the ubiquitous language of domain-driven design to describe the purpose and benefit of their code.
This allows the developers to focus on why the code should be created, rather than the technical details, and minimizes translation between the technical language in which the code is written and the domain language spoken by the business, users, stakeholders, project management, etc.



The Gherkin language
--------------------

The Gherkin language is a business readable, domain specific language created to support behavior descriptions.
It lets you describe software’s behaviour without detailing how that behaviour is implemented.
Gherkin allows the user to describe a feature or part of a feature with representative examples of expected outcomes.

Like YAML or Python, Gherkin is intented to be a human-readable line-oriented language.

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

With Gherkin, such a feature file can serve both as documentation and as automated tests.
These files should be written using natural language - ideally by the non-technical business participants in the software project.
Feature files serve two purposes – documentation and automated tests.

Using one of the available Gherkin parser, one can easily execute the described scenarios and check the expected outcomes.

.. seealso:: A quite complete overview of the Gherkin language is available `here <http://docs.behat.org/en/v2.5/guides/1.gherkin.html>`__.


BDD and Sismic
--------------

The implementation of the various steps of a scenario into executable code is usually the developer's responsibility.
There are many available tools to easily describe the relationship between the elements of a feature file written in
Gherkin and the pieces of code that implements those elements.

Although it is possible to manually integrate the BDD process with any library or software, Sismic is bundled with a command-line utility that does the job for you.
Sismic allows you to not have to write this code, or to use such tools.
Sismic command-line utility, namely ``sismic-behave``, relies on `Behave <http://pythonhosted.org/behave>`__, a Python library for BDD with full support of Gherkin syntax, to bring BDD to statecharts.

Suppose we wish to define the expected behavior of our running example, the elevator.
We first create a feature file that contains several scenarios of interest.
By convention, this file has the extension *.feature* but it is not mandatory.

.. literalinclude:: examples/elevator.feature
    :language: gherkin

Let us save this file as *elevator.feature* in the same directory than the definition of our statechart, *elevator.yaml*.

.. note:: As the command-line utility allows to specify the path to each file, it is not mandatory to put all of them
    in a single directory.

We then ask Sismic to run the scenarios described in this feature file, using our statechart.

.. code::

    sismic-behave elevator.yaml --features elevator.feature

Running this command will translate given feature file into executable code, compute the outcomes of the scenarios and check whether they match what is expected.
The command then displays the set of executed scenarios, the encountered errors, and a short summary.

.. code::

    [...]

    1 feature passed, 0 failed, 0 skipped
    10 scenarios passed, 0 failed, 0 skipped
    22 steps passed, 0 failed, 0 skipped, 0 undefined
    Took 0m0.027s

.. note:: ``sismic-behave`` accepts multiple files for the ``--features`` parameter.
    It also supports all the command-line parameters of Behave.
    See `Behave command-line arguments <http://pythonhosted.org/behave/behave.html#command-line-arguments>`__ for more information.

Sismic is bundled with a set of predefined steps, allowing you to describe common statechart behavior without having to write a single line of Python code.

.. note:: If you do not want to rely on Sismic and want to use *behave* command-line interface, you can easily
    import the predefined steps using ``from sismic.testing.steps import *``.
    This will also import *behave* and all the needed objects to define and use new steps.
    See `Python Step Implementations <http://pythonhosted.org/behave/tutorial.html#python-step-implementations>`__ for more information.


"Given" and "when" steps
------------------------

Given/when I do nothing
    This step should be use to explicitly state that nothing is done.

Given/when I reproduce "{scenario}"
    Reproduce the steps of given scenario's name.

    .. literalinclude:: examples/elevator.feature
      :language: gherkin
      :lines: 7-10, 18-23
      :emphasize-lines: 6

Given/when I repeat step "{step}" {repeat} times
    Repeat given step.

Given I disable automatic execution
    Some steps trigger an automatic execution of the statechart (like sending an event or
    awaiting). With this step, one can turn of the automatic execution.

Given I enable automatic execution
    Enable the automatic execution of the statechart (enabled by default).

Given/when I import a statechart from {path}
    Import a statechart from a yaml file.
    This step is implicitly executed when you use ``sismic-behave`` and is not needed unless
    you call ``behave`` directly.

Given/when I execute the statechart
    Execute the statechart, equivalent to :py:meth:`~sismic.interpreter.Interpreter.execute`.
    Should not be used unless automatic execution is disabled.

Given/when I execute once the statechart
    Execute the statechart, equivalent to :py:meth:`~sismic.interpreter.Interpreter.execute_once`.
    Should not be used unless automatic execution is disabled.

Given/when I send event {event_name}
    Send an event to the statechart, and execute the statechart if automatic execution is not disabled.

Given/when I send event {event_name} with {parameter}={value}
    Send an event to the statechart with given parameter. The value of the parameter is evaluated as Python code.
    The statechart is executed after this step.
    Additional parameters can be specified using a table, as follows.

    .. literalinclude:: examples/elevator.feature
      :language: gherkin
      :lines: 11-16
      :emphasize-lines: 3-5

Given/when I wait {seconds} seconds
    Increment the internal clock of the statechart, and perform a single execution of the statechart.
    As the execution uses a simulated clock, if your statechart relies on relative time delta,
    you should consider using the *repeated* version of this step.

Given/when I wait {seconds} seconds {repeat} times
    Repeatedly increment the internal clock of the statechart, and execute the statechart after each increment.

    .. literalinclude:: examples/microwave.feature
      :language: gherkin
      :lines: 14-18
      :emphasize-lines: 3

Given I set variable {variable} to {value}
    Set the value of a variable in the internal context of a statechart.
    Value is evaluated as Python code.


"Then" steps
------------

Then state {state} should be active
    Assert that given state name is active.

Then state {state} should not be active
    Assert that given state name is not active.

Then event {event_name} should be fired
    Assert that given event name is the latest fired event.

    .. literalinclude:: examples/microwave.feature
      :language: gherkin
      :lines: 27-30
      :emphasize-lines: 3

Then event {event_name} should be fired with {parameter}={value}
    Assert that given event name was fired during the last execution, and that it has an attribute *parameter*
    with given *value*, evaluated as Python code.
    Additional parameters can be specified using a table.

Then no event should be fired
    Assert that no event was fired by the statechart during the last execution.

Then variable {variable} should be defined
    Assert that given *variable* is defined in the context of the statechart.

Then the value of variable {variable} should be {value}
    Assert that given *variable* is defined and has given *value* in the context of the statechart.
    The value is evaluated as Python code.

Then expression {expression} should hold
    Assert that the truth value of given *expression* is true.
    The expression is evaluated as Python code inside the context of the statechart.

Then the statechart is in a final configuration
    Assert that the statechart is in a final configuration.


.. warning:: The documented list of steps, herebaove, could be incomplete or could contain slight variations.
    You can easily get an up-to-date list of all the available steps using the ``--steps`` arguments,
    as in ``sismic-behave elevator.yaml --features elevator.feature --steps``.
