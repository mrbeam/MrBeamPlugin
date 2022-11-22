from octoprint_mrbeam.util.version_comparator import compare_pep440_versions


def test_compare_pep440_versions_equal():
	assert compare_pep440_versions(v1="0.10.0", v2="0.10.0", comparator="__eq__") is True
	assert compare_pep440_versions(v1="0.10.0", v2="0.10.0", comparator="__le__") is True
	assert compare_pep440_versions(v1="0.10.0", v2="0.10.1", comparator="__lt__") is True
	assert compare_pep440_versions(v1="0.10.0", v2="0.10.0", comparator="__ge__") is True
	assert compare_pep440_versions(v1="0.10.1", v2="0.10.0", comparator="__gt__") is True
	assert compare_pep440_versions(v1="0.10.0a0", v2="0.10.0", comparator="__lt__") is True
	assert compare_pep440_versions(v1="0.10.0a0", v2="0.10.0a1", comparator="__lt__") is True
	assert compare_pep440_versions(v1="0.10.0a0", v2="0.10.0b0", comparator="__lt__") is True


def test_compare_pep440_versions_not_equal():
	assert compare_pep440_versions(v1="0.10.0", v2="0.10.1", comparator="__eq__") is False
	assert compare_pep440_versions(v1="0.10.1", v2="0.10.0", comparator="__le__") is False
	assert compare_pep440_versions(v1="0.10.1", v2="0.10.1", comparator="__lt__") is False
	assert compare_pep440_versions(v1="0.10.0", v2="0.10.1", comparator="__ge__") is False
	assert compare_pep440_versions(v1="0.10.1", v2="0.10.1", comparator="__gt__") is False
	assert compare_pep440_versions(v1="0.10.0", v2="0.10.0a0", comparator="__lt__") is False
	assert compare_pep440_versions(v1="0.10.0a1", v2="0.10.0a0", comparator="__lt__") is False
	assert compare_pep440_versions(v1="0.10.0b0", v2="0.10.0a0", comparator="__lt__") is False
