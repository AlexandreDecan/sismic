# Python Statechart Simulator [![Build Status](https://travis-ci.org/AlexandreDecan/PySS.svg)](https://travis-ci.org/AlexandreDecan/PySS) [![Coverage Status](https://coveralls.io/repos/AlexandreDecan/PySS/badge.svg?branch=master&service=github)](https://coveralls.io/github/AlexandreDecan/PySS?branch=master)

Python Statechart Simulator for Python >=3.4

## Overview

PySS provides a set of tools related to statechart manipulation and execution.
In particular, PySS provides:
 - An easy way to define statecharts with YAML
 - Discrete, step-by-step, fully observable statechart simulation following SCXML semantic
 - Built-in support for Python code, can be easily extended to other languages
 - A base framework for model-based testing

PySS has a complete support for simple state, composite state, orthogonal (parallel) state,
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

PySS can be installed using `pip` as usual: `pip install pyss`.
This installs the latest stable version.

You can test the latest version by cloning this repository.
Python >=3.4 is required, so we suggest you to test this package in a virtual environment.
Dependencies can be satisfied using `pip install -r requirements.txt`

PySS is expected to be imported as a Python module, but it also provides a command-line
interface.
The CLI can be used by calling the `pyss` module (`python -m pyss`) or, if
PySS is installed on your system (e.g. using `pip`), by directly calling `pyss` in your shell
(`pyss -h`).

```
(shell) pyss -h
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
(shell) pyss examples/concrete/history.yaml --evaluator=dummy --events next pause continue next pause stop -v
Initial configuration: ['s1', 'loop']
-- Configuration: ['s2', 'loop']
-- Configuration: ['pause']
-- Configuration: ['s2', 'loop']
-- Configuration: ['s3', 'loop']
-- Configuration: ['pause']
-- Configuration: ['stop']
Final: True

```

## Documentation

The documentation is currently in a "work-in-progress" state.

  - [YAML format for a statechart](https://github.com/AlexandreDecan/PySS/tree/master/docs/format.md)
  : how can I build a statechart using your YAML format?
  - [Code evaluation and code evaluator](https://github.com/AlexandreDecan/PySS/tree/master/docs/evaluation.md)
  : how can I evaluate/execute the code that is written in my statechart?
  - [Executing statecharts](https://github.com/AlexandreDecan/PySS/tree/master/docs/exection.md)
  : how can I execute a statechart using PySS?


## Credits and license

Under version 3 of the GNU General Public License.
Developed by Alexandre Decan at the University of Mons (Belgium).

