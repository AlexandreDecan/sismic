# Statechart Simulator for Python [![Build Status](https://travis-ci.org/AlexandreDecan/PySS.svg)](https://travis-ci.org/AlexandreDecan/PySS) [![Coverage Status](https://coveralls.io/repos/AlexandreDecan/PySS/badge.svg?branch=master&service=github)](https://coveralls.io/github/AlexandreDecan/PySS?branch=master)

(Currently under development)

## Overview

`pyss` provides a set of tools related to statechart manipulation and execution.
In particular, `pyss` provides:
 - An easy way to define statecharts with YAML
 - Discrete, step-by-step, fully observable statechart simulation following SCXML semantic
 - Built-in support for Python code, can be easily extended to other languages
 - A base framework for model-based testing

`pyss` has a complete support for simple state, composite state, orthogonal (parallel) state,
initial state, final state, history state (including shallow and deep semantics), internal
transitions, guarded transition, eventless transition, statechart entry action,
state entry action, state exit action, transition action, internal and external events and
parametrized events.

We expect to support the following features soon:
 - Static visualization (export to GraphViz)
 - Runtime dynamic visualization and manipulation


Example of a YAML definition of a state chart for an elevator:
```yaml
statechart:
  name: Elevator
  initial: active
  on entry: |
    current = 0
    destination = 0
    openDoors = lambda: print('open doors')
    closeDoors = lambda: print('close doors')
  states:
    - name: active
      parallel states:
        - name: movingElevator
          initial: doorsOpen
          on entry: current = 0
          states:
            - name: doorsOpen
              transitions:
                - target: doorsClosed
                  guard: destination != current
                  action: closeDoors()
                - target: doorsClosed
                  event: after10s
                  guard: current > 0
                  action: destination = 0
            - name: doorsClosed
              transitions:
                - target: movingUp
                  guard: destination > current
                - target: movingDown
                  guard: destination < current and destination >= 0
            - name: moving
              transitions:
                - target: doorsOpen
                  guard: destination == current
                  action: openDoors()
              states:
                - name: movingUp
                  on entry: current = current + 1
                  transitions:
                    - target: movingUp
                      guard: destination > current
                - name: movingDown
                  on entry: current = current - 1
                  transitions:
                    - target: movingDown
                      guard: destination < current
        - name: floorListener
          initial: floorSelecting
          on entry: destination = 0
          states:
            - name: floorSelecting
              transitions:
                - target: floorSelecting
                  event: floorSelected
                  action: destination = event.data['floor']
```

More examples are available in `examples/*.yaml`.


## Installation

We do not provide any package yet, but you can test `pyss` by cloning this repository.
The list of dependencies is given by `requirements.txt` and can be automatically satisfied by using `pip install -r requirements.txt`.
Python >=3.4 is required, so we suggest you to test this package in a virtual environment.

 - `pyss` is the main module, it contains the data structure,
 YAML loader (`pyss.io`), code evaluators (`pyss.evaluator`) and statechart simulator (`pyss.simulator`).
 - `tests` contains, uh, well, the tests!
 - `examples` currently contains several statecharts in YAML.


PySS is expected to be imported as a Python module, but it also provides a command-line
interface, available in `execute.py`.

```
(shell) python execute.py -h
usage: execute.py [-h] [--evaluator {python,dummy}] [-v]
                  [--events [EVENTS [EVENTS ...]]]
                  infile

positional arguments:
  infile                A YAML file describing a statechart

optional arguments:
  -h, --help            show this help message and exit
  --evaluator {python,dummy}
                        Evaluator to use for code
  -v                    Level of details, -v shows configurations, -vv shows
                        events, -vvv shows transitions
  --events [EVENTS [EVENTS ...]]
                        A list of event names
```

An example of a call:
```
(shell) python execute.py examples/concrete/history.yaml --evaluator=dummy --events next pause continue next pause stop -v
Initial configuration: ['s1', 'loop']
-- Configuration: ['s2', 'loop']
-- Configuration: ['pause']
-- Configuration: ['s2', 'loop']
-- Configuration: ['s3', 'loop']
-- Configuration: ['pause']
-- Configuration: ['stop']
Final: True

```

## Credits and license

Under version 3 of the GNU General Public License.
Developed by Alexandre Decan at the University of Mons (Belgium).


