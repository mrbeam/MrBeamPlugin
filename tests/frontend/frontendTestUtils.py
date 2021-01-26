import pytest
import logging


def get_versions(driver):
    js = """
    return {
      'BEAMOS_VERSION': BEAMOS_VERSION,
      'BEAMOS_BRANCH': BEAMOS_BRANCH,
      'BEAMOS_IMAGE': BEAMOS_IMAGE,
      'MRBEAM_ENV': MRBEAM_ENV,
      'MRBEAM_MODEL': MRBEAM_MODEL,
      'MRBEAM_LANGUAGE': MRBEAM_LANGUAGE,
      'MRBEAM_SERIAL': MRBEAM_SERIAL,
      'MRBEAM_PRODUCT_NAME': MRBEAM_PRODUCT_NAME,
      'MRBEAM_GRBL_VERSION': MRBEAM_GRBL_VERSION,
      'MRBEAM_SW_TIER': MRBEAM_SW_TIER,
      'MRBEAM_WIZARD_TO_SHOW': MRBEAM_WIZARD_TO_SHOW,
      'OCTOPRINT_VERSION': VERSION,
      'OCTOPRINT_BRANCH': BRANCH,
      'APIKEY': OctoPrint.options.apikey,
    };
    """
    return driver.execute_script(js)


def compare_dimensions(bbox, exp, tolerance=0.0001):
    #    exp = {
    #        "y": 27.573705673217773,
    #        "x": 5.796566963195801,
    #        "w": 149.99998474121094,
    #        "h": 149.99998474121094,
    #    }

    success_result = {}
    err_msg = "Dimensions do not match:"
    for key in "xywh":
        ukey = unicode(key)
        if ukey in bbox and key in exp:
            in_tolerance = abs(bbox[ukey] - exp[key]) < tolerance
            success_result[key] = in_tolerance
            if not in_tolerance:
                err_msg += " {}: {} != {}".format(key, bbox[ukey], exp[key])

    if all(success_result.values()):
        return True, ""
    else:
        return False, err_msg
