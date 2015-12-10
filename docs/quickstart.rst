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


Statechart in YAML
------------------

Example of a YAML definition of a statechart for an elevator:

.. literalinclude:: ../examples/concrete/elevator.yaml
   :language: yaml


More examples are available in the *examples* directory.

Statechart execution
--------------------

You can execute this example using the command-line interface or programmatically
or using the command-line interface, see :ref:`cli_execute`.

.. code:: python

    import pyss

    statechart = pyss.io.import_from_yaml(open('examples/concrete/elevator.yaml'))
    simulator = pyss.simulator.Simulator(statechart)
    simulator.send(pyss.model.Event('floorSelected', data={'floor': 4}))
    for step in simulator.execute():
        print('{}: {}'.format(step.transition, simulator.configuration))

The output should be::

   floorSelecting+floorSelected -> floorSelecting: ['active', 'movingElevator', 'floorListener', 'doorsOpen', 'floorSelecting']
   doorsOpen -> doorsClosed: ['active', 'movingElevator', 'floorListener', 'doorsOpen', 'floorSelecting']
   doorsClosed -> movingUp: ['active', 'movingElevator', 'floorListener', 'doorsOpen', 'floorSelecting']
   movingUp -> movingUp: ['active', 'movingElevator', 'floorListener', 'doorsOpen', 'floorSelecting']
   movingUp -> movingUp: ['active', 'movingElevator', 'floorListener', 'doorsOpen', 'floorSelecting']
   movingUp -> movingUp: ['active', 'movingElevator', 'floorListener', 'doorsOpen', 'floorSelecting']
   moving -> doorsOpen: ['active', 'movingElevator', 'floorListener', 'doorsOpen', 'floorSelecting']

