import sys
import unittest
import random
import string
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.utils.fsbst import FixSizeBST


def randomword(length=5):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))

class TestFlowStorage(unittest.TestCase):
    def setUp(self):
        self.items_number = np.random.randint(4, 40)
        self.values = [randomword() for _ in range(self.items_number)]
        self.keys = [randomword() for _ in range(self.items_number)]
        self.t = FixSizeBST(self.items_number)
        for key, value in zip(self.keys, self.values):
            self.t.add_new_node(key, value)

    def test_size(self):
        self.t.add_new_node(randomword(), randomword())
        self.assertEquals(self.items_number, len(self.t.keys()))

    def test_push_object(self):
        items = [(key, value) for key, value in zip(self.keys, self.values)]
        print(items)
        np.random.shuffle(items)
        finding_items, oldest_items  = items[:-1], items[-1]
        for _ in range(1000):
            np.random.shuffle(finding_items)
            for key, value in finding_items:
                self.t.get_value(key)
                self.assertEquals((key, value), self.t.items()[0])

        print(oldest_items)
        print(self.t.items())
        self.assertTrue(oldest_items in self.t.items()[-8:])
