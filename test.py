import unittest


class AidaTest(unittest.TestCase):
    def setUp(self):
        import psutil
        for p in psutil.process_iter():
            if 'aida' in p.name().lower():
                return
        raise AssertionError('Aida64 is not running')

    def test(self):
        import python_aida64
        data = python_aida64.getData()
        self.assertIsInstance(data, dict)
        self.assertIn('sys', data)
        self.assertIsInstance(data['sys'], list)
        self.assertNotEqual(len(data['sys']), 0)
        self.assertIsInstance(data['sys'][0], dict)


if __name__ == "__main__":
    unittest.main()
