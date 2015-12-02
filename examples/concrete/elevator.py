import pyss
import yaml

# Construct the statechart
sc = pyss.import_from_yaml(open('elevator.yaml'))

sc.validate()  # Raise an exception if our state machine is not a valid one

# Use a Python evaluator for the code in the state machine
evaluator = pyss.PythonEvaluator()

# Create a simulation for our state machine, with our evaluator
simulator = pyss.Simulator(sc, evaluator)

# Make the simulator runnable
print('- Start simulator, stabilization steps:')
for step in simulator.start():
    print(step)

print()
print('Initial configuration = {}'.format(simulator.configuration))

# Create a new event with some data
event = pyss.Event('floorSelected', {'floor': 4})

# Send this event to the simulator
simulator.send(event)
print('- {} sent'.format(event))

for step in simulator:
    print(step)
    print('-> {}'.format(simulator.configuration))
    print()



