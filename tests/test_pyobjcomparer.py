import unittest

from brennivin.pyobjcomparer import compare, get_compound_diff, assert_compare


def make1(f=0.000000001):
    return [1,
            {},
            {'a': [1, 2, 3],
             'b': {'1': 1}},
            1.1 + 0.01,
            f]


def make2():
    return range(6)


class sphere(object):
    def __init__(self, radius=1.0, translation=(0.0, 0.0, 0.0)):
        self.radius = radius
        self.translation = translation

    def __eq__(self, other):
        return (
            type(self) == type(other) and
            self.radius == other.radius and
            self.translation == other.translation)

    def __ne__(self, other):
        return not self.__eq__(other)


class TestComparer(unittest.TestCase):
    def assertCompare(self, val, eq, neq):
        self.assertTrue(compare(val, eq))
        self.assertFalse(compare(val, neq))

    def testEq(self):
        self.assertCompare(make1(), make1(0.0000000011), make2())

    def testStringEq(self):
        self.assertCompare('a', 'a', 'b')

    def testIntEq(self):
        self.assertCompare(1, 1, 2)

    def testFloatEq(self):
        a = 0.000000001
        b = 0.0000000001
        c = 0.001
        self.assertCompare(a, b, c)

    def testTupleEq(self):
        a = 1328, 839, 1389
        b = 1328, 839, 1389
        c = 1000, 839, 1389
        self.assertCompare(a, b, c)
        self.assertCompare(a, b, list(a))

    def testListEq(self):
        a = [1, 2, 3, 4]
        b = [1, 2, 3, 4]
        c = [1, 2, 3, 65]
        self.assertCompare(a, b, c)
        self.assertCompare(a, b, tuple(c))

    def testSetEq(self):
        a = set([1, 2, 3, 4])
        b = set([1, 2, 3, 4])
        c = set([1, 2, 3, 5])
        self.assertCompare(a, b, c)
        self.assertCompare(a, b, list(a))

    def testDictionaryEq(self):
        a = {'a': 1, 'b': 2, 'c': 1.00000}
        b = {'a': 1, 'b': 2, 'c': 1.00000}
        c = {'a': 1, 'b': 2, 'c': 1.01000}
        self.assertCompare(a, b, c)
        d = {'a': 1}
        self.assertCompare(a, b, d)

    def testIntVsFloat(self):
        self.assertTrue(compare(1.00, 1))

    def testDictVsList(self):
        a = {'a': 1, 'b': 2, 'c': 1.00000}
        b = [1, 2, 1.0000]
        self.assertFalse(compare(a, b))

    def testDictVsSet(self):
        a = {'a': 1, 'b': 2, 'c': 1.00000}
        b = set([1, 2, 3, 4])
        self.assertFalse(compare(a, b))

    def testObjectsEq(self):
        self.assertCompare(sphere(), sphere(), sphere(radius=0.0))

    def testTypeEq(self):
        self.assertCompare(int, int, str)

    def testMatrix(self):
        a = (257276184,
             [
                 [0, 0, -1, 0],
                 [0, 1, 0, 0],
                 [2, 0, 0, 0],
                 [10, 0, 0, 1]])
        b = (257276184,
             [
                 [2.2204460492503131e-16, 0.0, -1.0, 0.0],
                 [0.0, 1.0, 0.0, 0.0],
                 [2.0, 0.0, 4.4408920985006262e-16, 0.0],
                 [10.0, 0.0, 0.0, 1.0]])
        self.assertTrue(compare(a, b))

    def testObjVsDict(self):
        a = sphere()
        b = {'foo': 'bar'}
        self.assertFalse(compare(a, b))
        self.assertFalse(compare(b, a))


