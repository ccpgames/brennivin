import os
import time
import unittest

from brennivin import itertoolsext, osutils, testhelpers as th


class TestAssertNumbersEqual(unittest.TestCase):
    def testDifferenceRaises(self):
        """Test that a difference more than tolerance asserts."""
        self.assertRaises(AssertionError, th.assertNumbersEqual, self, 0, 2, 1)

    def testDifferenceEqualToToleranceIsEqual(self):
        """Test that a difference equal to the tolerance does not assert."""
        th.assertNumbersEqual(self, 0, 1, 1)


class TestAssertBetween(unittest.TestCase):

    def testTrue(self):
        th.assertBetween(self, 1, 2, 3)
        th.assertBetween(self, 1, 1, 3, True)
        th.assertBetween(self, 1, 3, 3, True)

    def testFalse(self):
        def assertNotBtw(*args, **kwargs):
            self.assertRaises(AssertionError,
                              th.assertBetween, self, *args, **kwargs)
        assertNotBtw(1, 1, 3)
        assertNotBtw(1, 3, 3)
        assertNotBtw(1, 4, 3)


class TestAssertFloatsSeqEqual(unittest.TestCase):
    def testBasic(self):
        """Test that two identical sequences do not assert."""
        a = (0, 0, 0)
        b = (0, 0, 0)
        th.assertNumberSequencesEqual(self, a, b)

    def testDifferenceLessThanTolerance(self):
        """Test that an element off by less than tolerance does not assert."""
        a = (0.0, 0.0, 0.0)
        b = (1e-10, 0.0, 0.0)
        th.assertNumberSequencesEqual(self, a, b, 0.0000000001)

    def testAssertDifferenceMoreThanTolerance(self):
        """Test that an element off by more than tolerance asserts."""
        a = (0, 0, 0)
        b = (2, 0, 0)
        self.assertRaises(AssertionError,
                          th.assertNumberSequencesEqual, self, a, b, 1)

    def testDifferenceLengths(self):
        """Test that sequences of different lengths asserts."""
        a = (0, 0)
        b = (0, 0, 0)

        def assertRaise(x, y):
            self.assertRaises(AssertionError,
                              th.assertNumberSequencesEqual, self, x, y)
        assertRaise(a, b)
        assertRaise(b, a)


class AssertStartsAndEndsWithTests(unittest.TestCase):

    def testStarts(self):
        s = 'abcd'
        th.assertStartsWith(s, 'ab')
        with self.assertRaises(AssertionError):
            th.assertStartsWith(s, 'b')

    def testEnds(self):
        s = 'abcd'
        th.assertEndsWith(s, 'cd')
        with self.assertRaises(AssertionError):
            th.assertStartsWith(s, 'c')


class TestAssertPermissionbitsEqual(unittest.TestCase):

    def setUp(self):
        self._files = []

    def CreateFile(self, readonlystate):
        p = osutils.mktemp('readonlystate_%s' % readonlystate)
        osutils.set_readonly(p, readonlystate)
        self._files.append(p)
        return p

    def testIdentical(self):
        a = self.CreateFile(True)
        b = self.CreateFile(True)
        th.assertPermissionbitsEqual(self, a, b)

    def testDifferentAsserts(self):
        a = self.CreateFile(False)
        b = self.CreateFile(True)
        self.assertRaises(AssertionError,
                          th.assertPermissionbitsEqual, self, a, b)

    def tearDown(self):
        map(lambda p: osutils.set_readonly(p, False), self._files)
        map(os.remove, self._files)


class TestTimeMock(unittest.TestCase):

    def testPatchesAndUnpatched(self):
        getall = lambda: [getattr(time, a) for a in th.patch_time.ATTRS]
        orig = getall()
        with th.patch_time():
            self.assertNotEqual(orig, getall())
        self.assertEqual(orig, getall())

    def testSystem(self):
        with th.patch_time(starttime=100):
            self.assertEqual(time.time(), 100)
            self.assertEqual(time.clock(), 0)
            time.sleep(2)
            self.assertEqual(time.time(), 102)
            self.assertEqual(time.clock(), 2)


class TestMonkeyPatcher(unittest.TestCase):

    def testPatchesAndUnpatches(self):
        o = itertoolsext.Bundle(a=1)
        mp = th.Patcher(o, 'a', 2)
        self.assertEqual(o.a, 1)
        mp.__enter__()
        self.assertEqual(o.a, 2)
        mp.__exit__()
        self.assertEqual(o.a, 1)

    def testCanOnlyBeEnteredOnce(self):
        o = itertoolsext.Bundle(a=1)
        mp = th.Patcher(o, 'a', 1)
        mp.__enter__()
        self.assertRaises(RuntimeError, mp.__enter__)


class TestXmlCompare(unittest.TestCase):

    def testNotEqual(self):
        a = '<root><a></a></root>'
        b = '<root><b></b></root>'
        self.assertRaises(AssertionError, th.assertXmlEqual, a, b)

    def testEqual(self):
        a = '<root />'
        b = '<root>\n</root>'
        th.assertXmlEqual(a, b)


class CallCounterTests(unittest.TestCase):

    def test_no_params(self):
        c = th.CallCounter.no_params()
        c()
        c()
        self.assertEqual(c.count, 2)
        with self.assertRaises(TypeError):
            c(1)

    def test_all_params(self):
        c = th.CallCounter.all_params()
        self.assertEqual(1, c(1))
        c()
        c(hi=1)
        self.assertEqual(c.count, 3)
