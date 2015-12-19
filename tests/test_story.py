import unittest
from sismic import io
from sismic.interpreter import Interpreter
from sismic.stories import Story, Pause, Event, random_stories_generator, story_from_trace


class StoryTests(unittest.TestCase):
    def test_storycreation(self):
        story = Story()
        story.append(Event('a'))
        story.append(Event('b'))
        story.append(Pause(10))
        story.append(Event('c'))

        self.assertEqual(len(story), 4)

    def test_tell(self):
        story = Story([Event('goto s2'), Pause(5), Event('goto final')])
        sc = io.import_from_yaml(open('examples/simple/simple.yaml'))
        interpreter = Interpreter(sc)
        story.tell(interpreter)

        self.assertTrue(interpreter.final)
        self.assertEqual(interpreter.time, 5)
        self.assertEqual(len(interpreter.trace), 4)


class StoryFromTraceTests(unittest.TestCase):
    def test_simple(self):
        interpreter = Interpreter(io.import_from_yaml(open('examples/simple/simple.yaml')))
        Story([Pause(2), Event('goto s2'), Pause(3)]).tell(interpreter)
        story = story_from_trace(interpreter.trace)
        expected = Story([Event('started'),
                          Event('entered', {'state': 's1'}),
                          Pause(2),
                          Event('consumed', {'event': Event('goto s2')}),
                          Event('exited', {'state': 's1'}),
                          Event('processed', {'source': 's1', 'target': 's2', 'event': Event('goto s2')}),
                          Event('entered', {'state': 's2'}),
                          Event('exited', {'state': 's2'}),
                          Event('processed', {'source': 's2', 'target': 's3', 'event': None}),
                          Event('entered', {'state': 's3'}),
                          Event('stopped')])
        for a, b in zip(story, expected):
            self.assertEqual(a, b)
            if isinstance(a, Event):
                self.assertEqual(a.data.items(), b.data.items())
            else:
                self.assertEqual(a.duration, b.duration)


class RandomStoryTests(unittest.TestCase):
    def setUp(self):
        self.story = Story([Event('a'), Event('b'), Event('c'), Pause(1), Pause(2)])

    def test_length(self):
        self.assertEqual(len(next(random_stories_generator(self.story))), 5)
        self.assertEqual(len(next(random_stories_generator(self.story, length=3))), 3)
        self.assertEqual(len(next(random_stories_generator(self.story, length=6))), 6)
        self.assertEqual(len(next(random_stories_generator([]))), 0)

    def test_number(self):
        self.assertEqual(len(list(random_stories_generator(self.story, number=10))), 10)


class ElevatorStoryTests(unittest.TestCase):
    def test_7th_floor_never_reached(self):
        tested = Interpreter(io.import_from_yaml(open('examples/concrete/elevator.yaml')))
        story = Story([Event('floorSelected', {'floor': 8})])
        trace = story.tell(tested).trace

        test_story = story_from_trace(trace)

        tester = Interpreter(io.import_from_yaml(open('examples/testers/elevator_7th_floor_never_reached.yaml')))
        self.assertTrue(test_story.tell(tester).final)

    def test_7th_floor_never_reached_fails(self):
        tested = Interpreter(io.import_from_yaml(open('examples/concrete/elevator.yaml')))
        story = Story([Event('floorSelected', {'floor': 4}), Pause(2), Event('floorSelected', {'floor': 7})])
        trace = story.tell(tested).trace

        test_story = story_from_trace(trace)

        tester = Interpreter(io.import_from_yaml(open('examples/testers/elevator_7th_floor_never_reached.yaml')))
        self.assertFalse(test_story.tell(tester).final)

    def test_elevator_moves_after_10s(self):
        tested = Interpreter(io.import_from_yaml(open('examples/concrete/elevator.yaml')))
        stories = [
            Story([Event('floorSelected', {'floor': 4})]),
            Story([Event('floorSelected', {'floor': 0})]),
            Story([Event('floorSelected', {'floor': 4}), Pause(10)]),
            Story([Event('floorSelected', {'floor': 0}), Pause(10)]),
            Story([Event('floorSelected', {'floor': 4}), Pause(9)]),
            Story([Event('floorSelected', {'floor': 0}), Pause(9)]),
        ]

        for story in stories:
            test_story = story_from_trace(story.tell(tested).trace)

            tester = Interpreter(io.import_from_yaml(open('examples/testers/elevator_moves_after_10s.yaml')))
            self.assertTrue(test_story.tell(tester).final)