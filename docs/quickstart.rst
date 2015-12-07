Quickstart
==========



Installation
------------

PySS can be installed using ``pip`` as usual: ``pip install pyss``.
This will install the latest stable version.

You can also install PySS from this repository by cloning it.
The development occurs in the *master* branch, the latest stable distributed version is in the *stable* branch.

PySS requires Python >=3.4 but should also work with Python 3.3.
You can isolate PySS installation by using virtual environments:

1. Get the tool to create environment: ``pip install virtualenv``
2. Create the environment: ``virtualenv -p python3.4 env``
3. Jump into: ``source env/bin/activate``
4. Install dependencies: ``pip install -r requirements.txt``
5. Test PySS: ``python -m unittest discover``


Example
-------

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


More examples are available in the *examples* directory.

Execution
---------

You can execute this example using the command-line interface or programmatically
or using the command-line interface, see :ref:`cli_execute`.

.. code:: python

    import pyss

    statechart = pyss.io.import_from_yaml(open('examples/concrete/elevator.yaml'))
    evaluator = pyss.evaluator.PythonEvaluator()
    simulator = pyss.simulator.Simulator(statechart, evaluator)

    simulator.send(pyss.model.Event('floorSelected', data={'floor': 4}))
    for step in simulator:
        print('{}: {}'.format(step.transition, simulator.configuration))

The output should be::

    doorsOpen -> doorsClosed: ['active', 'movingElevator', 'floorListener', 'floorSelecting', 'doorsClosed']
    doorsClosed -> movingUp: ['active', 'floorListener', 'movingElevator', 'floorSelecting', 'moving', 'movingUp']
    movingUp -> movingUp: ['active', 'floorListener', 'movingElevator', 'floorSelecting', 'moving', 'movingUp']
    movingUp -> movingUp: ['active', 'floorListener', 'movingElevator', 'floorSelecting', 'moving', 'movingUp']
    movingUp -> movingUp: ['active', 'floorListener', 'movingElevator', 'floorSelecting', 'moving', 'movingUp']
    moving -> doorsOpen: ['active', 'floorListener', 'movingElevator', 'floorSelecting', 'doorsOpen']

