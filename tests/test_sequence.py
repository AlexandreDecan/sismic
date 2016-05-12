import unittest
from sismic.code.sequence import *


class ConditionTests(unittest.TestCase):
    def setUp(self):
        self.true = SequenceCondition('True')
        self.false = SequenceCondition('False')

    def test_initial_call(self):
        self.assertEqual(self.true.evaluate(), True)
        self.assertEqual(self.false.evaluate(), False)

    def test_does_change(self):
        self.true.evaluate()
        self.false.evaluate()

        self.true.code = 'False'
        self.false.code = 'True'
        self.assertEqual(self.true.evaluate(), False)
        self.assertEqual(self.false.evaluate(), True)

    def test_forced_call(self):
        self.assertEqual(self.true.evaluate(True), True)
        self.assertEqual(self.false.evaluate(False), False)


class ConstantsTests(unittest.TestCase):
    def setUp(self):
        self.success = SequenceSuccess()
        self.failure = SequenceFailure()
        self.finish = SequenceFinish()

    def test_initial_call(self):
        self.assertEqual(self.success.evaluate(), True)
        self.assertEqual(self.failure.evaluate(), False)
        self.assertEqual(self.finish.evaluate(), False)

    def test_forced_call(self):
        self.assertEqual(self.success.evaluate(True), True)
        self.assertEqual(self.failure.evaluate(True), False)
        self.assertEqual(self.finish.evaluate(True), True)


# ################################################################


class SometimesTests(unittest.TestCase):
    def setUp(self):
        self.true = SequenceSometimes(SequenceCondition('True'))
        self.false = SequenceSometimes(SequenceCondition('False'))

    def test_initial_call(self):
        self.assertEqual(self.true.evaluate(), True)
        self.assertEqual(self.false.evaluate(), None)

    def test_true_does_not_update(self):
        self.true.evaluate()
        self.true.sequence.code = 'False'
        self.assertEqual(self.true.evaluate(), True)

    def test_false_does_update(self):
        self.false.evaluate()
        self.false.sequence.code = 'True'
        self.assertEqual(self.false.evaluate(), True)

    def test_forced_call(self):
        self.assertEqual(self.true.evaluate(True), True)
        self.assertEqual(self.false.evaluate(True), False)


class NotTests(unittest.TestCase):
    def setUp(self):
        self.ntrue = SequenceNegate(SequenceCondition('True'))
        self.nfalse = SequenceNegate(SequenceCondition('False'))
        self.nundefined = SequenceNegate(SequenceSometimes(SequenceCondition('False')))

    def test_initial_call(self):
        self.assertEqual(self.ntrue.evaluate(), False)
        self.assertEqual(self.nfalse.evaluate(), True)
        self.assertEqual(self.nundefined.evaluate(), None)

    def test_forced_call(self):
        self.assertEqual(self.ntrue.evaluate(True), False)
        self.assertEqual(self.nfalse.evaluate(True), True)
        self.assertEqual(self.nundefined.evaluate(True), True)


class AlwaysTests(unittest.TestCase):
    def setUp(self):
        self.true = SequenceCondition('True')
        self.false = SequenceCondition('False')
        self.atrue = SequenceAlways(self.true)
        self.afalse = SequenceAlways(self.false)

    def test_initial_call(self):
        self.assertEqual(self.atrue.evaluate(), None)
        self.assertEqual(self.afalse.evaluate(), False)

    def test_false_does_not_change(self):
        self.afalse.evaluate()
        self.false.code = 'True'
        self.assertEqual(self.afalse.evaluate(), False)

    def test_true_does_change(self):
        self.atrue.evaluate()
        self.true.code = 'False'
        self.assertEqual(self.atrue.evaluate(), False)

    def test_forced_call(self):
        self.assertEqual(self.atrue.evaluate(True), True)
        self.assertEqual(self.afalse.evaluate(True), False)


class NeverTests(unittest.TestCase):
    def setUp(self):
        self.true = SequenceTimedCondition(True, False)
        self.false = SequenceTimedCondition(False, True)
        self.ntrue = SequenceNever(self.true)
        self.nfalse = SequenceNever(self.false)

    def test_initial_call(self):
        self.assertEqual(self.ntrue.evaluate(), False)
        self.assertEqual(self.nfalse.evaluate(), None)

    def test_true_does_not_change(self):
        self.ntrue.evaluate()
        self.true.code = 'False'
        self.assertEqual(self.ntrue.evaluate(), False)

    def test_false_does_change(self):
        self.nfalse.evaluate()
        self.false.code = 'True'
        self.assertEqual(self.nfalse.evaluate(), False)

    def test_forced_call(self):
        self.assertEqual(self.ntrue.evaluate(True), False)
        self.assertEqual(self.nfalse.evaluate(True), True)