class TestGetCompoundDiff(unittest.TestCase):
    def assertBreadcrumb(self, ideal, result):
        self.assertEqual(ideal, result,
                         "Failed to create expected breadcrumbs.\n"
                         "Expected %s\n"
                         "Got:     %s" % (ideal, result))

    def testEmptyWhenEqual(self):
        a = {'value': 0}
        b = {'value': 0}
        result = get_compound_diff(a, b)
        self.assertBreadcrumb([], result)

    def testDict(self):
        a = {'type': 'Tr2Vector4Parameter',
             'value': [0, 0]}
        b = {'type': 'Tr2Vector4Parameter',
             'value': [0, 1]}
        result = get_compound_diff(a, b)
        self.assertBreadcrumb(['value', 1, '0 != 1'], result)

    def testList(self):
        a = [{'value': [0, 0]}, {'foo': 'bar'}]
        b = [{'value': [0, 1]}, {'foo': 'bar'}]
        result = get_compound_diff(a, b)
        self.assertBreadcrumb([0, 'value', 1, '0 != 1'], result)

    def testList2(self):
        self.assertBreadcrumb(
            [0, 2, '3 != 4'],
            get_compound_diff([[1, 2, 3]], [[1, 2, 4]]))

    def testNested(self):
        a = [{'first': [{'second': [{'third': [{'forth': 0}]}]}]}]
        b = [{'first': [{'second': [{'third': [{'forth': 1}]}]}]}]
        result = get_compound_diff(a, b)
        self.assertBreadcrumb(
            [0, 'first', 0, 'second', 0, 'third', 0, 'forth', '0 != 1'],
            result)

    def testItemType(self):
        a = [{'value': [0, '1']}]
        b = [{'value': [0, 1]}]
        result = get_compound_diff(a, b)
        self.assertBreadcrumb([0, 'value', 1, "'1' != 1"], result)

    def testSeqType(self):
        result = get_compound_diff([{}], [[]])
        self.assertBreadcrumb([0, 'list is not a dict'], result)

    def testListLen(self):
        self.assertBreadcrumb(
            [0, 'len neq (2 != 3): [1, 2] != [1, 2, 3]'],
            get_compound_diff([[1, 2]], [[1, 2, 3]]))

    def testDictLen(self):
        self.assertBreadcrumb(
            [0, "len neq (1 != 2): ['a'] != ['a', 'b']"],
            get_compound_diff([{'a': 1}], [{'a': 1, 'b': 2}]))

    def testMixed(self):
        a = sphere()
        b = {'foo': 'bar'}
        self.assertBreadcrumb(['%r != %r' % (a, b)], get_compound_diff(a, b))
        self.assertBreadcrumb(['sphere is not a dict'],
                              get_compound_diff(b, a))

    def testObjectReturnsNonemptyList(self):
        a = sphere()
        b = sphere(radius=0.0)
        result = get_compound_diff(a, b)
        self.assertBreadcrumb(['%r != %r' % (a, b)], result)

    def testData1(self):
        a = {'frames': [{'objects': [{'a': 1, 'b': 2}]}]}
        b = {'frames': [{'objects': [{'a': 1, 'b': 3}]}]}
        self.assertBreadcrumb(
            ['frames', 0, 'objects', 0, 'b', '2 != 3'],
            get_compound_diff(a, b))


class TestAssertCompare(unittest.TestCase):
    def testEqualityDoesNotRaise(self):
        assert_compare('a', 'a')

    def testRaiseOnInequality(self):
        with self.assertRaises(AssertionError):
            assert_compare('a', 'b')

    def _do_printobjs_test(self, doprint):
        a = [sphere()]
        b = [sphere(radius=10)]
        try:
            assert_compare(a, b, doprint)
            raise NotImplementedError()
        except AssertionError as ex:
            func = self.assertIn if doprint else self.assertNotIn
            func(str(a), ex.args[0])
            func(str(b), ex.args[0])

    def testPrintObjsFlagTrue(self):
        self._do_printobjs_test(True)

    def testPrintObjsFlagFalse(self):
        self._do_printobjs_test(False)