## Documentation

The documentation is in a work-in-progress state.

### YAML format for a statechart

Statecharts can be defined using a YAML format.
The root of the YAML file should declare a statechart:
```yaml
statechart:
  name: Name of this statechart
  initial: name of the initial state
```

The `name` and the `initial` state are mandatory. 
You can declare code to execute on the initialization of the statechart using `on entry`, as follows:
```yaml
statechart:
  name: with code
  initial: s1
  on entry: x = 1
```

Code can be written on multiple lines: 
```yaml
on entry: |
  x = 1
  y = 2
```

A statechart has to declare a (nonempty) list of states using `states`.
Each state consist of at least a `name`. Depending on the state type, several fields can be declared.

```yaml
statemachine:
  name: with state
  initial: s1
  states:
    - name: s1
```

For each state, it is possible to specify the code that has to be executed when entering and leaving the
state using `on entry` and `on exit` as follows:
```yaml
- name: s1
  on entry: x += 1
  on exit: |
    x -= 1
    y = 2
```

Final state simply declares a `type: final` property. 
History state simply declares a `type: history` property. Default semantic is shallow history. 
For a deep history semantic, add a `deep: True` property. Exemple:
```yaml
- name: s1
- name: history state
  type: history
  deep: True
- name: s2
  type: final
```

An history state can optionally define an initial state using `initial`, for e.g.:
```yaml
- name: history state
  type: history
  initial: s1
```
The `initial` value (for history state or, later, for compound state) should refer to a parent's
substate and will be used the first time the history state is reached if it has not yet a memorized configuration.

Except final states and history states, states can contain nested states.
Such a state is a compound state or a region, we do not make any difference between those two concepts.
```yaml
- name: compound state
  states: 
    - name: nested state 1
    - name: nested state 2
      states: 
        - name: nested state 2a
```

Orthogonal states (sometimes referred as parallel states) must be with `parallel states` instead of `states`.
For example, the following statechart declares two concurrent processes:
```yaml
statechart:
  name: Concurrent processes state machine
  initial: processes
  states: 
    - name: processes
      parallel states:
        - name: process 1
        - name: process 2
```
 
A compound orthogonal state can not be declared at top level, and should be nested in a compound state, as
illustrated in the previous example. In other words, it is not allowed to define `parallel states`
instead of `states` in this previous example.
 
Simple states, compound states and parallel states can declare transitions using `transitions`:
```yaml
- name: state with transitions
  transitions: 
    - target: other state
```

A transition can define a `target` (name of the target state), a `guard` (a Boolean expression
that will be evaluated), an `event` (name of the event) and an `action` (code that will be executed if the
transition is processed). All those fields are optional. A full example of a transition:
```yaml
- name: state with a transition
  transitions: 
    - target: other state
      event: click
      guard: x > 1
      action: print('Hello World!')
```
An internal transition is a transition that does not declare a `target`, implicitly meaning that its `target` is
the state in which the transition is defined. When such a transition is processed, the parent state is not exited nor
entered.

Finally, to prevent trivial infinite loops on execution, an internal transition must either define an event or a guard.

### Load a YAML file

A YAML definition of a statechart can be easily imported to a `StateChart` instance.
The module `pyss.io` provides a convenient loader `import_from_yaml(data)` which takes a textual YAML definition
of a statechart.

Although the parser is quite robut and should warn about most syntaxic problems, a `StateChart` instance has a
`validate()` method performs numerous other checks. This method either return `True` if the statechart *seems* to
be valid, or raise a `ValueError` exception with a meaningful message.



### Code evaluation

A statechart can write code to be executed under some circumstances.
For example, the `on entry` property on a `statechart`, `guard` or `action` on a transition or the
`on entry` and `on exit` property for a state.

In `pyss`, these pieces of code can be evaluated and executed by `Evaluator` instances.
An `Evaluator` must provide two methods:
 - A `evaluate_condition(condition, event)` method that takes a condition (a one-line string containing some code)
 and an `Event` instance (which is essentially a `name` and a dictionary `data`). This methods should return either `True` or `False`.
 - A `execute_action(action, event)` method that takes an action (a string containing some code) and an `Event`
 instance. This method should return a list of `Event` instances that will be treated as internal events
 (and thus that have priority).

