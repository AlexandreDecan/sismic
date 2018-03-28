import pytest

from sismic.exceptions import StatechartError
from sismic.model import Statechart, Transition, CompoundState, BasicState
from sismic.interpreter import Event


class TestEvents:
    def test_create_event(self):
        assert Event('hello') == Event(name='hello')

    def test_empty_event(self):
        with pytest.raises(TypeError):
            Event()

    def test_parametrized_events(self):
        event = Event('test', a=1, b=2, c=3)

        assert event.data == {'a': 1, 'b': 2, 'c': 3}
        assert event.a == 1
        assert event.b == 2
        assert event.c == 3
        assert event.name == 'test'

        with pytest.raises(AttributeError):
            _ = event.d

        with pytest.raises(KeyError):
            _ = event.data['d']

    def test_cannot_use_name_as_parameter(self):
        with pytest.raises(TypeError):
            Event('test', name='fail')


class TestStatechartTraveral:
    def test_parent(self, composite_statechart):
        assert composite_statechart.parent_for('s2') == 'root'
        assert composite_statechart.parent_for('root') is None

        with pytest.raises(StatechartError):
            composite_statechart.parent_for('unknown')

    def test_children(self, composite_statechart):
        assert set(composite_statechart.children_for('root')) == {'s1', 's2'}
        assert composite_statechart.children_for('s1b2') == []

    def test_ancestors(self, composite_statechart):
        assert composite_statechart.ancestors_for('s2') == ['root']
        assert composite_statechart.ancestors_for('s1a') == ['s1', 'root']
        assert composite_statechart.ancestors_for('s1b1') == ['s1b', 's1', 'root']

    def test_descendants(self, composite_statechart):
        assert composite_statechart.descendants_for('s2') == []
        assert set(composite_statechart.descendants_for('s1')) == {'s1a', 's1b', 's1b1', 's1b2'}

    def test_depth(self, composite_statechart):
        assert composite_statechart.depth_for('root') == 1
        assert composite_statechart.depth_for('s1') == 2
        assert composite_statechart.depth_for('s1a') == 3
        assert composite_statechart.depth_for('s1b1') == 4
        assert composite_statechart.depth_for('s2') == 2
        assert composite_statechart.depth_for('s1b2') == 4

    def test_lca(self, composite_statechart):
        assert composite_statechart.least_common_ancestor('s1', 's2') == 'root'
        assert composite_statechart.least_common_ancestor('s1', 's1a') == 'root'
        assert composite_statechart.least_common_ancestor('s1a', 's1b') == 's1'
        assert composite_statechart.least_common_ancestor('s1a', 's1b1') == 's1'

    def test_leaf(self, composite_statechart):
        assert sorted(composite_statechart.leaf_for([])) == []
        assert sorted(composite_statechart.leaf_for(['s1'])) == ['s1']
        assert sorted(composite_statechart.leaf_for(['s1', 's2'])) == ['s1', 's2']
        assert sorted(composite_statechart.leaf_for(['s1', 's1b1', 's2'])) == ['s1b1', 's2']
        assert sorted(composite_statechart.leaf_for(['s1', 's1b', 's1b1'])) == ['s1b1']

    def test_events_for(self, composite_statechart):
        assert set(composite_statechart.events_for()) == {'click', 'close', 'validate'}
        assert set(composite_statechart.events_for('s1b1')) == {'validate'}
        assert set(composite_statechart.events_for(['s1b1', 's1b'])) == {'click', 'validate'}

    def test_name_collision(self):
        root = CompoundState('root', 'a')
        sc = Statechart('test')
        sc.add_state(root, None)
        s1 = BasicState('a')
        s2 = BasicState('a')
        sc.add_state(s1, parent='root')

        with pytest.raises(StatechartError) as e:
            sc.add_state(s2, parent='root')
        assert 'already exists!' in str(e.value)

    def test_name_is_none(self):
        sc = Statechart('test')
        state = BasicState(name=None)
        with pytest.raises(StatechartError) as e:
            sc.add_state(state, None)
        assert 'must have a name' in str(e.value)

    def test_root_already_defined(self):
        root = CompoundState('root', 'a')
        sc = Statechart('test')
        sc.add_state(root, None)

        with pytest.raises(StatechartError) as e:
            sc.add_state(root, None)
        assert 'already exists!' in str(e.value)


