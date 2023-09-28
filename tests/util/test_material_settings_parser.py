from octoprint_mrbeam import parse_csv
from octoprint_mrbeam.util.device_info import (
    MODEL_MRBEAM_2_DC,
    MODEL_MRBEAM_2_DC_X,
    MODEL_MRBEAM_2_DC_S,
)
from octoprint_mrbeam.util.material_csv_parser import (
    LASER_MODEL_X,
    LASER_MODEL_S,
    DEFAULT_LASER_MODEL,
    model_ids_to_csv_name,
    MRB_DREAMCUT_X,
)


def test_model_ids_to_csv_name():
    assert model_ids_to_csv_name(MODEL_MRBEAM_2_DC_S, LASER_MODEL_X) == MRB_DREAMCUT_X
    assert model_ids_to_csv_name(MODEL_MRBEAM_2_DC_X, LASER_MODEL_X) == MRB_DREAMCUT_X
    assert model_ids_to_csv_name(MODEL_MRBEAM_2_DC, LASER_MODEL_X) == MRB_DREAMCUT_X


def test_material_settings_parser():
    material_dc = parse_csv(
        device_model=MODEL_MRBEAM_2_DC, laserhead_model=DEFAULT_LASER_MODEL
    )
    material_x = parse_csv(
        device_model=MODEL_MRBEAM_2_DC_X, laserhead_model=LASER_MODEL_X
    )
    material_s = parse_csv(
        device_model=MODEL_MRBEAM_2_DC_S, laserhead_model=LASER_MODEL_S
    )
    # TODO: SW-3719 test values for rotary mode
    assert material_dc.get("materials").get("Kraftplex").get("colors").get(
        "795f39"
    ).get("cut") != material_s.get("materials").get("Kraftplex").get("colors").get(
        "795f39"
    ).get(
        "cut"
    )
    assert material_dc.get("materials") != material_s.get("materials")
    assert (
        material_dc.get("materials")
        .get("Kraftplex")
        .get("colors")
        .get("795f39")
        .get("cut")[2]
        .get("cut_f")
        == 180
    )
    assert (
        material_s.get("materials")
        .get("Kraftplex")
        .get("colors")
        .get("795f39")
        .get("cut")[2]
        .get("cut_f")
        == 350
    )
    assert material_x.get("materials") != material_s.get("materials")
    assert (
        material_x.get("materials")
        .get("Kraftplex")
        .get("colors")
        .get("795f39")
        .get("cut")[2]
        .get("cut_f")
        != 350
    )
