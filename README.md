# Statechart Simulator for Python

(Currently under development)

## Overview

`pyss` provides a set of tools related to statechart manipulation and execution.
In particular, `pyss` provides:
 - A Python data structure to store and manipulate statecharts
 - A easy way to define statecharts using YAML
 - Statecharts simulators (SCXML semantic, no language restriction!)
 - A base framework for model-based testing

Example of a YAML definition of a simple state chart:
```
statemachine:
  name: Simple state machine
  initial: s1
  execute: x = 1

  states:
    - name: s1
      transitions:
        - target: s2
          event: click
          action: x = x + 1
        - event: key_pressed  # Internal transition
          condition: event.data['key'] > 42 
    - name: s2
      transitions: 
        - target: s3  # Eventless transition
    - name: s3
      transitions:
        - target: s1
          event: key_pressed
          action: x = x - 1
        - target: s2
          event: click
          
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
 YAML loader (`pyss.load`), code evaluators (`pyss.evaluator`) and statechart simulators (`pyss.simulator`).
 - `tests` contains, uh, well, the tests!
 - `examples` currently contains several statecharts in YAML.


## Credits & license

Under version 3 of the GNU General Public License.
Developed by Alexandre Decan at the University of Mons (Belgium).