class TestStatechartValidate:
    # REMARK: "Positive" tests are already done during io.import_from_yaml!
    def test_history_memory_is_not_a_child(self, history_statechart):
        history_statechart.state_for('loop.H').memory = 'pause'
        with pytest.raises(StatechartError) as e:
            history_statechart._validate_historystate_memory()
        assert 'Initial memory' in str(e.value)
        assert 'must be a parent\'s child' in str(e.value)

    def test_history_memory_unknown(self, history_statechart):
        history_statechart.state_for('loop.H').memory = 'unknown'
        with pytest.raises(StatechartError) as e:
            history_statechart._validate_historystate_memory()
        assert 'Initial memory' in str(e.value)
        assert 'does not exist' in str(e.value)

    def test_history_memory_self(self, history_statechart):
        history_statechart.state_for('loop.H').memory = 'loop.H'
        with pytest.raises(StatechartError) as e:
            history_statechart._validate_historystate_memory()
        assert 'Initial memory' in str(e.value)
        assert 'cannot target itself' in str(e.value)

    def test_compound_initial_not_a_child(self, composite_statechart):
        composite_statechart.state_for('s1b').initial = 's1'
        with pytest.raises(StatechartError) as e:
            composite_statechart._validate_compoundstate_initial()
        assert 'Initial state' in str(e.value)
        assert 'must be a child state' in str(e.value)

    def test_compound_initial_unknown(self, composite_statechart):
        composite_statechart.state_for('s1b').initial = 'unknown'
        with pytest.raises(StatechartError) as e:
            composite_statechart._validate_compoundstate_initial()
        assert 'Initial state' in str(e.value)
        assert 'does not exist' in str(e.value)


class TestTransition:
    def test_transitions_from(self, internal_statechart):
        assert internal_statechart.transitions_from('root') == []
        assert len(internal_statechart.transitions_from('active')) == 2
        assert len(internal_statechart.transitions_from('s1')) == 1

        for transition in internal_statechart.transitions_from('active'):
            assert transition.source == 'active'

        with pytest.raises(StatechartError) as e:
            internal_statechart.transitions_from('unknown')
        assert 'does not exist' in str(e.value)

    def test_transitions_to(self, internal_statechart):
        assert internal_statechart.transitions_to('root') == []
        assert len(internal_statechart.transitions_to('s1')) == 1
        assert len(internal_statechart.transitions_to('s2')) == 2

        for transition in internal_statechart.transitions_from('s2'):
            assert transition.target == 's2'

        with pytest.raises(StatechartError) as e:
            internal_statechart.transitions_to('unknown')
        assert 'does not exist' in str(e.value)

    def test_transitions_with(self, internal_statechart):
        assert len(internal_statechart.transitions_with('next')) == 1
        assert len(internal_statechart.transitions_with('unknown')) == 0

    def test_add_transition(self, internal_statechart):
        with pytest.raises(StatechartError) as e:
            internal_statechart.add_transition(Transition('s2'))
        assert 'Cannot add' in str(e.value)

        internal_statechart.add_transition(Transition('s1'))
        assert len(internal_statechart.transitions_to('s1')) == 2

    def test_rotate_source(self, internal_statechart):
        tr = next(t for t in internal_statechart.transitions if t.source == 's1')
        internal_statechart.rotate_transition(tr, new_source='s1')
        assert tr.source == 's1'

        internal_statechart.rotate_transition(tr, new_source='active')
        assert tr.source == 'active'

        with pytest.raises(StatechartError) as e:
            internal_statechart.rotate_transition(tr, new_source=None)
        assert 'State' in str(e.value)
        assert 'does not exist' in str(e.value)

        with pytest.raises(StatechartError) as e:
            internal_statechart.rotate_transition(tr, new_source='s2')
        assert 'cannot have transitions' in str(e.value)

        with pytest.raises(StatechartError) as e:
            internal_statechart.rotate_transition(tr, new_source='unknown')
        assert 'State' in str(e.value)
        assert 'does not exist' in str(e.value)

        internal_statechart.validate()

    def test_rotate_target(self, internal_statechart):
        tr = next(t for t in internal_statechart.transitions if t.source == 's1')
        internal_statechart.rotate_transition(tr, new_target='s2')
        assert tr.target == 's2'

        internal_statechart.rotate_transition(tr, new_target='active')
        assert tr.target == 'active'

        internal_statechart.rotate_transition(tr, new_target=None)
        assert tr.target is None
        assert tr.internal

        with pytest.raises(StatechartError) as e:
            internal_statechart.rotate_transition(tr, new_target='unknown')
        assert 'State' in str(e.value)
        assert 'does not exist' in str(e.value)

        internal_statechart.validate()

    def test_rotate_both(self, internal_statechart):
        tr = next(t for t in internal_statechart.transitions if t.source == 's1')

        internal_statechart.rotate_transition(tr, new_source='s1', new_target='s2')
        assert tr.source == 's1'
        assert tr.target == 's2'
        internal_statechart.validate()

    def test_rotate_both_unexisting(self, internal_statechart):
        tr = next(t for t in internal_statechart.transitions if t.source == 's1')

        with pytest.raises(ValueError):
            internal_statechart.rotate_transition(tr)

        with pytest.raises(StatechartError) as e:
            internal_statechart.rotate_transition(tr, new_source=None, new_target=None)
        assert 'State' in str(e.value)
        assert 'does not exist' in str(e.value)

        with pytest.raises(StatechartError) as e:
            internal_statechart.rotate_transition(tr, new_source='s2', new_target='s2')
        assert 'State' in str(e.value)
        assert 'cannot have transitions' in str(e.value)

        internal_statechart.validate()

    def test_rotate_both_with_internal(self, internal_statechart):
        tr = next(t for t in internal_statechart.transitions if t.source == 's1')

        internal_statechart.rotate_transition(tr, new_source='s1', new_target=None)
        assert tr.source == 's1'
        assert tr.target is None
        assert tr.internal
        internal_statechart.validate()

    def test_remove_existing_transition(self, internal_statechart):
        transitions = internal_statechart.transitions
        for transition in transitions:
            internal_statechart.remove_transition(transition)
        assert internal_statechart.transitions == []
        internal_statechart.validate()

    def test_remove_unexisting_transition(self, internal_statechart):
        with pytest.raises(StatechartError) as e:
            internal_statechart.remove_transition(None)
        assert 'Transition' in str(e.value)
        assert 'does not exist' in str(e.value)

        with pytest.raises(StatechartError) as e:
            internal_statechart.remove_transition(Transition('a', 'b'))
        assert 'Transition' in str(e.value)
        assert 'does not exist' in str(e.value)

        internal_statechart.validate()


