import unittest
from sismic import io
from sismic.interpreter import Interpreter
from sismic.model import Event, Transition, StateMixin
from sismic.exceptions import PreconditionError, PostconditionError, InvariantError


class ElevatorContractTests(unittest.TestCase):
    def setUp(self):
        with open('docs/examples/elevator/elevator.yaml') as f:
            self.sc = io.import_from_yaml(f)
        self.interpreter = Interpreter(self.sc)

    def test_no_error(self):
        self.interpreter.queue(Event('floorSelected', floor=4))
        self.interpreter.execute()
        self.assertFalse(self.interpreter.final)

    def test_state_precondition(self):
        self.sc.state_for('movingUp').preconditions.append('False')
        self.interpreter.queue(Event('floorSelected', floor=4))
        with self.assertRaises(PreconditionError) as cm:
            self.interpreter.execute()
        self.assertTrue(isinstance(cm.exception.obj, StateMixin))

    def test_state_postcondition(self):
        self.sc.state_for('movingUp').postconditions.append('False')
        self.interpreter.queue(Event('floorSelected', floor=4))
        with self.assertRaises(PostconditionError) as cm:
            self.interpreter.execute()
        self.assertTrue(isinstance(cm.exception.obj, StateMixin))

    def test_state_invariant(self):
        self.sc.state_for('movingUp').invariants.append('False')
        self.interpreter.queue(Event('floorSelected', floor=4))
        with self.assertRaises(InvariantError) as cm:
            self.interpreter.execute()
        self.assertTrue(isinstance(cm.exception.obj, StateMixin))

    def test_transition_precondition(self):
        transitions = self.sc.transitions_from('floorSelecting')
        transitions[0].preconditions.append('False')
        self.interpreter.queue(Event('floorSelected', floor=4))
        with self.assertRaises(PreconditionError) as cm:
            self.interpreter.execute()
        self.assertTrue(isinstance(cm.exception.obj, Transition))

    def test_transition_postcondition(self):
        transitions = self.sc.transitions_from('floorSelecting')
        transitions[0].postconditions.append('False')
        self.interpreter.queue(Event('floorSelected', floor=4))
        with self.assertRaises(PostconditionError) as cm:
            self.interpreter.execute()
        self.assertTrue(isinstance(cm.exception.obj, Transition))

    def test_do_not_raise(self):
        self.interpreter = Interpreter(self.sc, ignore_contract=True)
        transitions = self.sc.transitions_from('floorSelecting')
        transitions[0].postconditions.append('False')
        self.interpreter.queue(Event('floorSelected', floor=4))
        self.interpreter.execute()

