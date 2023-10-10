from octoprint_mrbeam import LaserCutterModeModel


def test_laser_cutter_mode_init():
    laser_cutter_mode = LaserCutterModeModel(1)
    assert laser_cutter_mode.id == 1
    assert laser_cutter_mode.name == "rotary"

    laser_cutter_mode = LaserCutterModeModel(2)  # Invalid mode id
    assert laser_cutter_mode.id == 0  # Should fall back to default id
    assert laser_cutter_mode.name == "default"  # Should fall back to default name


def test_laser_cutter_mode_setters():
    laser_cutter_mode = LaserCutterModeModel()

    # Setting id should change name
    laser_cutter_mode.id = 1
    assert laser_cutter_mode.id == 1
    assert laser_cutter_mode.name == "rotary"

    # Setting invalid id should set fall back id and name
    laser_cutter_mode.id = 2
    assert laser_cutter_mode.id == 0
    assert laser_cutter_mode.name == "default"

    # Setting name should change id
    laser_cutter_mode.name = "rotary"
    assert laser_cutter_mode.id == 1
    assert laser_cutter_mode.name == "rotary"

    # Setting invalid name should set fall back id and name
    laser_cutter_mode.name = "invalid_mode"
    assert laser_cutter_mode.id == 0
    assert laser_cutter_mode.name == "default"


def test_laser_cutter_mode_get_mode_key():
    laser_cutter_mode = LaserCutterModeModel()

    mode_key = laser_cutter_mode._get_mode_key("rotary")
    assert mode_key == 1

    mode_key = laser_cutter_mode._get_mode_key("invalid_mode")  # Invalid mode name
    assert mode_key == 0  # Should fall back to default id
