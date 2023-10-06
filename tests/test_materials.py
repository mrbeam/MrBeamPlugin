from mock.mock import MagicMock

import pytest
from octoprint_mrbeam.materials import Materials

SAMPLE_MATERIALS = {
    "my default material": {
        "name": "Sample Material (default)",
        "laser_cutter_mode": "default",
    },
    "my rotary material": {
        "name": "Sample Material (rotary)",
        "laser_cutter_mode": "rotary",
    },
    # This is a legacy material, with no laser_cutter_mode info
    "my legacy material": {
        "name": "Sample Material",
    }
}

# Define sample custom material key for testing
SAMPLE_MATERIAL_KEY = "sample_key"


@pytest.fixture
def materials_instance(mrbeam_plugin):
    materials_instance = Materials(mrbeam_plugin)
    materials_instance._write_materials_to_yaml = MagicMock()
    materials_instance._load_materials_from_yaml = MagicMock()
    return materials_instance


def test_get_custom_materials_for_laser_cutter_mode_default(materials_instance, mocker):
    mocker.patch("octoprint_mrbeam.MrBeamPlugin.get_laser_cutter_mode", return_value="default")
    materials_instance.custom_materials = SAMPLE_MATERIALS
    custom_materials = materials_instance.get_custom_materials_for_laser_cutter_mode()
    assert "my default material" in custom_materials
    assert "my legacy material" in custom_materials
    assert "my rotary material" not in custom_materials


def test_get_empty_custom_materials(materials_instance, mocker):
    mocker.patch("octoprint_mrbeam.MrBeamPlugin.get_laser_cutter_mode", return_value="default")
    materials_instance.custom_materials = {}
    custom_materials = materials_instance.get_custom_materials_for_laser_cutter_mode()
    assert custom_materials == {}


def test_get_custom_materials_for_laser_cutter_mode_rotary(materials_instance, mocker):
    mocker.patch("octoprint_mrbeam.MrBeamPlugin.get_laser_cutter_mode", return_value="rotary")
    materials_instance.custom_materials = SAMPLE_MATERIALS
    custom_materials = materials_instance.get_custom_materials_for_laser_cutter_mode()
    assert "my rotary material" in custom_materials
    assert "my default material" not in custom_materials
    assert "my legacy material" not in custom_materials


def test_add_custom_material(materials_instance, mocker):
    mocker.patch("octoprint_mrbeam.MrBeamPlugin.get_laser_cutter_mode", return_value="default")
    materials_instance.add_custom_material("my new material", {})
    assert "my new material - default" in materials_instance.custom_materials
    materials_instance._write_materials_to_yaml.assert_called_once()


def test_delete_custom_material(materials_instance):
    materials_instance.custom_materials = SAMPLE_MATERIALS
    materials_instance.delete_custom_material("my default material")
    assert "my default material" not in materials_instance.custom_materials
    assert "my rotary material" in materials_instance.custom_materials
    materials_instance._write_materials_to_yaml.assert_called_once()


def test_delete_all_custom_materials(materials_instance):
    # Ensure deleting all custom materials works correctly
    materials_instance.custom_materials = SAMPLE_MATERIALS
    materials_instance.delete_all_custom_materials()
    assert not materials_instance.custom_materials
    materials_instance._write_materials_to_yaml.assert_called_once()
