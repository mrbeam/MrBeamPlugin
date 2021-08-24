import sys, os, csv, json, collections
import octoprint_mrbeam

MRBEAM = "Mr Beam II"
MRB_DREAMCUT = "MrB II Dreamcut"
MRB_DREAMCUT_S = "MrB II Dreamcut S"

MRB_READY = "MrB II Dreamcut Ready"  # not used yet
MRB_DREAMCUT_NOT_VALIDATED = "Dreamcut (not validated)"  # not used yet
MRB_DREAMCUT_S_NOT_VALIDATED = "Dreamcut S (not validated)"  # not used yet

DEFAULT_LASER_MODEL = "0"
LASER_MODEL_S = "S"


def model_ids_to_csv_name(device_model_id, laser_model_id):
    convert = {
        (octoprint_mrbeam.util.device_info.MODEL_MRBEAM_2, DEFAULT_LASER_MODEL): MRBEAM,
        (
            octoprint_mrbeam.util.device_info.MODEL_MRBEAM_2_DC,
            DEFAULT_LASER_MODEL,
        ): MRB_DREAMCUT,
        (
            octoprint_mrbeam.util.device_info.MODEL_MRBEAM_2_DC,
            LASER_MODEL_S,
        ): MRB_DREAMCUT_S,
        (
            octoprint_mrbeam.util.device_info.MODEL_MRBEAM_2_DC_S,
            DEFAULT_LASER_MODEL,
        ): MRB_DREAMCUT,
        (
            octoprint_mrbeam.util.device_info.MODEL_MRBEAM_2_DC_S,
            LASER_MODEL_S,
        ): MRB_DREAMCUT_S,
        (
            octoprint_mrbeam.util.device_info.MODEL_MRBEAM_2_DC_R1,
            DEFAULT_LASER_MODEL,
        ): MRBEAM,
        (
            octoprint_mrbeam.util.device_info.MODEL_MRBEAM_2_DC_R2,
            DEFAULT_LASER_MODEL,
        ): MRBEAM,
    }
    if (device_model_id, laser_model_id) in convert.keys():
        return convert[(device_model_id, laser_model_id)]
    else:
        return False


