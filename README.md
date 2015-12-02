# Statechart Simulator for Python

(Currently under development)

## Overview

`pyss` provides a set of tools related to statechart manipulation and execution.
In particular, `pyss` provides:
 - An easy way to define statecharts using YAML
 - Discrete, step-by-step, statechart simulation following SCXML semantic
 - Built-in support for Python code, can be easily extended to other languages
 - A base framework for model-based testing

Example of a YAML definition of a state chart for an elevator:
```
statemachine:
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

`pyss` supports:
 - simple (basic) state, composite state, orthogonal state
 - initial state, final state, history state (incl. shallow and deep semantic)
 - guarded transition, eventless transition, internal transition
 - entry action, exit action, transition action
 - fully observable step-by-step execution (based on SCXML semantic)
 - (Not yet) static visualization
 - (Not yet) dynamic visualization during execution

More examples are available in `examples/*.yaml`.


## Installation

We do not provide any package yet, but you can test `pyss` by cloning this repository.
The list of dependencies is given by `requirements.txt` and can be automatically satisfied by using `pip install -r requirements.txt`.
Python >=3.4 is required, so we suggest you to test this package in a virtual environment.

 - `pyss` is the main module, it contains the data structure,
 YAML loader (`pyss.io`), code evaluators (`pyss.evaluator`) and statechart simulators (`pyss.simulator`).
 - `tests` contains, uh, well, the tests!
 - `examples` currently contains several statecharts in YAML.


## Credits and license

Under version 3 of the GNU General Public License.
Developed by Alexandre Decan at the University of Mons (Belgium).

## Documentation

In progress.

### YAML format for a statemachine

Statemachines can be defined using a YAML format. 
The root of the YAML file should declare a statemachine:
```
statemachine:
  name: Name of this state machine
  initial: name of the initial state
```

The `name` and the `initial` state are mandatory. 
You can declare code to execute on the initialization of the statemachine using `on entry`, as follows:
```
statemachine:
  name: with code
  initial: s1
  on entry: x = 1
```

Code can be written on multiple lines: 
```
on entry: |
  x = 1
  y = 2
```

A statemachine has to declare a (nonempty) list of states using `states`. 
Each state consist of at least a `name`. Depending on the state type, several fields can be declared.

```
statemachine:
  name: with state
  initial: s1
  states:
    - name: s1
```

For each state, it is possible to specify the code that has to be executed when entering and leaving the state using `on entry` and `on exit` as follows:
```
- name: s1
  on entry: x += 1
  on exit: |
    x -= 1
    y = 2
```

Final state simply declares a `type: final` property. 
History state simply declares a `type: history` property. Default semantic is shallow history. 
For a deep history semantic, add a `deep: True` property. Exemple:
```
- name: s1
- name: history state
  type: history
  deep: True
- name: s2
  type: final
```

An history state can stipulate its initial memory using `initial`, for e.g.:
```
- name: history state
  type: history
  initial: s1
```

The `initial` value (for history state or, later, for compound state) should refer to a parent's substate. 

Except final states and history states, states can contain nested states. Such a state is a compound state or a region, we do not make any difference between those two concepts. 
```
- name: compound state
  states: 
    - name: nested state 1
    - name: nested state 2
      states: 
        - name: nested state 2a
```

Orthogonal (or parallel) states can be declared using `parallel states` instead of `states`. 
For example, the following state machine declares two concurrent processes:
```
statemachine:
  name: Concurrent processes state machine
  initial: processes
  states: 
    - name: processes
      parallel states:
        - name: process 1
        - name: process 2
```
 
A compound orthogonal state can not be declared at top level, and should be nested in a compound state, as illustrated in the previous example (in other words, one cannot use `parallel states` instead of `states` in this previous example). 
 
Except final states and history states, states can declare transitions using `transitions`:
```
- name: state with transitions
  transitions: 
    - target: other state
```

A transition can define a `target` (name of the target state), a `guard` (a one-line Boolean expression that will be evaluated), an `event` (name of the event) and an `action` (code that will be executed if the transition is performed). A full example of a transition: 
```
- name: state with a transition
  transitions: 
    - target: other state
      event: click
      guard: x > 1
      action: print('Hello World!')
```

Each field is optional. A transition with no event has priority. If a transition does not declare a `target`, it is an internal transition. A transition can not be internal AND eventless AND guardless (or this eventually lead to an infinite execution). 

### Load a YAML file

Statemachines (in YAML format) can be easily imported in Python. 
The module `io` provides a convinient function `import_from_yaml(content)` which takes a string as input, and return a `StateMachine` instance (see `statemachine` module). 

The parser is quite robust, and should warn you for most syntaxic problem. 
A `StateMachine` instance has a `validate()` method that returns `True` if the statemachine *seems* to be valid, or raise an (detailed) exception instead. You should always consider using this method before doing anything else!

### Code evaluation

Statemachine can declare code to be executed under some circumstances (on entry, on exit, when a transition is processed, to evaluate a guard, etc.). The code can be evaluated using an `Evaluator`. By default, `pyss` provides two built-in `Evaluator` subclasses: 
 - A `DummyEvaluator` that does nothing, but always evaluate a condition to `True`. 
 - A `PythonEvaluator` that understands Python.

An `Evaluator` must provide two methods: 
 - A `evaluate_condition(condition, event)` method that takes a condition (a one-line string containing some code) and an `Event` instance (which is essentially a `name` and a dictionary `data`). This methds should return either `True` or `False`.
 - A `execute_action(action, event)` method that takes an action (a string containing some code) and an `Event` instance. This method should return a list of `Event` instances that will be treated as internal events (and thus that have priority). 
 
The `PythonEvaluator` stores a `context`, which is a dictionary-like structure that contains the data available when evaluating or executing code. The context is always exposed as `__locals__` to the code that is executed. 
For example, consider the following state machine.
```
statemachine: 
  # ...
  on entry: x = 1
  states:
    - name: s1
      on entry: x += 1
```

When the state machine is initialized, the `context` of a `PythonEvaluator` will contain `{'x': 1}`. 
When *s1* is entered, the code will be evaluated with this context. After the execution of `x += 1`, the context will contain `{'x': 1}`. 

Importantly, the context is prepopulated with `__builtins__` as in a standard Python scope, meaning that you can use nearly anything you want in your code (in fact, this part of the evaluator relies on `eval` and `exec`). 
A `send` function is also exposed in the context. This function takes an `Event` instance (also exposed) and generates an internal event in the simulation. 

Moreover, an initial context can be provided, eg. `PythonEvaluator({'x': 42, 'my_favorite_module': my_favorite_module})`.

### Statemachine execution

The module `simulator` contains a `Simulator` class that interprets a statemachine following SCXML semantic. 
A `Simulator` instance is constructed upon a `StateMachine` instance and optionally an `Evaluator` (if not specified, a `DummyEvaluator` instance will be used). 

The simulator exposes the following methods: 
 - `send(event)` takes an `Event` instance that will be added to a FIFO queue of external events. This method returns `self` and can thus be chained: `simulator.send(Event('click')).send(Event('another click'))`. 
 - `start()` initializes the simulator to a stable situation (ie. processes initial steps). Return a list of `MicroStep` instances (see below). 
 - `execute()` computes and executes the next step (eventless transition, evented transition or nothing; followed by some stabilization steps like processing history and initial states). This method returns an instance of `MacroStep` or `None` if nothing was done.
 - Property `configuration`: contains an (unordered) list of active states. 
 - Property `running`: return `True` if and only if the state machine is running AND is not in a final configuration.
 
Example:
```
simulator = Simulator(my_statemachine)
simulator.start()
# We are now in a stable initial state
simulator.send(Event('click'))  # Send event to the simulator
simulator.execute()  # Will process the event if no eventless transitions are found at first
```

For convenience, `send` can be chained: 
```
simulator.send(Event('click')).send(Event('click')).execute()
```
Notice that `execute()` will at most process one of the two events! To process all the event, call repeatedly `execute()` until it returns a `None` value: 
```
while simulator.execute():
  pass
```

For convenience, a `Simulator` instance exposes an iterator: 
```
for step in simulator: 
  assert isinstance(step, MacroStep)
```

The `execute()` method returns an instance of `MacroStep`. Such an instance corresponds to the process of a `Transition` instance (see `statemachine` module), for given `Event` instance (or `None` if transition is eventless) and leads to an ordered list of `exited_states` and `entered_states`. The order in those lists corresponds to the order in which the `on exit` and `on entry` codes were executed. 

In fact, a macro step is an aggregation of `MicroSteps` instances, with a main step (the one that possibly consumes an event and performs a transition) and a (possibly empty) list of other micro steps (stabilization steps that could add states to the list of `exited_states` and `entered_states`). 

This way, a complete run of a state machine can be summarized as an ordered list of `MacroStep` instances. 
