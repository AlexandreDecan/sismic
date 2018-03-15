from sismic.bdd.cli import execute_behave


def test_elevator():
    d = lambda f: 'docs/examples/elevator/' + f

    assert 0 == execute_behave(
        statechart=d('elevator_contract.yaml'),
        features=[d('elevator.feature')],
        steps=[],
        properties=[],
        debug_on_error=False,
        parameters= []
    )


def test_microwave():
    d = lambda f: 'docs/examples/microwave/' + f

    assert 0 == execute_behave(
        statechart=d('microwave.yaml'),
        features=[d('heating.feature')],
        steps=[],
        properties=[],
        debug_on_error=False,
        parameters=[]
    )


def test_microwave_with_properties():
    d = lambda f: 'docs/examples/microwave/' + f

    assert 0 == execute_behave(
        statechart=d('microwave.yaml'),
        features=[d('heating.feature')],
        steps=[],
        properties=[d('heating_off_property.yaml'), d('heating_on_property.yaml'), d('heating_property.yaml')],
        debug_on_error=False,
        parameters=[]
    )


def test_microwave_with_steps():
    d = lambda f: 'docs/examples/microwave/' + f

    assert 0 == execute_behave(
        statechart=d('microwave.yaml'),
        features=[d('heating_human.feature')],
        steps=[d('heating_steps.py')],
        properties=[],
        debug_on_error=False,
        parameters=[]
    )


def test_microwave_with_steps_and_properties():
    d = lambda f: 'docs/examples/microwave/' + f

    assert 0 == execute_behave(
        statechart=d('microwave.yaml'),
        features=[d('heating_human.feature')],
        steps=[d('heating_steps.py')],
        properties=[d('heating_off_property.yaml'), d('heating_on_property.yaml'), d('heating_property.yaml')],
        debug_on_error=False,
        parameters=[]
    )

