import unittest
from sismic import io
from sismic.interpreter import Interpreter
from sismic.story import Story, Pause, Event, random_stories, story_from_trace


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

        self.assertFalse(interpreter.running)
        self.assertEqual(interpreter.time, 5)
        self.assertEqual(len(interpreter.trace), 4)


class StoryFromTraceTests(unittest.TestCase):
    def test_simple(self):
        interpreter = Interpreter(io.import_from_yaml(open('examples/simple/simple.yaml')))
        Story([Event('goto s2')]).tell(interpreter)
        story = story_from_trace(interpreter.trace)
        expected = Story([Event('started'),
                          Event('entered', {'state': 's1'}),
                          Event('consumed', {'event': Event('goto s2')}),
                          Event('processed', {'source': 's1', 'target': 's2', 'event': Event('goto s2')}),
                          Event('exited', {'state': 's1'}),
                          Event('entered', {'state': 's2'}),
                          Event('processed', {'source': 's2', 'target': 's3', 'event': None}),
                          Event('exited', {'state': 's2'}),
                          Event('entered', {'state': 's3'}),
                          Event('stopped')])
        for a, b in zip(story, expected):
            self.assertEqual(a, b)
            self.assertEqual(a.data.items(), b.data.items())
