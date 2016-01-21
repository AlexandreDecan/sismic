import unittest
from sismic import io
from sismic.interpreter import Interpreter
from sismic.stories import Story, Pause, Event
from sismic.testing import teststory_from_trace


class StoryFromTraceTests(unittest.TestCase):
    def test_simple(self):
        interpreter = Interpreter(io.import_from_yaml(open('tests/yaml/simple.yaml')))
        Story([Pause(2), Event('goto s2'), Pause(3)]).tell(interpreter)
        story = teststory_from_trace(interpreter.trace)
        expected = Story([Event('started'),
                          Event('step'),
                          Event('entered', state='root'),
                          Event('entered', state='s1'),
                          Pause(2),
                          Event('step'),
                          Event('consumed', event=Event('goto s2')),
                          Event('exited', state='s1'),
                          Event('processed', source='s1', target='s2', event=Event('goto s2')),
                          Event('entered', state='s2'),
                          Event('step'),
                          Event('exited', state='s2'),
                          Event('processed', source='s2', target='s3', event=None),
                          Event('entered', state='s3'),
                          Event('stopped')])
        for a, b in zip(story, expected):
            self.assertEqual(a, b)
            if isinstance(a, Event):
                self.assertEqual(a.data.items(), b.data.items())
            else:
                self.assertEqual(a.duration, b.duration)


class ElevatorStoryTests(unittest.TestCase):
    def test_7th_floor_never_reached(self):
        tested = Interpreter(io.import_from_yaml(open('docs/examples/elevator.yaml')))
        story = Story([Event('floorSelected', floor=8)])
        trace = story.tell(tested).trace

        test_story = teststory_from_trace(trace)

        tester = Interpreter(io.import_from_yaml(open('docs/examples/tester_elevator_7th_floor_never_reached.yaml')))
        self.assertTrue(test_story.tell(tester).final)

    def test_7th_floor_never_reached_fails(self):
        tested = Interpreter(io.import_from_yaml(open('docs/examples/elevator.yaml')))
        story = Story([Event('floorSelected', floor=4), Pause(2), Event('floorSelected', floor=7)])
        trace = story.tell(tested).trace

        test_story = teststory_from_trace(trace)

        tester = Interpreter(io.import_from_yaml(open('docs/examples/tester_elevator_7th_floor_never_reached.yaml')))
        self.assertFalse(test_story.tell(tester).final)

    def test_elevator_moves_after_10s(self):
        tested_sc = io.import_from_yaml(open('docs/examples/elevator.yaml'))
        tester_sc = io.import_from_yaml(open('docs/examples/tester_elevator_moves_after_10s.yaml'))

        stories = [
            Story([Event('floorSelected', floor=4)]),
            Story([Event('floorSelected', floor=0)]),
            Story([Event('floorSelected', floor=4), Pause(10)]),
            Story([Event('floorSelected', floor=0), Pause(10)]),
            Story([Event('floorSelected', floor=4), Pause(9)]),
            Story([Event('floorSelected', floor=0), Pause(9)]),
        ]

        for story in stories:
            tested = Interpreter(tested_sc)
            test_story = teststory_from_trace(story.tell(tested).trace)

            tester = Interpreter(tester_sc)
            self.assertTrue(test_story.tell(tester).final)