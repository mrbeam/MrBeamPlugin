from unittest import TestCase

from octoprint_mrbeamdoc.enum.mrbeam_doctype import MrBeamDocType

from octoprint_mrbeam.util import string_util


class TestStringUtils(TestCase):
    def test_extra_space_at_the_end__then_removed(self):
        self.assertEquals(string_util.separate_camelcase_words('Test '), 'Test')

    def test_extra_space_at_the_beginning__then_removed(self):
        self.assertEquals(string_util.separate_camelcase_words(' Test'), 'Test')

    def test_extra_space_at_the_middle__then_removed(self):
        self.assertEquals(string_util.separate_camelcase_words('Test  Test       Test'), 'Test Test Test')

    def test_no_camelcase__then_only_removed_extra_space(self):
        self.assertEquals(string_util.separate_camelcase_words('Test Test   Test', separator=','), 'Test Test Test')

    def test_camelcase_and_extra_space__then_separate_and_removed_extra_space(self):
        self.assertEquals(string_util.separate_camelcase_words('Test   TestTest', separator=','), 'Test Test,Test')

    def test_uppercase_word__then_first_char_separated_and_next_chars_in_groups_of_2(self):
        self.assertEquals(string_util.separate_camelcase_words('TESTTEST', separator=','), 'T,ES,TT,ES,T')

    def test_lowercase_word__then_unchanged(self):
        self.assertEquals(string_util.separate_camelcase_words('testtest', separator=','), 'testtest')

    def test_separation_of_2_words(self):
        self.assertEquals(string_util.separate_camelcase_words('TestTest'), 'Test Test')

    def test_separation_of_3_words(self):
        self.assertEquals(string_util.separate_camelcase_words('TestTestTest'), 'Test Test Test')

    def test_custom_separator(self):
        self.assertEquals(string_util.separate_camelcase_words('AtestBtestCtest', separator=','), 'Atest,Btest,Ctest')

    def test_separate_mrbeamdoc_type_usermanual_right_format_for_translation(self):
        self.assertEquals(string_util.separate_camelcase_words(MrBeamDocType.USER_MANUAL.value), 'User Manual')

    def test_separate_mrbeamdoc_type_quickstart_right_format_for_translation(self):
        self.assertEquals(string_util.separate_camelcase_words(MrBeamDocType.QUICKSTART_GUIDE.value),
                          'Quickstart Guide')