class TestStatechartStates:
    def test_remove_existing_state(self, internal_statechart):
        internal_statechart.remove_state('active')

        assert 'active' not in internal_statechart.states
        nb_transitions = 0
        for transition in internal_statechart.transitions:
            if transition.source == 'active':
                nb_transitions += 1
        assert nb_transitions == 0

        nb_transitions = 0
        for transition in internal_statechart.transitions:
            if transition.target == 'active':
                nb_transitions += 1
        assert nb_transitions == 0
        internal_statechart.validate()

    def test_remove_unregister_parent_children(self, internal_statechart):
        internal_statechart.remove_state('s1')
        assert 's1' not in internal_statechart.children_for('active')
        internal_statechart.validate()

    def test_remove_unexisting_state(self, internal_statechart):
        with pytest.raises(StatechartError) as e:
            internal_statechart.remove_state('unknown')
        assert 'State' in str(e.value)
        assert 'does not exist' in str(e.value)

        internal_statechart.validate()

    def test_remove_root_state(self, internal_statechart):
        internal_statechart.remove_state('root')
        assert internal_statechart.transitions == []
        assert internal_statechart.states == []
        assert internal_statechart.root is None
        internal_statechart.validate()

    def test_remove_nested_states(self, composite_statechart):
        composite_statechart.remove_state('s1')
        assert 's1a' not in composite_statechart.states
        composite_statechart.validate()

    def test_remove_nested_states_continued(self, composite_statechart):
        composite_statechart.remove_state('s1a')
        assert 's1a' not in composite_statechart.states
        composite_statechart.validate()

    def test_rename_unexisting_state(self, internal_statechart):
        with pytest.raises(StatechartError) as e:
            internal_statechart.rename_state('unknown', 's3')
        assert 'State' in str(e.value)
        assert 'does not exist' in str(e.value)

        internal_statechart.validate()

    def test_do_not_change_name(self, internal_statechart):
        internal_statechart.rename_state('s2', 's2')

        assert 's2' in internal_statechart.states
        assert internal_statechart.parent_for('s2') == 'root'
        assert 's2' in internal_statechart.children_for('root')

        internal_statechart.validate()

    def test_rename_to_an_existing_state(self, internal_statechart):
        with pytest.raises(StatechartError) as e:
            internal_statechart.rename_state('s2', 's1')
        assert 'State' in str(e.value)
        assert 'already exists!' in str(e.value)

        internal_statechart.validate()

    def test_rename_old_disappears(self, composite_statechart):
        composite_statechart.rename_state('s1', 'new s1')

        assert 's1' not in composite_statechart.states
        assert 's1' != composite_statechart.parent_for('s1a')
        assert 's1' not in composite_statechart.children_for('root')

        with pytest.raises(StatechartError) as e:
            composite_statechart.state_for('s1')
        assert 'State' in str(e.value)
        assert 'does not exist' in str(e.value)

        with pytest.raises(StatechartError) as e:
            composite_statechart.children_for('s1')
        assert 'State' in str(e.value)
        assert 'does not exist' in str(e.value)

        with pytest.raises(StatechartError) as e:
            composite_statechart.parent_for('s1')
        assert 'State' in str(e.value)
        assert 'does not exist' in str(e.value)

        composite_statechart.validate()

    def test_rename_change_state_name(self, composite_statechart):
        state = composite_statechart.state_for('s1')
        composite_statechart.rename_state('s1', 'new s1')
        assert state.name == 'new s1'

    def test_rename_new_appears(self, composite_statechart):
        composite_statechart.rename_state('s1', 'new s1')

        assert 'new s1' in composite_statechart.states
        assert 'new s1' == composite_statechart.parent_for('s1a')
        assert 'new s1' in composite_statechart.children_for('root')

        composite_statechart.state_for('new s1')
        composite_statechart.children_for('new s1')
        composite_statechart.parent_for('new s1')
        composite_statechart.validate()

    def test_rename_adapt_transitions(self, internal_statechart):
        internal_statechart.rename_state('s1', 's3')

        nb_transitions = 0
        for transition in internal_statechart.transitions:
            if transition.source == 's1':
                nb_transitions += 1
        assert nb_transitions == 0

        nb_transitions = 0
        for transition in internal_statechart.transitions:
            if transition.target == 's1':
                nb_transitions += 1
        assert nb_transitions == 0

        assert len(internal_statechart.transitions_from('s3')) == 1
        assert len(internal_statechart.transitions_to('s2')) == 2
        internal_statechart.validate()

    def test_rename_root(self, internal_statechart):
        internal_statechart.rename_state('root', 'new root')

        assert 'new root' in internal_statechart.states
        assert 'root' not in internal_statechart.states

        assert internal_statechart.parent_for('new root') is None
        assert internal_statechart.parent_for('active') == 'new root'
        assert 'active' in internal_statechart.children_for('new root')

        internal_statechart.validate()

    def test_rename_change_initial(self, internal_statechart):
        internal_statechart.rename_state('active', 's3')
        assert internal_statechart.state_for('root').initial == 's3'
        internal_statechart.validate()

    def test_rename_change_memory(self, history_statechart):
        history_statechart.state_for('loop.H').memory = 's1'
        history_statechart.rename_state('s1', 's4')
        assert history_statechart.state_for('loop.H').memory == 's4'
        history_statechart.validate()

    def test_move_simple(self, composite_statechart):
        composite_statechart.move_state('s1b2', 's1b1')
        assert 's1b2' in composite_statechart.children_for('s1b1')
        assert 's1b2' not in composite_statechart.children_for('s1b')
        assert 's1b1' == composite_statechart.parent_for('s1b2')
        composite_statechart.validate()

    def test_move_composite(self, composite_statechart):
        composite_statechart.move_state('s1b', 's1a')
        assert 's1b' in composite_statechart.children_for('s1a')
        assert 's1b' not in composite_statechart.children_for('s1')
        assert 's1a' == composite_statechart.parent_for('s1b')
        composite_statechart.validate()

    def test_move_to_descendant(self, composite_statechart):
        with pytest.raises(StatechartError) as e:
            composite_statechart.move_state('s1b', 's1b')
        assert 'State' in str(e.value)
        assert 'cannot be moved into itself or one of its descendants' in str(e.value)

        with pytest.raises(StatechartError) as e:
            composite_statechart.move_state('s1b', 's1b1')
        assert 'State' in str(e.value)
        assert 'cannot be moved into itself or one of its descendants' in str(e.value)

        with pytest.raises(StatechartError) as e:
            composite_statechart.move_state('s1', 's1b1')
        assert 'State' in str(e.value)
        assert 'cannot be moved into itself or one of its descendants' in str(e.value)

        composite_statechart.validate()

    def test_move_unexisting(self, composite_statechart):
        with pytest.raises(StatechartError) as e:
            composite_statechart.move_state('unknown', 's1b1')
        assert 'State' in str(e.value)
        assert 'does not exist' in str(e.value)

        with pytest.raises(StatechartError) as e:
            composite_statechart.move_state('s1b1', 'unknown')
        assert 'State' in str(e.value)
        assert 'does not exist' in str(e.value)

        composite_statechart.validate()

    def test_move_with_initial(self, composite_statechart):
        composite_statechart.move_state('s1a', 'root')
        assert composite_statechart.state_for('s1').initial is None
        composite_statechart.validate()

    def test_move_with_memory(self, history_statechart):
        history_statechart.state_for('loop.H').memory = 's1'
        history_statechart.move_state('s1', 's2')
        assert history_statechart.state_for('loop.H').memory is None
        history_statechart.validate()


