import unittest
from sismic import io
from sismic.model import MacroStep, MicroStep, Transition
from sismic.interpreter import Interpreter
from sismic.stories import Story, Pause, Event
from sismic.testing import teststory_from_trace
from sismic.testing.tester import ExecutionWatcher


class StoryFromTraceTests(unittest.TestCase):
    def test_simple(self):
        with open('tests/yaml/simple.yaml') as f:
            sc = io.import_from_yaml(f)
        interpreter = Interpreter(sc)

        trace = Story([Pause(2), Event('goto s2'), Pause(3)]).tell(interpreter)
        story = teststory_from_trace(trace)

        expected = Story([
            Event('execution started'),
            Pause(2),
            Event('step started'),
            Event('state entered', state='root'),
            Event('state entered', state='s1'),
            Event('step ended'),
            Event('step started'),
            Event('event consumed', event=Event('goto s2')),
            Event('state exited', state='s1'),
            Event('transition processed', source='s1', target='s2', event=Event('goto s2')),
            Event('state entered', state='s2'),
            Event('step ended'),
            Event('step started'),
            Event('state exited', state='s2'),
            Event('transition processed', source='s2', target='s3', event=None),
            Event('state entered', state='s3'),
            Event('step ended'),
            Event('execution stopped')
        ])
        for a, b in zip(story, expected):
            self.assertEqual(a, b)
            if isinstance(a, Event):
                self.assertEqual(a.data.items(), b.data.items())
            else:
                self.assertEqual(a.duration, b.duration)


class AtomicStoryFromTraceTests(unittest.TestCase):
    def test_execution_started(self):
        story = teststory_from_trace([])
        self.assertIn(Event('execution started'), story)

        story = teststory_from_trace([MacroStep(0, [])])
        self.assertIn(Event('execution started'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep()])])
        self.assertIn(Event('execution started'), story)

    def test_execution_stopped(self):
        story = teststory_from_trace([])
        self.assertIn(Event('execution stopped'), story)

        story = teststory_from_trace([MacroStep(0, [])])
        self.assertIn(Event('execution stopped'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep()])])
        self.assertIn(Event('execution stopped'), story)

    def test_step_started(self):
        story = teststory_from_trace([])
        self.assertNotIn(Event('step started'), story)

        story = teststory_from_trace([MacroStep(0, [])])
        self.assertIn(Event('step started'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep()])])
        self.assertIn(Event('step started'), story)

    def test_step_ended(self):
        story = teststory_from_trace([])
        self.assertNotIn(Event('step ended'), story)

        story = teststory_from_trace([MacroStep(0, [])])
        self.assertIn(Event('step ended'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep()])])
        self.assertIn(Event('step ended'), story)

    def test_event_consumed(self):
        story = teststory_from_trace([])
        self.assertNotIn(Event('event consumed'), story)

        story = teststory_from_trace([MacroStep(0, [])])
        self.assertNotIn(Event('event consumed'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep()])])
        self.assertNotIn(Event('event consumed'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep(event=Event('a'))])])
        self.assertIn(Event('event consumed', event=Event('a')), story)

    def test_state_entered(self):
        story = teststory_from_trace([])
        self.assertNotIn(Event('state entered'), story)

        story = teststory_from_trace([MacroStep(0, [])])
        self.assertNotIn(Event('state entered'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep()])])
        self.assertNotIn(Event('state entered'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep(entered_states=['a'])])])
        self.assertIn(Event('state entered', state='a'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep(entered_states=['a', 'b'])])])
        self.assertIn(Event('state entered', state='a'), story)
        self.assertIn(Event('state entered', state='b'), story)
        self.assertLess(story.index(Event('state entered', state='a')),
                        story.index(Event('state entered', state='b')))

    def test_state_exited(self):
        story = teststory_from_trace([])
        self.assertNotIn(Event('state exited'), story)

        story = teststory_from_trace([MacroStep(0, [])])
        self.assertNotIn(Event('state exited'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep()])])
        self.assertNotIn(Event('state exited'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep(exited_states=['a'])])])
        self.assertIn(Event('state exited', state='a'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep(exited_states=['a', 'b'])])])
        self.assertIn(Event('state exited', state='a'), story)
        self.assertIn(Event('state exited', state='b'), story)
        self.assertLess(story.index(Event('state exited', state='a')),
                        story.index(Event('state exited', state='b')))

    def test_transition_processed(self):
        story = teststory_from_trace([])
        self.assertNotIn(Event('transition processed'), story)

        story = teststory_from_trace([MacroStep(0, [])])
        self.assertNotIn(Event('transition processed'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep()])])
        self.assertNotIn(Event('transition processed'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep(event=Event('c'), transition=Transition('a', 'b', event='c'))])])
        self.assertIn(Event('transition processed', source='a', target='b', event=Event('c')), story)

    def test_event_sent(self):
        story = teststory_from_trace([])
        self.assertNotIn(Event('event sent'), story)

        story = teststory_from_trace([MacroStep(0, [])])
        self.assertNotIn(Event('event sent'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep()])])
        self.assertNotIn(Event('event sent'), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep(sent_events=[Event('a')])])])
        self.assertIn(Event('event sent', event=Event('a')), story)

        story = teststory_from_trace([MacroStep(0, [MicroStep(sent_events=[Event('a'), Event('b')])])])
        self.assertIn(Event('event sent', event=Event('a')), story)
        self.assertIn(Event('event sent', event=Event('b')), story)
        self.assertLess(story.index(Event('event sent', event=Event('a'))),
                       story.index(Event('event sent', event=Event('b'))))


