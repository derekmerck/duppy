# Given a set of conditions on variables, see if a set of variables satisfies it,
# or could satisfy it.

import warnings
import logging
from collections import deque


class VariableType(object):

    # Need a list of generated variables, so we only create a new one if neccesary

    _dict = dict()

    def __init__(self, **kwargs):
        super(VariableType, self).__init__()
        # Basically decorators for outputs
        self.name  = kwargs.get('name',  'var')
        self.units = kwargs.get('units', 'arbs')
        self.dtype = kwargs.get('dtype', 'float')
        VariableType._dict[self.name] = self

    # This is somewhat bad practice b/c it will re-init every time, but it's easy to implement
    # and the side effect is irrelevant in this context
    def __new__(cls, **kwargs):
        name = kwargs.get('name')
        if VariableType._dict.get(name):
            return VariableType._dict[name]
        else:
            return super(VariableType, cls).__new__(cls)

    def __repr__(self):
        return '<ss:var: %s>' % self.name


class TypedValue(object):

    def __init__(self, variable, value):
        if isinstance(variable, basestring):
            # It's just a name
            variable = VariableType(name=variable)
        self.variable = variable
        self.value = value
        # self.history = deque(maxlen=history_len)
        # self.prediction_func = prediction_func

    # @property
    # def value(self):
    #     return self.history[0]
    #
    # @value.setter
    # def value(self, _value):
    #     self.history.push(_value)
    #
    # def predict(self, range):
    #     if self.prediction_func:
    #         return self.prediction_func(self.history, range)
    #     else:
    #         return self.value

    def __eq__(self, other):
        # Only one instance of a var allowed in the set
        return self.variable.name == other.variable.name

    def __hash__(self):
        # Only one instance of a var allowed in a set
        return hash(self.variable)

    def __repr__(self):
        return '<ss:tv: %s=%g>' % (self.variable.name, self.value)


class TypedCondition(object):

    def __init__(self, variable, operator, value, value1=None):
        if isinstance(variable, basestring):
            # It's just a name
            variable = VariableType(name=variable)
        self.variable = variable
        self.value = value
        self.value1 = value1
        self.operator = operator
        # self.prediction_range = prediction_range

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

    def __init__(self, items={}):
        self.typed_values = []
        for variable, value in items.iteritems():
            item = TypedValue(variable, value)
            self.typed_values.append(item)

    def __repr__(self):
        return repr(self.typed_values)


class TypedConditionSet(object):
    def __init__(self, items={}):
        self.typed_conditions = []
        for variable, condition in items.iteritems():
            item = TypedCondition(variable, *condition)
            self.typed_conditions.append(item)

    def satisfied_by(self, typed_value_set):
        for condition in self.typed_conditions:
            if not condition.satisfied_by_any(typed_value_set):
                # logging.debug('Failed on %s' % condition)
                return False
        return True

    def satisfiable_by(self, typed_value_set):
        for condition in self.typed_conditions:
            if condition.not_satisfied_by_any(typed_value_set):
                return False
        return True

    def __repr__(self):
        return repr(self.typed_conditions)

# Can extend this to "rules" by subclassing TypedConditionSet and adding priority, etc.
class OrderedConditionSets(object):

    def __init__(self, conditions=None):

        self.condition_sets = []
        if conditions:
            for c in conditions:
                self.append(c)

    def append(self, c):
            if not isinstance(c, TypedConditionSet):
                c = TypedConditionSet(c)
            self.condition_sets.append(c)

    def match_condition_set(self, values):
        if not isinstance(values, TypedValueSet):
            values = TypedValueSet(values)

        for condition_set in self.condition_sets:
            if condition_set.satisfied_by(values):
                # logging.debug('Satisfied by {0}'.format(condition_set))
                return condition_set


def test_ordered_conditions():

    S = OrderedConditionSets([{'x': ('GT', 10),   #Rule 1
                              'y': ('LT', 5) },
                             {'x': ('EQ', 7) }]) # Rule 2

    v = TypedValueSet({'x': 7})

    S.match_condition_set(v)

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


def test_simple_satset():
    pass

    c0 = TypedConditionSet({'x': ('GT', 10),
                            'y': ('LT', 5) } )

    c1 = TypedConditionSet( {'x': ('EQ', 7) } )

    v0 = TypedValueSet({'x': 7})
    v1 = TypedValueSet({'x': 12, 'y': 0})

    logging.debug(c0)
    logging.debug(c1)
    logging.debug(v0)
    logging.debug(v1)

    logging.debug(c0.satisfied_by(v0))
    logging.debug(c0.satisfied_by(v1))
    logging.debug(c0.satisfiable_by(v0))
    logging.debug(c0.satisfiable_by(v1))
    logging.debug(c1.satisfied_by(v0))
    logging.debug(c1.satisfied_by(v0))
    logging.debug(c1.satisfiable_by(v0))
    logging.debug(c1.satisfiable_by(v1))


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    test_ordered_conditions()

