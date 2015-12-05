Python Statechart Simulator
===========================

Python Statechart Simulator for Python >=3.4

.. image:: https://travis-ci.org/AlexandreDecan/PySS.svg
    :target: https://travis-ci.org/AlexandreDecan/PySS
.. image:: https://coveralls.io/repos/AlexandreDecan/PySS/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/AlexandreDecan/PySS?branch=master
.. image:: https://badge.fury.io/py/pyss.svg
    :target: https://pypi.python.org/pypi/PySS



Overview
--------

PySS provides a set of tools related to statechart manipulation and
execution. In particular, PySS provides:

- An easy way to define statecharts with YAML
- Discrete, step-by-step, fully observable statechart simulation following SCXML semantic
- Built-in support for Python code, can be easily extended to other languages
- A base framework for model-based testing

PySS has a complete support for simple state, composite state,
orthogonal (parallel) state, initial state, final state, history state
(including shallow and deep semantics), internal transitions, guarded
transition, eventless transition, statechart entry action, state entry
action, state exit action, transition action, internal and external
events and parametrized events.

We expect to support the following features soon: - Static visualization
(export to GraphViz) - Runtime dynamic visualization and manipulation

Example of a YAML definition of a state chart for an elevator:

.. code:: yaml

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


More examples are available in ``examples/*.yaml``.

Installation
------------

PySS can be installed using ``pip`` as usual: ``pip install pyss``. This
installs the latest stable version.

You can also install PySS from this repository.
Python >=3.4 is required, so we suggest you to test this package in a virtual environment:
1. Get the tool to create environment: `pip install virtualenv`
2. Create the environment: `virtualenv -p python3.3 env`
3. Jump into: `source env/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Test PySS: `python -m unittest discover`

You can find the latest distributed version in the `stable` branch.


Documentation
-------------

The documentation is currently in a "work-in-progress" state.

- `Create a statechart using YAML format <https://github.com/AlexandreDecan/PySS/tree/master/docs/format.md>`__
- `Use the command-line interface to execute statechart <https://github.com/AlexandreDecan/PySS/tree/master/docs/cli.md>`__
- `Use PySS as a module to execute statechart <https://github.com/AlexandreDecan/PySS/tree/master/docs/execution.md>`__
- `Evaluate and execute the code contained in statecharts <https://github.com/AlexandreDecan/PySS/tree/master/docs/evaluation.md>`__


Credits
-------

Developed by Alexandre Decan at the University of Mons (Belgium).

GNU Lesser General Public License, version 3.