class ElevatorStoryTests(unittest.TestCase):
    def setUp(self):
        with open('docs/examples/elevator/elevator.yaml') as f:
            sc = io.import_from_yaml(f)
        self.tested = Interpreter(sc)

    def test_7th_floor_never_reached(self):
        story = Story([Event('floorSelected', floor=8)])
        trace = story.tell(self.tested)  # self.tested is an interpreter for our elevator

        test_story = teststory_from_trace(trace)

        with open('docs/examples/elevator/tester_elevator_7th_floor_never_reached.yaml') as f:
            tester = Interpreter(io.import_from_yaml(f))
        test_story.tell(tester)
        self.assertFalse(tester.final)

    def test_7th_floor_never_reached_fails(self):
        story = Story([Event('floorSelected', floor=4), Pause(2), Event('floorSelected', floor=7)])
        trace = story.tell(self.tested)  # self.tested is an interpreter for our elevator

        test_story = teststory_from_trace(trace)

        with open('docs/examples/elevator/tester_elevator_7th_floor_never_reached.yaml') as f:
            tester = Interpreter(io.import_from_yaml(f))
        test_story.tell(tester)
        self.assertTrue(tester.final)

    def test_elevator_moves_after_10s(self):
        stories = [
            Story([Event('floorSelected', floor=4)]),
            Story([Event('floorSelected', floor=0)]),
            Story([Event('floorSelected', floor=4), Pause(10)]),
            Story([Event('floorSelected', floor=0), Pause(10)]),
            Story([Event('floorSelected', floor=4), Pause(9)]),
            Story([Event('floorSelected', floor=0), Pause(9)]),
        ]

        for story in stories:
            with self.subTest(story=story):
                # Reopen because we need to reset it
                with open('docs/examples/elevator/elevator.yaml') as f:
                    sc = io.import_from_yaml(f)
                tested = Interpreter(sc)

                test_story = teststory_from_trace(story.tell(tested))

                with open('docs/examples/elevator/tester_elevator_moves_after_10s.yaml') as f:
                    tester = Interpreter(io.import_from_yaml(f))
                test_story.tell(tester)
                self.assertFalse(tester.final)


class WatchElevatorTests(unittest.TestCase):
    def setUp(self):
        with open('docs/examples/elevator/elevator.yaml') as f:
            sc = io.import_from_yaml(f)
        self.tested = Interpreter(sc)
        self.watcher = ExecutionWatcher(self.tested)

    def test_7th_floor_never_reached(self):
        with open('docs/examples/elevator/tester_elevator_7th_floor_never_reached.yaml') as f:
            tester_sc = io.import_from_yaml(f)

        tester = self.watcher.watch_with(tester_sc)
        self.watcher.start()

        # Send elevator to 4th
        self.tested.queue(Event('floorSelected', floor=4)).execute()
        self.watcher.stop()
        self.assertFalse(tester.final)

    def test_7th_floor_never_reached_fails(self):
        with open('docs/examples/elevator/tester_elevator_7th_floor_never_reached.yaml') as f:
            tester_sc = io.import_from_yaml(f)

        tester = self.watcher.watch_with(tester_sc)
        self.watcher.start()

        # Send elevator to 7th
        self.tested.queue(Event('floorSelected', floor=7)).execute()
        self.watcher.stop()
        self.assertTrue(tester.final)


    def test_7th_floor_never_reached_fails_fast(self):
        with open('docs/examples/elevator/tester_elevator_7th_floor_never_reached.yaml') as f:
            tester_sc = io.import_from_yaml(f)

        tester = self.watcher.watch_with(tester_sc, fails_fast=True)
        self.watcher.start()

        # Send elevator to 7th
        with self.assertRaises(AssertionError) as cm:
            self.tested.queue(Event('floorSelected', floor=7)).execute()
        self.assertTrue(tester.final)


    def test_destination_reached(self):
        with open('docs/examples/elevator/tester_elevator_destination_reached.yaml') as f:
            tester_statechart = io.import_from_yaml(f)

        # Create the interpreter and the watcher
        watcher = ExecutionWatcher(self.tested)

        # Add the tester and start watching
        tester = watcher.watch_with(tester_statechart)
        watcher.start()

        # Send the elevator to 4th
        self.tested.queue(Event('floorSelected', floor=4)).execute(max_steps=2)
        self.assertEqual(tester.context['destinations'], [4])

        self.tested.execute()
        self.assertEqual(tester.context['destinations'], [])

        # Stop watching. The tester must be in a final state
        watcher.stop()

        self.assertFalse(tester.final)