# Deep merging of dictionaries
# inspired from in dict_merge in iobeam_protocol
def dict_merge(dct, merge_dct):
    """Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``. if the nested item are lists, then concatenate the lists.
    :param dct: dict / list onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.iteritems():
        if (
            k in dct.keys()
            and isinstance(dct[k], dict)
            and isinstance(merge_dct[k], collections.Mapping)
        ):
            dict_merge(dct[k], merge_dct[k])
        elif k in dct.keys() and type(dct[k]) is list and type(merge_dct[k]) is list:
            dct[k] = dct[k] + merge_dct[k]
        else:
            dct[k] = merge_dct[k]


def parse_csv(path=None, device_model=MRBEAM, laserhead_model="0"):
    """

    Assumes following column order:
    mrbeamversion, material, colorcode, thickness_or_engrave, intensity, speed, passes, pierce_time, dithering

    :param path: path to csv file
    :param device_model: the model of the device to use. Will return the material settings to use for that model.
    :param laserhead_model: the type of laserhead to use. Will return the material settings to use for that laserhead.
    :return:
    """
    path = path or os.path.join(
        __package_path__, "files/material_settings/materials.csv"
    )
    dictionary = {}
    with open(path, "r") as f:
        reader = csv.reader(f)
        fields = reader.next()
        prev_vals = None
        current_material = None
        current_color = None
        cur_color_has_cutting_setting = False
        for i, row in enumerate(reader):
            for j in range(len(row)):
                if type(row[j]) is str:
                    row[j] = row[j].strip()
            (
                mrbeamversion,
                material,
                colorcode,
                thickness_or_engrave,
                intensity,
                speed,
                passes,
                compressor_lvl,
                pierce_time,
                dithering,
            ) = row[:10]

            if colorcode and colorcode[0] == "#":
                colorcode = colorcode[1:]  # remove the '#' from the color hex

            # this is in case we have to skip the first line of a (another) material
            if material:
                current_material = material
            if colorcode:
                current_color = colorcode

            if not mrbeamversion in [MRBEAM, MRB_DREAMCUT, MRB_DREAMCUT_S, MRB_READY]:
                # Either a comment line, unused setting or experimental settings
                continue

            if not prev_vals or (
                current_material and current_material != prev_vals[1]
            ):  # Changed from 1 current_material to an other
                # Set default engraving setting (no engraving)
                # Set default cutting setting (no cutting)
                # Assumes that every new current_material comes with a new color setting
                dict_merge(
                    dictionary,
                    {
                        mrbeamversion: {
                            current_material: {
                                "colors": {current_color: {"engrave": None, "cut": []}}
                            }
                        }
                    },
                )
            elif (
                prev_vals and current_color and current_color != prev_vals[2]
            ):  # Changed from 1 color to the other
                dict_merge(
                    dictionary,
                    {
                        mrbeamversion: {
                            prev_vals[1]: {
                                "colors": {current_color: {"engrave": None, "cut": []}}
                            }
                        }
                    },
                )

            if prev_vals:
                # Retain the value of the previous line if no value is given (in the case of a cell merge)
                if (
                    not current_material
                ):  # No current_material name, assume the previous one
                    current_material = prev_vals[1]
                if not current_color:  # No Color name, assume the previous one
                    current_color = prev_vals[2]

            try:
                if type(thickness_or_engrave) is str:
                    thickness = float(thickness_or_engrave.strip().replace(",", "."))
                else:
                    thickness = float(thickness_or_engrave)
                settingname = "cut"
                try:
                    settings = [
                        {
                            "thicknessMM": thickness,
                            "cut_i": int(intensity),
                            "cut_f": int(speed),
                            "cut_p": int(passes),
                            "cut_compressor": int(compressor_lvl),
                        }
                    ]
                except ValueError as e:
                    raise Exception(
                        'Can not handle line {}: exception: "{}", row: {}'.format(
                            i, e, row
                        )
                    )
            except ValueError as e:
                if not thickness_or_engrave.lower().__contains__("engrav"):
                    raise Exception(
                        "Did not understand if line {} is an engraving or cutting job. Type of elm is {}: '{}' row: {}, original exception: \"{}\"".format(
                            i, type(thickness_or_engrave), thickness_or_engrave, row, e
                        )
                    )
                dithering = True if dithering == "yes" else False
                pierce_time = pierce_time or 0
                settings = {
                    "eng_compressor": int(compressor_lvl),
                    "eng_pierce": int(pierce_time),
                    "dithering": dithering,
                    "eng_p": passes,
                }
                settingname = "engrave"
                i_split = intensity.split("-")
                if len(i_split) == 2:
                    settings.update({"eng_i": [int(i_split[0]), int(i_split[1])]})
                elif len(i_split) == 1:
                    settings.update({"eng_i": [0, int(i_split[0])]})
                s_split = speed.split("-")
                if len(s_split) == 2:
                    settings.update({"eng_f": [int(s_split[0]), int(s_split[1])]})
                elif len(s_split) == 1:
                    settings.update({"eng_f": [0, int(s_split[0])]})
                # Can be error prone
            colorname = current_color  # TODO get current_color from colorname ?
            dict_merge(
                dictionary,
                {
                    mrbeamversion: {
                        current_material: {
                            "name": current_material,
                            # 'img': "", # TODO
                            # 'description': "", # TODO
                            # 'hints': "", # TODO
                            # 'safety_notes': "", # TODO
                            # 'laser_type': mrbeamversion,
                            "colors": {
                                current_color: {
                                    "name": colorname,
                                    settingname: settings,
                                }
                            },
                        }
                    }
                },
            )
            prev_vals = [
                mrbeamversion,
                current_material,
                current_color,
                thickness_or_engrave,
                intensity,
                speed,
                passes,
                compressor_lvl,
                pierce_time,
                dithering,
            ]  # update current row values for next loop
    csv_name = model_ids_to_csv_name(device_model, str(laserhead_model))
    if csv_name not in dictionary:
        csv_name = MRBEAM
    res = dict(
        materials=dictionary.get(csv_name, {}), laser_source=str(laserhead_model)
    )
    return res


if __name__ == "__main__":
    if len(sys.argv[1]) > 1:
        path = sys.argv[1]
        ret = parse_csv(path)
    else:
        ret = parse_csv()
    print(json.dumps(ret, indent=2))
    # f_csv = os.open(path)
