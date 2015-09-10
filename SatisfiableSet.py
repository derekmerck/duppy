# Given a set of conditions on variables, see if a set of variables satisfies it,
# or could satisfy it.   hhjhk

import warnings
import logging
from collections import deque


class VariableType(object):

    def __init__(self, **kwargs):
        super(VariableType, self).__init__()
        # Basically decorators for outputs
        self.name  = kwargs.get('name', 'var')
        self.units = kwargs.get('units', 'arbs')
        self.dtype = kwargs.get('dtype', 'float')

    def __repr__(self):
        return '<ss:var: %s>' % self.name


class TypedValue(object):

    def __init__(self, variable, value, history_len=0, prediction_func=None):
        self.variable = variable
        self.value = value
        self.history = deque(maxlen=history_len)
        self.prediction_func = prediction_func

    @property
    def value(self):
        return self.history[0]

    @value.setter
    def value(self, _value):
        self.history.push(_value)

    def predict(self, range):
        if self.prediction_func:
            return self.prediction_func(self.history, range)
        else:
            return self.value

    def __eq__(self, other):
        # Only one instance of a var allowed in the set
        return self.variable.name == other.variable.name

    def __hash__(self):
        # Only one instance of a var allowed in the set
        return hash(self.variable)

    def __repr__(self):
        return '<ss:tv: %s=%g>' % (self.variable.name, self.value)


class TypedCondition(object):

    def __init__(self, variable, operator, value, value1=None, prediction_range=None):
        self.variable = variable
        self.value = value
        self.value1 = value1
        self.operator = operator
        self.prediction_range = prediction_range

    def satisfied_by_any(self, typed_value_set):
        for typed_value in typed_value_set.typed_values:
            if self.comparable(typed_value):
                if self.satisfied_by(typed_value):
                    return True
        return False

    def not_satisfied_by_any(self, typed_value_set):
        for typed_value in typed_value_set.typed_values:
            if self.comparable(typed_value):
                if not self.satisfied_by(typed_value):
                    return True
        return False

    def comparable(self, typed_value):
        if typed_value.variable.name != self.variable.name:
            # logging.debug('%s IS NOT comparable to %s' % (self.variable.name, typed_value.variable.name))
            return False
        else:
            # logging.debug('%s IS comparable to %s' % (self.variable.name, typed_value.variable.name))
            return True

    def satisfied_by(self, typed_value):

        if not self.comparable(typed_value):
            # Tried an improper comparison
            err = 'Improper comparison of %s with %s' % (typed_value.variable.name, self.variable.name)
            warnings.warn(err)
            return False

        if self.operator == 'GT':
            return typed_value.value > self.value
        elif self.operator == 'GTE':
            return typed_value.value >= self.value
        elif self.operator == 'LT':
            return typed_value.value < self.value
        elif self.operator == 'LTE':
            return typed_value.value <= self.value
        elif self.operator == 'EQ':
            return typed_value.value == self.value
        elif self.operator == 'NEQ':
            return typed_value.value != self.value
        elif self.operator == 'IN':
            return self.value < typed_value.value < self.value1
        elif self.operator == 'TLT':  # Trending less than
            return self.value < typed_value.predict(self.prediction_range)
        elif self.operator == 'TGT':  # Trending greater than
            return self.value > typed_value.predict(self.prediction_range)
        else:
            warnings.warn('No operation defined for %s' % self.operator)
            return False

    def __repr__(self):
        if self.operator == 'GT':
            return '<ss:tc: %s>%g>' % (self.variable.name, self.value)
        elif self.operator == 'GTE':
            return '<ss:tc: %s>=%g>' % (self.variable.name, self.value)
        elif self.operator == 'LT':
            return '<ss:tc: %s<%g>' % (self.variable.name, self.value)
        elif self.operator == 'LTE':
            return '<ss:tc: %s<=%g>' % (self.variable.name, self.value)
        elif self.operator == 'EQ':
            return '<ss:tc: %s==%g>' % (self.variable.name, self.value)
        elif self.operator == 'NEQ':
            return '<ss:tc: %s!=%g>' % (self.variable.name, self.value)
        elif self.operator == 'IN':
            return '<ss:tc: %g<%s<%g>' % (self.value, self.variable.name, self.value1)
        elif self.operator == 'TLT':
            return '<ss:tc: %s..<%g>' % (self.variable.name, self.value)
        elif self.operator == 'TGT':
            return '<ss:tc: %g..>%g>' % (self.variable.name, self.value)
        else:
            warnings.warn('No operation defined for %s' % self.operator)


class TypedValueSet(object):
    # TODO: Need unique typed values ...

    def __init__(self, items=[]):
        self.typed_values = items


class TypedConditionSet(object):
    # TODO: Need unique typed conditions ...

    def __init__(self, items=[]):
        self.typed_conditions = items

    def satisfied_by(self, typed_value_set):
        for condition in self.typed_conditions:
            if not condition.satisfied_by_any(typed_value_set):
                logging.debug('Failed on %s' % condition)
                return False
        return True

    def satisfiable_by(self, typed_value_set):
        for condition in self.typed_conditions:
            if condition.not_satisfied_by_any(typed_value_set):
                return False
        return True


def test_satset():

    logger = logging.getLogger(__name__)

    dog_b = VariableType(name='has dog',                       dtype='boolean')
    cat_f = VariableType(name='cat fraction', units='percent', dtype='float')
    ape_i = VariableType(name='monkey count', units='barrels', dtype='int')

    dog_0b   = TypedValue(dog_b,  False)
    dog_1b   = TypedValue(dog_b,  True)
    cat_n10f = TypedValue(cat_f, -10)
    cat_10f  = TypedValue(cat_f,  10)
    ape_n10i = TypedValue(ape_i, -10)
    ape_10i  = TypedValue(ape_i,  10)

    logger.debug(dog_0b)
    logger.debug(cat_n10f)
    logger.debug(ape_n10i)

    dog_eq_1     = TypedCondition(dog_b, 'EQ', True)
    cat_in_n20_0 = TypedCondition(cat_f, 'IN', -20, 0)
    ape_gt_0     = TypedCondition(ape_i, 'GT', 50)

    logger.debug(dog_eq_1)
    logger.debug(cat_in_n20_0)

    logger.debug(dog_eq_1.satisfied_by(dog_1b))
    assert(dog_eq_1.satisfied_by(dog_1b) is True)
    logger.debug(dog_eq_1.satisfied_by(dog_0b))
    assert(dog_eq_1.satisfied_by(dog_0b) is False)

    U = TypedValueSet([dog_1b, cat_n10f])
    A = TypedConditionSet([dog_eq_1, cat_in_n20_0])

    logger.debug(U)
    logger.debug(A)

    logger.debug(A.satisfiable_by(U))
    assert(A.satisfiable_by(U) is True)
    logger.debug(A.satisfied_by(U))
    assert(A.satisfied_by(U) is True)

    A.typed_conditions.append(ape_gt_0)
    logger.debug(A.satisfiable_by(U))
    assert(A.satisfiable_by(U) is True)
    logger.debug(A.satisfied_by(U))
    assert(A.satisfied_by(U) is False)

    U.typed_values.append(ape_n10i)
    logger.debug(A.satisfiable_by(U))
    assert(A.satisfiable_by(U) is False)
    logger.debug(A.satisfied_by(U))
    assert(A.satisfied_by(U) is False)


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    test_satset()

