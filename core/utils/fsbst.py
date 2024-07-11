import sys
from pathlib import Path
import hashlib

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.joinpath('third_party', 'pybst', 'pybst')))

from ..third_party.pybst.pybst.splaytree import SplayTree

class SaveKeyInfoNode:
    def __init__(self, key_info, value):
        self.key_info = key_info
        self.value = value

class FixSizeBST:
    def __init__(self, fix_size):
        self._fix_size = fix_size
        self._splay_tree = SplayTree()

    def _remove_oldest_element(self):
        oldest_node = self._splay_tree.levelorder()[-1]
        self._splay_tree.delete(oldest_node.key)

    def _sha256_hash(self, data):
        return int(hashlib.sha256(data.encode()).hexdigest(), 16)

    def add_new_node(self, key_info, value):
        key = self._sha256_hash(key_info)
        if self._splay_tree.get_element_count() >= self._fix_size:
            self._remove_oldest_element()

        self._splay_tree.insert(key, SaveKeyInfoNode(key_info, value))

    def get_value(self, key_info):
        key = self._sha256_hash(key_info)
        save_key_info_node = self._splay_tree.get_node(key)
        if not save_key_info_node:
        	return None
        return save_key_info_node.value.value

    def delete(self, key_info):
        key = self._sha256_hash(key_info)
        self._splay_tree.delete(key)

    def keys(self):
        return [node.value.key_info for node in self._splay_tree.postorder()]

    def items(self):
        return [(node.value.key_info, node.value.value) for node in self._splay_tree.levelorder()]