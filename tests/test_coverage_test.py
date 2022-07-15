from octoprint_mrbeam.coverage_test import tested_function


def test_tested_function():
    assert tested_function(True) is True
    assert tested_function(False) is False


def test_tested_function_fail():
    assert tested_function(True) is False
    assert tested_function(False) is True