class TestCopyFromStatechart:
    @pytest.fixture
    def modified_simple_statechart(self, simple_statechart):
        for state in simple_statechart.states:
            simple_statechart.rename_state(state, 'sc1_' + state)
        return simple_statechart

    def test_keep_other_states(self, modified_simple_statechart, composite_statechart):
        sc1_states = modified_simple_statechart.states

        composite_statechart.copy_from_statechart(modified_simple_statechart, source='sc1_root', replace='s1a')
        assert 's1a' in composite_statechart.states
        assert 'sc1_root' not in composite_statechart.states

        sc1_states.remove('sc1_root')
        for state in sc1_states:
            assert state in composite_statechart.states

    def test_keep_other_transitions(self, modified_simple_statechart, composite_statechart):
        sc1_transitions = modified_simple_statechart.transitions

        composite_statechart.copy_from_statechart(modified_simple_statechart, source='sc1_root', replace='s1b1')

        for transition in sc1_transitions:
            assert transition in composite_statechart.transitions

    def test_keep_existing_states(self, modified_simple_statechart, composite_statechart):
        sc2_states = composite_statechart.states

        composite_statechart.copy_from_statechart(modified_simple_statechart, source='sc1_root', replace='s1b1')

        for state in sc2_states:
            assert state in composite_statechart.states

    def test_keep_existing_transitions(self, modified_simple_statechart, composite_statechart):
        sc2_transitions = composite_statechart.transitions

        composite_statechart.copy_from_statechart(modified_simple_statechart, source='sc1_root', replace='s1b1')

        for transition in sc2_transitions:
            assert transition in composite_statechart.transitions

    def test_orphaned_transitions(self, modified_simple_statechart, composite_statechart):
        with pytest.raises(StatechartError) as e:
            composite_statechart.copy_from_statechart(modified_simple_statechart, source='sc1_s1', replace='s1b1')
        assert 'not contained in' in str(e.value)

        with pytest.raises(StatechartError) as e:
            composite_statechart.copy_from_statechart(modified_simple_statechart, source='sc1_final', replace='s1b1')
            assert 'not contained in' in str(e.value)

    def test_invalid_plug(self, modified_simple_statechart, composite_statechart):
        # On compound
        with pytest.raises(StatechartError) as e:
            composite_statechart.copy_from_statechart(modified_simple_statechart, source='sc1_root', replace='s1')
        assert 'children' in str(e.value)

        with pytest.raises(StatechartError) as e:
            composite_statechart.copy_from_statechart(modified_simple_statechart, source='sc1_root', replace='s1b')
            assert 'children' in str(e.value)

    def test_with_namespace(self, modified_simple_statechart, composite_statechart):
        sc1_states = modified_simple_statechart.states
        sc2_states = composite_statechart.states

        namespace = lambda s: '__' + s
        composite_statechart.copy_from_statechart(modified_simple_statechart, source='sc1_root', replace='s1a', renaming_func=namespace)

        expected_states = sc2_states + [namespace(s) for s in sc1_states]
        expected_states.remove(namespace(modified_simple_statechart.root))

        assert set(expected_states) == set(composite_statechart.states)

    def test_conflicting_names(self, modified_simple_statechart, composite_statechart):
        modified_simple_statechart.rename_state('sc1_s1', 's1')
        with pytest.raises(StatechartError) as e:
            composite_statechart.copy_from_statechart(modified_simple_statechart, source='sc1_root', replace='s1a')
        assert 'already exists' in str(e.value)
