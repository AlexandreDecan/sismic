from sismic.interpreter import Event
from sismic import testing


def test_writer(writer):
    writer.queue(
        Event('keyPress', key='bonjour '),
        Event('toggle'),
        Event('keyPress', key='a '),
        Event('toggle'),
        Event('toggle_bold'),
        Event('keyPress', key='tous !'),
        Event('leave')
    )

    writer.execute()
    assert writer.final
    assert writer.context['output'] == ['bonjour ', '[b]', '[i]', 'a ', '[/b]', '[/i]', '[b]', 'tous !', '[/b]']


class TestElevator:
    def test_init(self, elevator):
        assert elevator.configuration == []

        # Stabilisation
        elevator.execute_once()

        assert set(elevator.configuration) == {'active', 'floorListener', 'floorSelecting',
                                               'movingElevator', 'doorsOpen'}

    def test_floor_selection(self, elevator):
        # Stabilisation
        elevator.execute_once()

        elevator.queue(Event('floorSelected', floor=4)).execute_once()
        assert elevator.context['destination'] == 4

        elevator.execute_once()
        assert set(elevator.configuration) == {'active', 'active', 'doorsClosed', 'floorListener', 'floorSelecting', 'movingElevator'}

    def test_floor_selected_and_reached(self, elevator):
        # Stabilisation
        elevator.execute_once()

        elevator.queue(Event('floorSelected', floor=4)).execute()
        assert elevator.context['current'] == 4

        elevator.clock.time += 10
        elevator.execute()

        assert 'doorsOpen' in elevator.configuration
        assert elevator.context['current'] == 0


class TestRemoteElevator:
    def test_button(self, elevator, remote_elevator):
        assert elevator.context['current'] == 0

        steps = remote_elevator.queue(Event('button_2_pushed')).execute()
        assert testing.event_is_fired(steps, 'floorSelected', {'floor': 2})

        elevator.execute()
        assert elevator.context['current'] == 2

    def test_button_0_on_groundfloor(self, elevator, remote_elevator):
        assert elevator.context['current'] == 0

        remote_elevator.queue(Event('button_0_pushed')).execute()
        elevator.execute()

        assert elevator.context['current'] == 0


class TestMicrowave:
    def test_lamp_on(self, microwave):
        microwave.execute_once()
        microwave.queue(Event('door_opened'))

        steps = microwave.execute_once()
        assert testing.event_is_fired(steps, 'lamp_switch_on')

    def test_heating_on(self, microwave):
        microwave.execute_once()
        microwave.queue(
            Event('door_opened'),
            Event('item_placed'),
            Event('door_closed'),
            Event('timer_inc')
        ).execute()

        microwave.queue(Event('cooking_start'))
        steps = microwave.execute()
        
        assert testing.event_is_fired(steps, 'heating_on')
        assert testing.event_is_fired(steps, 'lamp_switch_on')
        assert testing.event_is_fired(steps, 'turntable_start')