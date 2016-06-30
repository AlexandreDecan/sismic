from functools import reduce, partial
from sismic.exceptions import StatechartError

import abc
import pyparsing  # type: ignore
from typing import Callable, Optional, List


class Sequence(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def evaluate(self, force=False) -> Optional[bool]:
        raise NotImplementedError()

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class SequenceItem(Sequence):
    def __eq__(self, other):
        return self.__class__ == other.__class__


class SequenceUnaryOperator(Sequence):
    def __init__(self, sequence: Sequence) -> None:
        self._sequence = sequence

    @property
    def sequence(self):
        return self._sequence

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.sequence)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.sequence == other.sequence


class SequenceBinaryOperator(Sequence):
    def __init__(self, left_sequence: Sequence, right_sequence: Sequence) -> None:
        self._left = left_sequence
        self._right = right_sequence

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    def __repr__(self):
        return '%s(%s, %s)' % (self.__class__.__name__, self.left, self.right)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.left == other.left and self.right == other.right


# ################################################################


class SequenceCondition(SequenceItem):
    def __init__(self, code: str, eval_func: Callable[[str], bool]=None) -> None:
        super().__init__()
        self.code = code
        self._eval_func = eval_func if eval_func else eval

    def evaluate(self, force=False):
        return self._eval_func(self.code)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.code)

    def __eq__(self, other):
        return super().__eq__(other) and self.code == other.code


class SequenceTimedCondition(SequenceItem):
    def __init__(self, *truth: List[bool]) -> None:
        super().__init__()
        self._truth = (t for t in truth)

    def evaluate(self, force=False):
        return next(self._truth)


class SequenceSuccess(SequenceItem):
    def evaluate(self, force=False):
        return True


class SequenceFailure(SequenceItem):
    def evaluate(self, force=False):
        return False


class SequenceFinish(SequenceItem):
    def evaluate(self, force=False):
        return force


# ################################################################


class SequenceSometimes(SequenceUnaryOperator):
    def __init__(self, sequence: Sequence) -> None:
        super().__init__(sequence)
        self._satisfied = False

    def evaluate(self, force=False):
        if not self._satisfied:
            if self.sequence.evaluate(force) is True:
                self._satisfied = True

        if self._satisfied:
            return True
        else:
            return False if force else None


class SequenceNegate(SequenceUnaryOperator):
    def evaluate(self, force=False):
        sequence = self.sequence.evaluate(force)
        return None if sequence is None else not sequence


class SequenceAlways(SequenceUnaryOperator):
    def __init__(self, sequence: Sequence) -> None:
        super().__init__(sequence)
        self._unsatisfied = False

    def evaluate(self, force=False):
        if not self._unsatisfied:
            sequence = self.sequence.evaluate(force)
            if sequence is False or sequence is None:
                self._unsatisfied = True

        if self._unsatisfied:
            return False
        else:
            return True if force else None


class SequenceNever(SequenceUnaryOperator):
    def __init__(self, sequence: Sequence) -> None:
        super().__init__(sequence)
        self._satisfied = False

    def evaluate(self, force=False):
        if not self._satisfied:
            sequence = self.sequence.evaluate(force)
            if sequence is True:
                self._satisfied = True

        if self._satisfied:
            return False
        else:
            return True if force else None


# ################################################################


class SequenceAnd(SequenceBinaryOperator):
    def evaluate(self, force=False):
        left = self.left.evaluate(force)
        right = self.right.evaluate(force)

        if left is False or right is False:
            return False
        elif left is True and right is True:
            return True
        else:
            return None


class SequenceOr(SequenceBinaryOperator):
    def evaluate(self, force=False):
        left = self.left.evaluate(force)
        right = self.right.evaluate(force)

        if left is True or right is True:
            return True
        elif left is False and right is False:
            return False
        else:
            return None


