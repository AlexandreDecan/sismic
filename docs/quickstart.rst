Quickstart
==========



Installation
------------

Sismic can be installed using ``pip`` as usual: ``pip install sismic``.
This will install the latest stable version.

You can also install Sismic from its repository by cloning it.
The development occurs in the *master* branch, the latest stable distributed version is in the *stable* branch.

Sismic requires Python >=3.4 but should also work with Python 3.3.
You can isolate Sismic installation by using virtual environments:

1. Get the tool to create environment: ``pip install virtualenv``
2. Create the environment: ``virtualenv -p python3.4 env``
3. Jump into: ``source env/bin/activate``
4. Install dependencies: ``pip install -r requirements.txt``
5. Test PySS: ``python -m unittest discover``


Statechart in YAML
------------------

Example of a YAML definition of a statechart for an elevator.
This statechart includes contract definition.


.. literalinclude:: ../examples/elevator_contract.yaml
    :language: yaml


More examples are available in the *examples* directory.

Statechart execution
--------------------

Quick example:

.. testcode::

   import sismic

   with open('../examples/elevator.yaml') as f:
      statechart = sismic.io.import_from_yaml(f)
      interpreter = sismic.interpreter.Interpreter(statechart)
      interpreter.send(sismic.model.Event('floorSelected', data={'floor': 4}))
      for step in interpreter.execute():
         print('{}: {}'.format(step.transitions, interpreter.configuration))

.. testoutput::
   :options: -ELLIPSIS

   [Transition(floorSelecting, floorSelecting, Event(floorSelected))]: ['active', 'floorListener', 'movingElevator', 'doorsOpen', 'floorSelecting']
   [Transition(doorsOpen, doorsClosed, None)]: ['active', 'floorListener', 'movingElevator', 'doorsOpen', 'floorSelecting']
   [Transition(doorsClosed, movingUp, None)]: ['active', 'floorListener', 'movingElevator', 'doorsOpen', 'floorSelecting']
   [Transition(movingUp, movingUp, None)]: ['active', 'floorListener', 'movingElevator', 'doorsOpen', 'floorSelecting']
   [Transition(movingUp, movingUp, None)]: ['active', 'floorListener', 'movingElevator', 'doorsOpen', 'floorSelecting']
   [Transition(movingUp, movingUp, None)]: ['active', 'floorListener', 'movingElevator', 'doorsOpen', 'floorSelecting']
   [Transition(moving, doorsOpen, None)]: ['active', 'floorListener', 'movingElevator', 'doorsOpen', 'floorSelecting']


