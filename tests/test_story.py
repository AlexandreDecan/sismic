import unittest
from sismic import io
from sismic.interpreter import Interpreter
from sismic.stories import Story, Pause, Event, random_stories_generator


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
        sc = io.import_from_yaml(open('tests/yaml/simple.yaml'))
        interpreter = Interpreter(sc)
        story.tell(interpreter)

        self.assertTrue(interpreter.final)
        self.assertEqual(interpreter.time, 5)
        self.assertEqual(len(interpreter.trace), 4)


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

