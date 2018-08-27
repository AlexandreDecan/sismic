import pytest

from sismic.exceptions import (InvariantError, PostconditionError,
                               PreconditionError)
from sismic.interpreter import Interpreter, Event
from sismic.model import StateMixin, Transition


def test_no_error(elevator):
    elevator.queue('floorSelected', floor=4)
    elevator.execute()

    assert not elevator.final


def test_state_precondition(elevator):
    elevator.statechart.state_for('movingUp').preconditions.append('False')
    elevator.queue('floorSelected', floor=4)

    with pytest.raises(PreconditionError) as e:
        elevator.execute()

    assert isinstance(e.value.obj, StateMixin)


def test_state_postcondition(elevator):
    elevator.statechart.state_for('movingUp').postconditions.append('False')
    elevator.queue('floorSelected', floor=4)

    with pytest.raises(PostconditionError) as e:
        elevator.execute()

    assert isinstance(e.value.obj, StateMixin)


def test_state_invariant(elevator):
    elevator.statechart.state_for('movingUp').invariants.append('False')
    elevator.queue('floorSelected', floor=4)

    with pytest.raises(InvariantError) as e:
        elevator.execute()

    assert isinstance(e.value.obj, StateMixin)


def test_transition_precondition(elevator):
    transitions = elevator.statechart.transitions_from('floorSelecting')
    transitions[0].preconditions.append('False')
    elevator.queue('floorSelected', floor=4)

    with pytest.raises(PreconditionError) as e:
        elevator.execute()

    assert isinstance(e.value.obj, Transition)


def test_transition_postcondition(elevator):
    transitions = elevator.statechart.transitions_from('floorSelecting')
    transitions[0].postconditions.append('False')
    elevator.queue('floorSelected', floor=4)

    with pytest.raises(PostconditionError) as e:
        elevator.execute()

    assert isinstance(e.value.obj, Transition)


def test_do_not_raise(elevator):
    elevator = Interpreter(elevator.statechart, ignore_contract=True)
    transitions = elevator.statechart.transitions_from('floorSelecting')
    transitions[0].postconditions.append('False')

    elevator.queue('floorSelected', floor=4).execute()
