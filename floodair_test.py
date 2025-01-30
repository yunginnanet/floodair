import unittest
import ranger


class TestRange(unittest.TestCase):
    def test_range_init(self):
        r = ranger.Range(1, 55, 0.1, ranger.RangeMode.STOP)
        self.assertEqual(1, r._start)
        self.assertEqual(55, r._end)
        self.assertEqual(0.1, r._delta)
        self.assertEqual(0.9, r._index)
        self.assertEqual(ranger.RangeMode.STOP, r.mode)
        r.resume()
        self.assertEqual(ranger.RangeMode.STATIC, r.mode)

    def test_range_sequence_stop_and_resume(self):
        r = ranger.Range(1, 55, 0.1, ranger.RangeMode.SEQUENCE)
        self.assertEqual(r.next(), 1)
        r.stop()
        with self.assertRaises(StopIteration):
            r.__next__()
            r.resume()
            self.assertEqual(r.next(), 1.1)

    def test_range_maxiter(self):
        r = ranger.Range(1, 55, 0.1, ranger.RangeMode.SEQUENCE, 10)
        for i in range(0, 10):
            n = r.next()
            if i == 0:
                self.assertEqual(1, n)
                continue
            self.assertAlmostEqual((float(1.0) + float(0.1 * i)), n)
        with self.assertRaises(StopIteration):
            r.next()
        self.assertAlmostEqual(1.0, r.spin())
        self.assertAlmostEqual(1.1, r.spin())
        self.assertAlmostEqual(1.2, r.next())

    def test_range_sequence(self):
        r = ranger.Range(1, 55)
        for i in range(1, 55):
            n = r.next()
            self.assertEqual(i, n)
        self.assertEqual(54, r._index)
        r.stop()
        self.assertEqual(54, r._index)
        r.reset(None, None, 0.1)
        self.assertEqual(r._index, r._start - r._delta)
        for i in range(0, 10):
            n = r.next()
            if i == 0:
                self.assertEqual(1, n)
                continue
            self.assertAlmostEqual((float(1.0) + float(0.1 * i)), n)

    def test_range_random(self):
        r = ranger.Range(1, 55, 0.1, ranger.RangeMode.RANDOM)
        for i in range(1, 55):
            n = r.next()
            self.assertTrue(1 <= n <= 55)
        r.reset(None, 256.55)
        for i in range(1, 55):
            n = r.next()
            self.assertTrue(1 <= n <= 256.55)

    def test_range_sequence_static(self):
        r = ranger.Range(1, None, None, ranger.RangeMode.STATIC, -1)
        for i in range(1, 55):
            self.assertEqual(1, r.next())

    def test_range_iterable(self):
        r = ranger.Range(1, 55, 0.1, ranger.RangeMode.STATIC, 100)
        ct=0
        for i in r:
            ct+=1
            self.assertEqual(1, i)

        if ct != 100:
            self.fail("Expected 100 iterations, got %d" % ct)


class TestRanger(unittest.TestCase):
   def test_ranger_iterable(self):
        r = ranger.Ranger("1-10_0.5,5,0.r:1-1.0")

        for _ in range(0, 30):
            ct = 0
            for i in r:
                ct += 1
                print(i)
                self.assertTrue(1 <= i <= 10 or i == 5 or 0.1 <= i <= 1.0)

            if ct != 30:
                self.fail("Expected 30 iterations, got %d" % ct)

if __name__ == '__main__':
    unittest.main()