By default, `pyss` provides two built-in `Evaluator` subclasses:
 - A `DummyEvaluator` that always evaluate a guard to `True` and silently ignores `action`, `on entry` and `on exit`.
 - A `PythonEvaluator` that brings Python into our statecharts.

An instance of `PythonEvaluator` can evaluate and execute Python code expressed in the statechart.
Such an instance relies on the concept of `context`, which is a dictionary-like structure that contains the data
that are exposed to the pieces of code of the statechart (ie. override `__locals__`).

As an example, consider the following partial statechart definition.
```yaml
statechar:
  # ...
  on entry: x = 1
  states:
    - name: s1
      on entry: x += 1
```
When the statechart is initialized, the `context` of a `PythonEvaluator` will contain `{'x': 1}`.
When *s1* is entered, the code will be evaluated with this context.
After the execution of `x += 1`, the context will contain `{'x': 1}`.

When a `PythonEvaluator` instance is initialized, a prepopulated context can be specified:
```python
import math as my_favorite_module
# ...
evaluator = PythonEvaluator({'x': 1, 'math': my_favorite_module})
```

By default, the context will expose an `Event` class (from `model.Event`) and a `send` function, that can be used
to send internal event to the simulator (eg.: `on entry: send(Event('Hello World!'))`).

Additionally, the `__builtins__` of Python are also exposed, implying that you can use nearly everything provided
by the standard library of Python.


### Statechart execution

The module `simulator` contains a `Simulator` class that interprets a statechart following SCXML semantic.
A `Simulator` instance is constructed upon a `StateChart` instance and an optional `Evaluator`.
If no `Evaluator` instance is specified, a `DummyEvaluator` instance will be used by default.

The main methods of a simulator instance are:
 - `send(event)` takes an `Event` instance that will be added to a FIFO queue of external events.
 - `start()` initializes the simulator to a stable situation (ie. processes initial steps). Return a list of `MicroStep` instances (see below). 
 - `execute()` processes a transition based on the oldest queued event (or no event if an eventless transition can be processed), and stabilizes
  the simulator in a stable situation (ie. processes initial states, history states, etc.). This method returns an instance of `MacroStep` (see
  below) or `None` if (1) no eventless transition can be processed, (2) there is no event in the event queue.
  This method returns an instance of `MacroStep` or `None` if nothing was done.
 - Property `configuration`: contains an (unordered) list of active states. 
 - Property `running`: return `True` if and only if the statechart is running AND is not in a final configuration.
 
Example:
```python
simulator = Simulator(my_statechart)
simulator.start()
# We are now in a stable initial state
simulator.send(Event('click'))  # Send event to the simulator
simulator.execute()  # Will process the event if no eventless transitions are found at first
```

For convenience, `send` returns `self` and thus can be chained:
```python
simulator.send(Event('click')).send(Event('click')).execute()
```

Notice that `execute()` consumes at most one event at a time.
In this example, the second *click* event is not processed.

To process all events *at once*, repeatedly call `execute()` until it returns a `None` value.
For instance:
```python
while simulator.execute():
  pass
```

As a shortcut, a `Simulator` instance provides an iterator:
```python
for step in simulator: 
  assert isinstance(step, MacroStep)
assert simulator.execute() == None
```

The simulator is fully observable: its `execute()` method returns an instance of `MacroStep`.
A macro step corresponds to the process of either an eventless transition, or an evented transition,
or no transition (but consume the event), including the stabilization steps (ie. the steps that are needed
to enter nested states, or to switch into the configuration of an history state).

A `MacroStep` exposes an `Event` (`None` in case of eventless transition), a `Transition` (`None` if the
event was consumed without triggering a transition) and two sequences of state names: `entered_states` and
`exited_states`. States order in those list indicates the order in which their `on entry` and `on exit` actions
were processed.

The main step and the stabilization steps of a macro step are exposed through `main_step` and `micro_steps`.
The first is a `MicroStep` instance, and the second is an ordered list of `MicroStep` instances.
A micro step is the smallest, atomic step that a statechart can execute.
A `MacroStep` instance can be viewed (and is!) an aggregate of `MicroStep` instances.

This way, a complete run of a state machine can be summarized as an ordered list of `MacroStep` instances,
and details of such a run can be obtained using the `MicroStep`'s of a `MacroStep`.