# ################################################################


class AndTests(unittest.TestCase):
    def setUp(self):
        self.true = SequenceCondition('True')
        self.false = SequenceCondition('False')
        self.undef = SequenceSometimes(SequenceCondition('False'))

    def test_initial_call(self):
        self.assertEqual(SequenceAnd(self.true, self.true).evaluate(), True)
        self.assertEqual(SequenceAnd(self.true, self.false).evaluate(), False)
        self.assertEqual(SequenceAnd(self.true, self.undef).evaluate(), None)
        self.assertEqual(SequenceAnd(self.false, self.true).evaluate(), False)
        self.assertEqual(SequenceAnd(self.false, self.false).evaluate(), False)
        self.assertEqual(SequenceAnd(self.false, self.undef).evaluate(), False)
        self.assertEqual(SequenceAnd(self.undef, self.true).evaluate(), None)
        self.assertEqual(SequenceAnd(self.undef, self.false).evaluate(), False)
        self.assertEqual(SequenceAnd(self.undef, self.undef).evaluate(), None)

    def test_forced_call(self):
        self.assertEqual(SequenceAnd(self.true, self.true).evaluate(True), True)
        self.assertEqual(SequenceAnd(self.true, self.false).evaluate(True), False)
        self.assertEqual(SequenceAnd(self.false, self.true).evaluate(True), False)
        self.assertEqual(SequenceAnd(self.false, self.false).evaluate(True), False)


class OrTests(unittest.TestCase):
    def setUp(self):
        self.true = SequenceCondition('True')
        self.false = SequenceCondition('False')
        self.undef = SequenceSometimes(SequenceCondition('False'))

    def test_initial_call(self):
        self.assertEqual(SequenceOr(self.true, self.true).evaluate(), True)
        self.assertEqual(SequenceOr(self.true, self.false).evaluate(), True)
        self.assertEqual(SequenceOr(self.true, self.undef).evaluate(), True)
        self.assertEqual(SequenceOr(self.false, self.true).evaluate(), True)
        self.assertEqual(SequenceOr(self.false, self.false).evaluate(), False)
        self.assertEqual(SequenceOr(self.false, self.undef).evaluate(), None)
        self.assertEqual(SequenceOr(self.undef, self.true).evaluate(), True)
        self.assertEqual(SequenceOr(self.undef, self.false).evaluate(), None)
        self.assertEqual(SequenceOr(self.undef, self.undef).evaluate(), None)

    def test_forced_call(self):
        self.assertEqual(SequenceOr(self.true, self.true).evaluate(True), True)
        self.assertEqual(SequenceOr(self.true, self.false).evaluate(True), True)
        self.assertEqual(SequenceOr(self.false, self.true).evaluate(True), True)
        self.assertEqual(SequenceOr(self.false, self.false).evaluate(True), False)


