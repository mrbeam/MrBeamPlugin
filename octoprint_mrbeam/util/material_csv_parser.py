import sys, os, csv, json, collections

MRBEAM = 'Mr Beam II'
MRB_DREAMCUT = 'MrB II Dreamcut'
MRB_READY = 'MrB II Dreamcut Ready'
# Deep merging of dictionaries
# inspired from in dict_merge in iobeam_protocol
def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``. if the nested item are lists, then concatenate the lists.
    :param dct: dict / list onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None
    """
    for k, v in merge_dct.iteritems():
        if k in dct.keys() and isinstance(dct[k], dict) and isinstance(merge_dct[k], collections.Mapping):
            dict_merge(dct[k], merge_dct[k])
        elif k in dct.keys() and type(dct[k]) is list and type(merge_dct[k]) is list:
            dct[k] = dct[k] + merge_dct[k]
        else:
            dct[k] = merge_dct[k]

def parse_csv(path = None, laserhead=MRBEAM):
    """

    Assumes following column order:
    mrbeamversion, material, colorcode, thickness_or_engrave, intensity, speed, passes, pierce_time, dithering

    :param path: path to csv file
    :param laserhead: the type of laserhead to use. Will return the material settings to use for that laserhead.
    :return:
    """
    path = path or os.path.join(__package_path__, "files/material_settings/materials.csv")
    dictionary = {}
    with open(path, 'r') as f:
        reader = csv.reader(f)
        fields = reader.next()
        prev_vals = None
        cur_color_has_engraving_setting = False
        cur_color_has_cutting_setting = False
        for i, row in enumerate(reader):
            for j in range(len(row)):
                if type(row[j]) is str:
                    row[j] = row[j].strip()
            mrbeamversion, material, colorcode, thickness_or_engrave, intensity, speed, passes, compressor_lvl, pierce_time, dithering = row[:10]
            if not mrbeamversion in [MRBEAM, MRB_DREAMCUT, MRB_READY]:
                # Either a comment line, unused setting or experimental settings
                continue
            if colorcode and colorcode[0] == '#':
                colorcode = colorcode[1:] # remove the '#' from the color hex
            if not prev_vals or (material and material != prev_vals[1]): # Changed from 1 material to an other
                # Set default engraving setting (no engraving)
                # Set default cutting setting (no cutting)
                # Assumes that every new material comes with a new color setting
                dict_merge(dictionary, {mrbeamversion: {material: {'colors': {colorcode: {'engrave': None,
                                                                                          'cut': []}}}}})
            elif prev_vals and colorcode and colorcode != prev_vals[2]:  # Changed from 1 color to the other
                dict_merge(dictionary, {mrbeamversion: {prev_vals[1]: {'colors': {colorcode: {'engrave': None,
                                                                                              'cut': []}}}}})
            if prev_vals:
                # Retain the value of the previous line if no value is given (in the case of a cell merge)
                if not material: # No material name, assume the previous one
                    material = prev_vals[1]
                if not colorcode:  # No Color name, assume the previous one
                    colorcode = prev_vals[2]

            try:
                if type(thickness_or_engrave) is str:
                    thickness = float(thickness_or_engrave.replace(',', '.'))
                else:
                    thickness = float(thickness_or_engrave)
                settingname = 'cut'
                settings = [{'thicknessMM': thickness, 'cut_i': int(intensity), 'cut_f': int(speed), 'cut_p': int(passes), 'cut_compressor_lvl': int(compressor_lvl)}]
            except ValueError:
                if not thickness_or_engrave.lower().__contains__('engrav'):
                    raise Exception("Did not understand if line {} is an engraving or cutting job. Type of elm is {} : {}".format(i, type(thickness_or_engrave), thickness_or_engrave))
                dithering = True if dithering == 'yes' else False
                pierce_time = pierce_time or 0
                settings = {'engrave_compressor_lvl': int(compressor_lvl),
                            'eng_pierce': int(pierce_time),
                            'dithering': dithering}
                settingname = 'engrave'
                i_split = intensity.split('-')
                if len(i_split) == 2:
                    settings.update({'eng_i': [int(i_split[0]), int(i_split[1])]})
                elif len(i_split) == 1:
                    settings.update({'eng_i': [0, int(i_split[0])]})
                s_split = speed.split('-')
                if len(s_split) == 2:
                    settings.update({'eng_f': [int(s_split[0]), int(s_split[1])]})
                elif len(s_split) == 1:
                    settings.update({'eng_f': [0, int(s_split[0])]})
                # Can be error prone
            colorname = colorcode # TODO get colorcode from colorname ?
            dict_merge(dictionary, {mrbeamversion: {material: {'name': material,
                                                               # 'img': "", # TODO
                                                               # 'description': "", # TODO
                                                               # 'hints': "", # TODO
                                                               # 'safety_notes': "", # TODO
                                                               # 'laser_type': mrbeamversion,
                                                               'colors': { colorcode: {'name': colorname,
                                                                                       settingname: settings}}}}})
            prev_vals = [mrbeamversion, material, colorcode, thickness_or_engrave, intensity, speed, passes, compressor_lvl, pierce_time, dithering] # update current row values for next loop
    return dictionary[laserhead]


if __name__ == "__main__":
    if len(sys.argv[1]) > 1:
        path = sys.argv[1]
        ret = parse_csv(path)
    else:
        ret = parse_csv()
    print json.dumps(ret, indent=2)
    # f_csv = os.open(path)
