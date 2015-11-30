# Statechart Simulator for Python

## Overview

`pyss` provides a set of tools related to statechart manipulation and execution.
In particular, `pyss` provides:
 - A Python data structure to store and manipulate statecharts
 - A easy way to define statecharts using YAML (see `examples/*.yaml`)
 - Statecharts simulators (SCXML semantic, no language restriction!)
 - A base framework for model-based testing


## Features

`pyss` actually exhibits the following features:
 - simple (basic) state, composite state, orthogonal state
 - initial state, final state, history state (incl. shallow and deep semantic)
 - guarded transition, eventless transition, internal transition
 - entry action, exit action, transition action
 - (Not yet) fully observable step-by-step execution (based on SCXML semantic)
 - (Not yet) static visualization
 - (Not yet) dynamic visualization during execution


## Development

Pyss is currently under development.
Expected features for this package:
 - Distribution a full package on `PyPi` (install with `pip`)
 - Integration of a continuous integration process, with heavy test coverage
 - Well documented on *ReadTheDocs*, including a complete reference and many examples


## Content

 - `pyss` is the main module, it contains the data structure,
 YAML loader, code evaluators and statechart executors.
 - `tests` contains, uh, well, the tests!
 - `examples` currently contains several statecharts in YAML.


## Credits & license

Under version 3 of the GNU General Public License.

Developed by Alexandre Decan at the University of Mons (Belgium).