class ThenTests(unittest.TestCase):
    def setUp(self):
        self.true = SequenceCondition('True')
        self.false = SequenceCondition('False')
        self.undef = SequenceSometimes(SequenceCondition('False'))

        self.tt = SequenceThen(self.true, self.true)
        self.tf = SequenceThen(self.true, self.false)
        self.tu = SequenceThen(self.true, self.undef)
        self.ft = SequenceThen(self.false, self.true)
        self.ff = SequenceThen(self.false, self.false)
        self.fu = SequenceThen(self.false, self.undef)
        self.ut = SequenceThen(self.undef, self.true)
        self.uf = SequenceThen(self.undef, self.false)
        self.uu = SequenceThen(self.undef, self.undef)

    def test_initial_call(self):
        self.assertEqual(self.tt.evaluate(), None)
        self.assertEqual(self.tf.evaluate(), None)
        self.assertEqual(self.tu.evaluate(), None)
        self.assertEqual(self.ft.evaluate(), None)
        self.assertEqual(self.ff.evaluate(), None)
        self.assertEqual(self.fu.evaluate(), None)
        self.assertEqual(self.ut.evaluate(), None)
        self.assertEqual(self.uf.evaluate(), None)
        self.assertEqual(self.uu.evaluate(), None)

    def test_second_call(self):
        self.tt.evaluate()
        self.tf.evaluate()
        self.tu.evaluate()
        self.ft.evaluate()
        self.ff.evaluate()
        self.fu.evaluate()
        self.ut.evaluate()
        self.uf.evaluate()
        self.uu.evaluate()

        self.assertEqual(self.tt.evaluate(), True)
        self.assertEqual(self.tf.evaluate(), False)
        self.assertEqual(self.tu.evaluate(), None)
        self.assertEqual(self.ft.evaluate(), None)
        self.assertEqual(self.ff.evaluate(), None)
        self.assertEqual(self.fu.evaluate(), None)
        self.assertEqual(self.ut.evaluate(), None)
        self.assertEqual(self.uf.evaluate(), None)
        self.assertEqual(self.uu.evaluate(), None)

    def test_initial_forced_call(self):
        self.assertEqual(self.tt.evaluate(True), False)
        self.assertEqual(self.tf.evaluate(True), False)
        self.assertEqual(self.tu.evaluate(True), False)
        self.assertEqual(self.ft.evaluate(True), False)
        self.assertEqual(self.ff.evaluate(True), False)
        self.assertEqual(self.fu.evaluate(True), False)
        self.assertEqual(self.ut.evaluate(True), False)
        self.assertEqual(self.uf.evaluate(True), False)
        self.assertEqual(self.uu.evaluate(True), False)

    def test_second_forced_call(self):
        self.tt.evaluate()
        self.tf.evaluate()
        self.ft.evaluate()
        self.ff.evaluate()

        self.assertEqual(self.tt.evaluate(True), True)
        self.assertEqual(self.tf.evaluate(True), False)
        self.assertEqual(self.ft.evaluate(True), False)
        self.assertEqual(self.ff.evaluate(True), False)

    def test_delayed_condition(self):
        tf_t = SequenceThen(SequenceTimedCondition(True, False, False), self.true)
        tf_f = SequenceThen(SequenceTimedCondition(True, False, False), self.false)
        ft_t = SequenceThen(SequenceTimedCondition(False, True, True), self.true)
        ft_f = SequenceThen(SequenceTimedCondition(False, True, True), self.false)

        self.assertEqual(tf_t.evaluate(), None)
        self.assertEqual(tf_f.evaluate(), None)
        self.assertEqual(ft_t.evaluate(), None)
        self.assertEqual(ft_f.evaluate(), None)

        self.assertEqual(tf_t.evaluate(), True)
        self.assertEqual(tf_f.evaluate(), False)
        self.assertEqual(ft_t.evaluate(), None)
        self.assertEqual(ft_f.evaluate(), None)

        self.assertEqual(tf_t.evaluate(), True)
        self.assertEqual(tf_f.evaluate(), False)
        self.assertEqual(ft_t.evaluate(), True)
        self.assertEqual(ft_f.evaluate(), False)


class BuilderTests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(build_sequence('success'), SequenceSuccess())
        self.assertEqual(build_sequence('failure'), SequenceFailure())

    def test_atom(self):
        self.assertEqual(build_sequence('"True"'), SequenceSometimes(SequenceCondition('True')))
        self.assertEqual(build_sequence('never "True"'), SequenceNever(SequenceSometimes(SequenceCondition('True'))))

    def test_binary(self):
        mapping = {
            'and': SequenceAnd,
            'or': SequenceOr,
            '->': SequenceThen
        }

        for operator, func in mapping.items():
            with self.subTest(operator=operator):
                self.assertEqual(build_sequence('"True" %s "False"' % operator),
                                 func(SequenceSometimes(SequenceCondition('True')), SequenceSometimes(SequenceCondition('False'))))

    def test_operator_priority(self):
        codes = [
            ('never never success', 'never (never success)'),
            ('never success and failure', '(never success) and failure'),
            ('success and never failure', 'success and (never failure)'),

            ('success and success or success', '(success and success) or success'),
            ('success or success and success', 'success or (success and success)'),

            ('success or success -> success', '(success or success) -> success'),
            ('success -> success or success', 'success -> (success or success)'),

            ('success -> failure -> success', '(success -> failure) -> success'),
            ('success and failure and success', '(success and failure) and success'),
            ('success or failure or success', '(success or failure) or success'),
        ]

        for code_a, code_b in codes:
            with self.subTest(code_a=code_a, code_b=code_b):
                self.assertEqual(build_sequence(code_a), build_sequence(code_b))

    def test_invalid_code(self):
        codes = [
            '',
            'a',
            '"True\'',
            'success never success',
            'success andsuccess',
            'success (and success)',
            '()',
            '() and ()',
        ]
        for code in codes:
            with self.subTest(code=code):
                with self.assertRaises(StatechartError):
                    build_sequence(code)
