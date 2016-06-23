import unittest
from sismic import io
from sismic.interpreter import Interpreter
from sismic.model import MacroStep, MicroStep, Event, InternalEvent
from sismic.stories import Story, random_stories_generator, story_from_trace, Pause


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
        with open('tests/yaml/simple.yaml') as f:
            sc = io.import_from_yaml(f)

        interpreter = Interpreter(sc)
        trace = story.tell(interpreter)

        self.assertTrue(interpreter.final)
        self.assertEqual(interpreter.time, 5)
        self.assertEqual(len(trace), 4)

    def test_tell_by_step(self):
        story = Story([Event('goto s2'), Pause(5), Event('goto final')])
        with open('tests/yaml/simple.yaml') as f:
            sc = io.import_from_yaml(f)

        interpreter = Interpreter(sc)
        teller = story.tell_by_step(interpreter)
        self.assertEqual(Event('goto s2'), next(teller)[0])
        self.assertEqual(Pause(5), next(teller)[0])
        self.assertEqual(Event('goto final'), next(teller)[0])
        with self.assertRaises(StopIteration):
            next(teller)

        self.assertTrue(interpreter.final)
        self.assertEqual(interpreter.time, 5)


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


class StoryFromTraceTests(unittest.TestCase):
    def test_empty_trace(self):
        trace = []
        self.assertListEqual(story_from_trace(trace), [])

    def test_events(self):
        trace = [
            MacroStep(0, [MicroStep(event=Event('a'))]),
            MacroStep(0, [MicroStep(event=Event('b'))]),
            MacroStep(0, [MicroStep(event=Event('c'))]),
            MacroStep(0, [MicroStep(event=Event('d'))]),
        ]
        self.assertListEqual(story_from_trace(trace), [
            Event('a'), Event('b'), Event('c'), Event('d')
        ])

    def test_pauses(self):
        trace = [
            MacroStep(0, []),
            MacroStep(10, []),
            MacroStep(10, []),
            MacroStep(15, []),
        ]
        self.assertListEqual(story_from_trace(trace), [
            Pause(10), Pause(5)
        ])

    def test_initial_pause(self):
        trace = [MacroStep(10, [])]
        self.assertListEqual(story_from_trace(trace), [Pause(10)])

    def test_events_and_pauses(self):
        trace = [
            MacroStep(2, [MicroStep(event=Event('a'))]),
            MacroStep(5, [MicroStep(event=Event('b'))]),
            MacroStep(9, [MicroStep(event=Event('c'))]),
            MacroStep(14, [MicroStep(event=Event('d'))]),
        ]
        self.assertListEqual(story_from_trace(trace), [
            Pause(2), Event('a'), Pause(3), Event('b'), Pause(4), Event('c'), Pause(5), Event('d')
        ])

    def test_ignore_internal_events(self):
        trace = [
            MacroStep(2, [MicroStep(event=Event('a'))]),
            MacroStep(5, [MicroStep(event=Event('b'))]),
            MacroStep(9, [MicroStep(event=InternalEvent('c'))]),
            MacroStep(14, [MicroStep(event=Event('d'))]),
        ]
        self.assertListEqual(story_from_trace(trace), [
            Pause(2), Event('a'), Pause(3), Event('b'), Pause(4), Pause(5), Event('d')
        ])