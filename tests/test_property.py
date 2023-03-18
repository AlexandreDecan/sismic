import pytest

from sismic.interpreter import Event, MetaEvent, InternalEvent
from sismic.exceptions import PropertyStatechartError


class TestInterpreterMetaEvents:
    @pytest.fixture
    def property_statechart(self, microwave, mocker):
        prop_sc = mocker.MagicMock(name='Interpreter', spec=microwave)
        prop_sc.queue = mocker.MagicMock(return_value=None)
        prop_sc.execute = mocker.MagicMock(return_value=None)
        prop_sc.final = False
        prop_sc.time = 0
        
        def prop_sc_call(statechart, clock):    
            return prop_sc

        # Bind it
        microwave.bind_property_statechart(None, interpreter_klass=prop_sc_call)

        return prop_sc

    def test_deprecated_interpreter(self, microwave):
        with pytest.warns(DeprecationWarning):
            microwave.bind_property_statechart(microwave)

    def test_synchronised_time(self, microwave, property_statechart):
        assert microwave.time == property_statechart.time
        microwave.clock.time += 10
        assert microwave.time == property_statechart.time

    def test_empty_step(self, microwave, property_statechart):
        microwave.execute()
        assert property_statechart.queue.call_args_list[0][0][0] == MetaEvent('step started', time=0)
        assert property_statechart.queue.call_args_list[-1][0][0] == MetaEvent('step ended')

        for call in property_statechart.queue.call_args_list:
            assert isinstance(call[0][0], MetaEvent)

    def test_event_sent(self, microwave, property_statechart):
        # Add send to a state
        state = microwave.statechart.state_for('door closed')
        state.on_entry = 'send("test")'

        microwave.execute()

        assert MetaEvent('event sent', event=InternalEvent('test')) in [x[0][0] for x in property_statechart.queue.call_args_list]

    def test_meta_event_sent(self, microwave, property_statechart):
        # Add meta to a state
        state = microwave.statechart.state_for('door closed')
        state.on_entry = 'notify("test", x=1, y="hello")'

        microwave.execute()

        assert MetaEvent('event sent', event=MetaEvent('test', x=1, y='hello')) not in [x[0][0] for x in property_statechart.queue.call_args_list]
        assert MetaEvent('test', x=1, y='hello') in [x[0][0] for x in property_statechart.queue.call_args_list]

    def test_trace(self, microwave, property_statechart):
        microwave.queue('door_opened')
        microwave.execute()

        call_list = [
            MetaEvent('step started', time=0),
            MetaEvent('state entered', state='controller'),
            MetaEvent('state entered', state='door closed'),
            MetaEvent('state entered', state='closed without item'),
            MetaEvent('step ended'),

            MetaEvent('step started', time=0),
            MetaEvent('event consumed', event=Event('door_opened')),
            MetaEvent('state exited', state='closed without item'),
            MetaEvent('state exited', state='door closed'),
            MetaEvent('transition processed', source='closed without item', target='opened without item', event=Event('door_opened')),
            MetaEvent('state entered', state='door opened'),
            MetaEvent('state entered', state='opened without item'),
            MetaEvent('event sent', event=InternalEvent('lamp_switch_on')),
            MetaEvent('step ended')
        ]

        for i, call in enumerate(call_list):
            effective_call = property_statechart.queue.call_args_list[i][0][0]

            assert isinstance(effective_call, MetaEvent)
            assert call.name == effective_call.name

            for param in ['state', 'source', 'target', 'event']:
                if param in call.data:
                    assert effective_call.data[param] == call.data[param]

    def test_final(self, microwave, property_statechart):
        microwave.execute()
        assert not property_statechart.final

        property_statechart.final = True
        assert property_statechart.final

        with pytest.raises(PropertyStatechartError):
            microwave.execute()
