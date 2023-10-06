import pytest

from octoprint_mrbeam.model.custom_material_model import CustomMaterialModel


@pytest.fixture
def sample_custom_material():
    sample_material_data = {
        "name": "Sample Material",
        "description": "This is a test material",
        "colors": ["red", "green", "blue"],
        "hints": "Some hints",
        "img": "sample.jpg",
        "laser_cutter_mode": "default",
        "laser_model": "sample_model",
        "safety_notes": "Safety notes for testing",
        "plugin_v": "1.0",
        "device_model": "Device123",
    }

    custom_material = CustomMaterialModel("sample_key", sample_material_data, "default", "X", "1.0", "dreamcut")

    yield custom_material


def test_material_key_generation(sample_custom_material):
    assert sample_custom_material.material_key == "sample_key - default"


def test_to_dict(sample_custom_material):
    material_dict = sample_custom_material.to_dict()
    expected_dict = {'laser_cutter_mode': 'default', 'safety_notes': 'Safety notes for testing', 'description': 'This is a test material', 'img': 'sample.jpg', 'device_model': 'dreamcut', 'name': 'Sample Material', 'custom': True, 'laser_model': 'X', 'colors': ['red', 'green', 'blue'], 'v': '1.0', 'material_key': 'sample_key - default', 'hints': 'Some hints'}

    assert material_dict == expected_dict
