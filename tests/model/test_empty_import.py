from unittest import TestCase

from octoprint_mrbeam.model import EmptyImport


class TestBurgerMenuService(TestCase):

    def test_random_attribute_returns_self(self):
        empty_import = EmptyImport()
        self.assertIs(empty_import.documents, empty_import)

    def test_random_method_returns_none(self):
        empty_import = EmptyImport()
        result = empty_import.random_method()
        self.assertIs(result, None)
