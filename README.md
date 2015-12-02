# Statechart Simulator for Python

(Currently under development)

## Overview

`pyss` provides a set of tools related to statechart manipulation and execution.
In particular, `pyss` provides:
 - A Python data structure to store and manipulate statecharts
 - A easy way to define statecharts using YAML
 - Statecharts simulators (SCXML semantic, no language restriction!)
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

To be done...