class SequenceThen(SequenceBinaryOperator):
    def __init__(self, left_sequence: Sequence, right_sequence: Sequence) -> None:
        super().__init__(left_sequence, right_sequence)
        self._left_satisfied = False

    def evaluate(self, force=False):
        if self._left_satisfied:
            return self.right.evaluate(force)
        else:
            self._left_satisfied = self.left.evaluate(force)
            return False if force else None


def build_sequence(expression: str, evaluation_function: Callable[[str], bool]=eval) -> Sequence:
    """
    Parse an expression and return the corresponding sequence according to the following mini-language:

     - atom:
         - "code" or 'code': a fragment of code (e.g. Python code) representing a Boolean expression that
           evaluates to true or false. The semantics is "satisfied once": as soon as the code evaluates to true once,
           the truth value of the expression remains true. This is equivalent as "sometimes 'code'" in linear
           temporal logic.
     - constants:
         - failure: this constant always evaluates to false.
         - success: this constant always evaluates to true.
     - unary operators:
         - never A: this expression evaluates to false as soon as expression A evaluates to true.
     - binary operators:
         - A and B: logical and
         - A or B: logical or
         - A -> B: this is equivalent to "(next always B) since A" in linear temporal logic, i.e. B has to be true
           (strictly) since A holds. Notice that, due to the "satisfied once" semantics of the atoms, if A and B are
           atoms, this is merely equivalent to "(A and next (sometimes B))", which means A needs to be true strictly
           before B or, in other words, A must be satisfied once, then B must be holds once.

    Keywords are case-insensitive. Parentheses can be used to group sub expressions.
    Unary operators have precedence over binary ones (e.g. "A and never B" is equivalent to "A and (never B)").
    Unary operators are right associative while binary operators are left associative (e.g. "A and B and C" is
    equivalent to "(A and B) and C").
    The binary operators are listed in decreasing priority (e.g. "A or B and C" is equivalent to "A or (B and C)",
    and "A and B -> C or D" is equivalent to "(A and B) -> (C or D)").

    Examples (assuming that expressions between quotes can be evaluated to true or false):

     - "put water" -> "put coffee": ensures water is put before coffee.
     - "put water" and "put coffee": ensures water and coffee are put. Due to the "satisfied once" semantics of the
       atoms, the order in which items are put does not matter.
     - (never "put water") or ("put water" -> "put coffee"): if water is put, then coffee must be put too.
     - never ("put water" -> "put water"): the condition will fail if water is put twice (but will succeed if water
       is put once or never put).
     - "put water" -> (never "put water"): put water exactly once.

    :param expression: an expression to parse
    :param evaluation_function: the function that will be called to evaluate nested pieces of code
    :return: a *Sequence* instance.
    """
    def unary_operator(func, term):
        term = term[0]
        return func(term[0])

    def binary_operator(func, term):
        term = term[0]
        return reduce(func, term[1:], term[0])

    condition = pyparsing.quotedString().setParseAction(
        lambda s, l, t: SequenceSometimes(SequenceCondition(t[0][1:-1], evaluation_function))
    )

    constants = (
        pyparsing.CaselessKeyword('failure').setParseAction(SequenceFailure) |
        pyparsing.CaselessKeyword('success').setParseAction(SequenceSuccess)
    )

    unary_ops = [(pyparsing.CaselessKeyword(keyword).suppress(), 1, pyparsing.opAssoc.RIGHT,
                  partial(unary_operator, func)) for keyword, func in [
        ('never', SequenceNever),
    ]]

    binary_ops = [(pyparsing.CaselessKeyword(keyword).suppress(), 2, pyparsing.opAssoc.LEFT,
                   partial(binary_operator, func)) for keyword, func in [
        ('and', SequenceAnd),
        ('or', SequenceOr),
        ('->', SequenceThen),
    ]]

    operands = (constants | condition)
    expr = pyparsing.operatorPrecedence(operands, unary_ops + binary_ops)

    try:
        return expr.parseString(expression, parseAll=True)[0]
    except pyparsing.ParseBaseException as e:
        raise StatechartError('Invalid sequential condition:\n%s' % expression) from e