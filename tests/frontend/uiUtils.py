import time
import re
import json
import logging
import platform

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
import custom_expected_conditions as CEC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

from tests.frontend import frontendTestUtils

DEFAULT_ENV = {
    "BEAMOS_VERSION": "?",
    "BEAMOS_BRANCH": "?",
    "BEAMOS_IMAGE": "?",
    "MRBEAM_ENV": "?",
    "MRBEAM_MODEL": "?",
    "MRBEAM_LANGUAGE": "?",
    "MRBEAM_SERIAL": "?",
    "MRBEAM_PRODUCT_NAME": "?",
    "MRBEAM_GRBL_VERSION": "?",
    "MRBEAM_SW_TIER": "?",
    "MRBEAM_WIZARD_TO_SHOW": "?",
    "APIKEY": "?",
}

SELECTOR_SUCCESS_NOTIFICATION = "body > div.ui-pnotify > div.alert-success"
SELECTOR_MATERIAL = {
    "bamboo": '#material_list > li[mrb_name="/plugin/mrbeam/static/img/materials/Bamboo.jpg"]',
    "felt": '#material_list > li[mrb_name="/plugin/mrbeam/static/img/materials/Felt.jpg"]',
    "first": "#material_list > li[mrb_name]:first-child",
}

SELECTOR_MATERIAL_COLOR = {
    "first": "#color_list > li.material_color_entry:first-child",
    "felt": "#material_color_eb5a3e",
}

SELECTOR_MATERIAL_THICKNESS = {
    "first": "#thickness_list > div.thickness_sample:first-child",
    "felt": "#material_thickness_3",
    "engrave": "#material_thickness_-1",
}
SELECTOR_CONVERSION_PROGRESS_HEADLINE = (
    "#dialog_vector_graphics_conversion > div.modal-header > h3:nth-child(2)"
)


def load_webapp(driver, baseUrl):
    # init
    wait = WebDriverWait(driver, 10, poll_frequency=0.5)

    # Step # | name | target | value
    # 1 | open | / |
    driver.get(baseUrl + "?" + str(time.time()))
    # 2 | setWindowSize | 1280x800 |
    driver.set_window_size(1280, 800)

    loading_overlay = wait.until(
        CEC.document_ready(), "Waiting for document.readyState == 'complete'"
    )

    modernLogin = isOctoPrint_1_4(driver)
    if not modernLogin:
        skip_loading_animation(driver)

    versions = frontendTestUtils.get_versions(driver)
    logging.getLogger().info("Testing {}".format(versions))
    return versions


def isOctoPrint_1_4(driver):
    # js = 'return mrbeam.isOctoPrintVersionMin("1.4")'
    js = 'return (document.title == "OctoPrint Login")'
    return driver.execute_script(js)


def login(driver, user="dev@mr-beam.org", pw="a"):
    useModernLogin = isOctoPrint_1_4(driver)
    # logging.getLogger().debug("useModern... {}".format(useModernLogin))
    if useModernLogin:
        return loginOctoprint_1_4(driver, user, pw)
    else:
        return loginOctoprint_1_3(driver, user, pw)


def loginOctoprint_1_4(driver, user, pw):

    wait = WebDriverWait(driver, 3, poll_frequency=0.5)
    inputUser = _fill_input(driver, "#login-user", user)
    inputPassword = _fill_input(driver, "#login-password", pw)
    driver.find_element(By.ID, "login-button").click()
    skip_loading_animation(driver)

    js = "return OctoPrint.options.apikey;"
    return driver.execute_script(js)


def loginOctoprint_1_3(driver, user, pw):
    wait = WebDriverWait(driver, 10)

    inputUser = _fill_input(driver, "#login_screen_email_address_in", user)
    inputPassword = _fill_input(driver, "#login_screen_password_in", pw)
    driver.find_element(By.ID, "login_screen_login_btn").click()
    login_dialog = wait.until(
        EC.invisibility_of_element_located((By.ID, "loginscreen_dialog"))
    )
    js = "return OctoPrint.options.apikey;"
    return driver.execute_script(js)


def skip_loading_animation(driver):
    wait = WebDriverWait(driver, 60, poll_frequency=0.5)
    loading_overlay = wait.until(
        EC.visibility_of_element_located((By.ID, "loading_overlay")),
        "Waiting for #loading_overlay to appear...",
    )
    body = wait.until(
        CEC.element_has_css_class(
            (By.TAG_NAME, "body"), "run_loading_overlay_animation"
        ),
        "Waiting for <body> to get class .run_loading_overlay_animation ...",
    )
    loading_overlay.click()
    loading_overlay = wait.until(
        EC.invisibility_of_element_located((By.ID, "loading_overlay")),
        "Waiting for #loading_overlay to disappear...",
    )
    return body


def close_notifications(driver):
    # close PNotifies for: login successful, corner calibration, update notification
    js = "PNotify.removeAll();"
    driver.execute_script(js)


def add_quick_shape_rect(driver, w=99, h=77, r=0, stroke=True, fill=False):
    _click_on(driver, "#working_area_tab_shape_btn")
    _click_on(driver, "#shape_tab_link_rect")
    _fill_input(driver, "#quick_shape_rect_w", str(w))
    _fill_input(driver, "#quick_shape_rect_h", str(h))
    _fill_input(driver, "#quick_shape_rect_radius", str(r))
    _set_checkbox(driver, "#quick_shape_stroke", stroke)
    _set_checkbox(driver, "#quick_shape_fill", fill)
    _click_on(driver, "#quick_shape_shape_done_btn")
    quickShapeElement, listElement = get_design(driver)
    return quickShapeElement, listElement


def add_quick_shape_circle(driver, r=77, stroke=True, fill=False):
    _click_on(driver, "#working_area_tab_shape_btn")
    _click_on(driver, "#shape_tab_link_circle")
    _fill_input(driver, "#quick_shape_circle_radius", str(r))
    _set_checkbox(driver, "#quick_shape_stroke", stroke)
    _set_checkbox(driver, "#quick_shape_fill", fill)
    _click_on(driver, "#quick_shape_shape_done_btn")
    quickShapeElement, listElement = get_design(driver)
    return quickShapeElement, listElement


def add_quick_shape_star(
    driver, corners=5, r=77, sharpness=0.3, stroke=True, fill=False
):
    _click_on(driver, "#working_area_tab_shape_btn")
    _click_on(driver, "#shape_tab_link_star")
    _fill_input(driver, "#quick_shape_star_radius", str(r))
    _fill_input(driver, "#quick_shape_star_corners", str(corners))
    _fill_input(driver, "#quick_shape_star_sharpness", str(sharpness))
    _set_checkbox(driver, "#quick_shape_stroke", stroke)
    _set_checkbox(driver, "#quick_shape_fill", fill)
    _click_on(driver, "#quick_shape_shape_done_btn")
    quickShapeElement, listElement = get_design(driver)
    return quickShapeElement, listElement


def add_quick_shape_heart(driver, w=99, h=55, magic=0.4, stroke=True, fill=False):
    _click_on(driver, "#working_area_tab_shape_btn")
    _click_on(driver, "#shape_tab_link_heart")
    _fill_input(driver, "#quick_shape_heart_w", str(w))
    _fill_input(driver, "#quick_shape_heart_h", str(h))
    _fill_input(driver, "#quick_shape_heart_lr", str(magic))
    _set_checkbox(driver, "#quick_shape_stroke", stroke)
    _set_checkbox(driver, "#quick_shape_fill", fill)
    _click_on(driver, "#quick_shape_shape_done_btn")
    quickShapeElement, listElement = get_design(driver)
    return quickShapeElement, listElement


def get_design(driver):
    wait = WebDriverWait(driver, 10, poll_frequency=0.5)
    designElement = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "#userContent g.userSVG")),
        message="Waiting for design to appear on working area.",
    )
    listId = designElement.get_attribute("mb:origin")
    listElement = driver.find_element_by_id(listId)
    logging.getLogger().info("Found design #{}".format(listId))
    return (designElement, listElement)


def get_paths(driver, selector):
    js = """
        let dAttrs = [];
        const elements = snap.selectAll('{} path');
        for(let i = 0; i < elements.length; i++){{
            dAttrs.push(elements[i].attr('d'));
        }}
        return dAttrs;
    """.format(
        selector
    )
    return driver.execute_script(js)


def add_svg_url(driver, url):
    wait = WebDriverWait(driver, 10)
    js = """
        let vm = ko.dataFor(document.getElementById('area_preview'));
        const file = {{
          date: 1234567890,
          display: "{0}",
          name: "{0}",
          origin: "local",
          path: "{0}",
          refs: {{
            download: "{0}",
            resource: "{0}"
          }},
          size: 999999,
          type: "model",
          typePath: ["model", "svg"],
          weight: 1
        }};
        vm.placeSVG(file, function(id){{ alert(id); }});
    """.format(
        url
    )
    driver.execute_script(js)

    # Wait for the alert to be displayed
    wait.until(EC.alert_is_present())

    # Store the alert in a variable for reuse
    alert = driver.switch_to.alert

    # Store the alert text in a variable
    placedSvgId = alert.text

    # Press the Cancel button
    alert.dismiss()
    listElem = wait.until(EC.visibility_of_element_located((By.ID, placedSvgId)))
    # svgElem = wait.until(EC.visibility_of_element_located((By.ID, placedSvgId+'-0'))) # does not work. exec js instead?
    return listElem


def get_bbox(driver):
    js = """
        let bb = snap.select('#userContent').getBBox();
        return bb;
    """
    bbox = driver.execute_script(js)
    # {u'vb': u'76.14178466796875 51.783084869384766 159.1521759033203 251.14407348632812',
    # u'r0': 148.66300880016152,
    # u'r1': 79.57608795166016,
    # u'r2': 125.57203674316406,
    # u'h': 251.14407348632812,
    # u'height': 251.14407348632812,
    # u'width': 159.1521759033203,
    # u'cy': 177.35512161254883,
    # u'cx': 155.7178726196289,
    # u'w': 159.1521759033203,
    # u'x': 76.14178466796875,
    # u'x2': 235.29396057128906,
    # u'path': [[u'M', 76.14178466796875, 51.783084869384766], [u'l', 159.1521759033203, 0], [u'l', 0, 251.14407348632812], [u'l', -159.1521759033203, 0], [u'z']],
    # u'y2': 302.9271583557129,
    # u'y': 51.783084869384766}
    return bbox


def select_material(driver, material="felt", cut=True, engrave=True):
    # ensure conversion dialog is open
    element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "dialog_vector_graphics_conversion")),
        message="Conversion dialog not visible: Did cou call start conversion?",
    )

    # ensure no material is selected
    isMaterialSelected = driver.execute_script(
        """
        vm = ko.dataFor(document.getElementById('material_row'));
        return (vm.selected_material() !== null);
    """
    )
    if isMaterialSelected:
        unselect_material()

    close_notifications(
        driver
    )  # ensure no "Text elements" or "Update Notification" covers the material list

    # select material
    materialElem = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTOR_MATERIAL[material]))
    )
    materialElem.click()

    time.sleep(1)  # important to ensure css transition is finished
    materialColor = driver.find_element_by_css_selector(
        SELECTOR_MATERIAL_COLOR["first"]
    )
    materialColor.click()

    time.sleep(1)  # important to ensure css transition is finished
    materialThickness = driver.find_element_by_css_selector(
        SELECTOR_MATERIAL_THICKNESS["first"]
    )
    materialThickness.click()

    # enable cutting if desired and material does not provide settings
    _click_on(driver, "#parameter_assignment_show_advanced_settings_cb")
    el = driver.find_element(
        By.CSS_SELECTOR, "#engrave_job div.not_possible_on_this_material > a"
    )
    if el.is_displayed():
        el.click()
    el = driver.find_element(
        By.CSS_SELECTOR, "#first_job div.not_possible_on_this_material > a"
    )
    if el.is_displayed():
        el.click()
    _fill_input(driver, "#svgtogcode_img_intensity_white", "7")
    _fill_input(driver, "#svgtogcode_img_intensity_black", "77")
    _fill_input(driver, "#svgtogcode_img_feedrate_white", "888")
    _fill_input(driver, "#svgtogcode_img_feedrate_black", "88")
    _fill_input(driver, "#parameter_assignment_pierce_time_in", "1")
    _fill_input(driver, "#svgtogcode_img_line_dist", "1")
    _fill_input(driver, "#first_job input.param_intensity", "99")
    _fill_input(driver, "#first_job input.param_feedrate", "999")
    _fill_input(driver, "#first_job input.param_passes", "1")
    # _fill_input(driver, '#first_job input.compressor_input', '1')
    _click_on(driver, "#parameter_assignment_engraving_mode_precise_btn")
    driver.execute_script("$('#engrave_job input[name=overshoot_type]').click()")
    # _click_on(driver, '#engrave_job input[name=overshoot_type]')
    _fill_input(driver, "#first_job input.param_piercetime", "1")
    # enable engraving if desired and material does not provide settings

    # return success


def unselect_material(driver):
    driver.execute_script(
        """
        vm = ko.dataFor(document.getElementById('material_row'));
        vm.select_material(null);
    """
    )
    # wait?


def start_conversion(driver, material="felt"):
    wait = WebDriverWait(driver, 10, poll_frequency=2.0)
    # driver.find_element(By.ID, "laser_button").click() # does not work??
    driver.execute_script("$('#laser_button').click();")  # workaround
    conversion_dialog = wait.until(
        EC.visibility_of_element_located((By.ID, "dialog_vector_graphics_conversion"))
    )

    # ensure material is selected
    isMaterialSelected = driver.execute_script(
        """
        vm = ko.dataFor(document.getElementById('material_row'));
        return (vm.selected_material() !== null);
    """
    )

    if not isMaterialSelected:
        select_material(driver, "felt")

    driver.find_element(By.ID, "start_job_btn").click()


def wait_for_conversion_started(driver, log_callback):
    # log message Example
    # Conversion started. {\\"gcode_location\\":\\"local\\",\\"gcode\\":\\"httpsmrbeam.github.iotest_rsccritical_designsFillings-in-defs.17.gco\\",\\"stl\\":\\"local/temp.svg\\",\\"time\\":1.9296720027923584,\\"stl_location\\":\\"local\\"}"', u'timestamp': 1609170424979, u'level': u'DEBUG'}
    # pattern = r"(.+\"Conversion started.)(?P<payload>.+)\""
    pattern = r"(.+\"SELENIUM_CONVERSION_FINISHED:)(?P<payload>.+)\""
    regex = re.compile(pattern)
    msg = wait_for_console_msg(
        driver,
        pattern,
        log_callback,
        message="Listening on console.log for {} ...".format(pattern),
    )
    if msg:
        m = regex.match(msg["message"])
        payload = m.group("payload")
        payload = payload.replace("\\", "")
        d = json.loads(payload)
        return d
    else:
        return None


def wait_for_ready_to_laser_dialog(driver):
    wait = WebDriverWait(driver, 20, poll_frequency=0.5)
    js = "return mrbeam.mrb_state.rtl_mode"
    wait.until(
        CEC.js_expression_true(js),
        message="Waiting for js '{}' to return true...".format(js),
    )
    js = "return mrbeam.viewModels.readyToLaserViewModel.gcodeFile"
    gcode = driver.execute_script(js)
    return gcode


def wait_for_console_msg(driver, pattern, log_callback, message=""):
    wait = WebDriverWait(driver, 20, poll_frequency=0.5)
    logEntry = wait.until(
        CEC.console_log_contains(pattern, log_callback), message=message
    )
    return logEntry


def ensure_device_homed(driver):
    js = """
        let isHomed = mrbeam.mrb_state.is_homed;
        if(!isHomed){
            mrbeam.viewModels.workingAreaViewModel.performHomingCycle('position_buttons');
        }
    """
    driver.execute_script(js)
    wait = WebDriverWait(driver, 20, poll_frequency=0.5)
    el = wait.until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, "#mrb_state_header > span:nth-child(2) > span"),
            "Operational",
        ),
        "Waiting for homing cycle to finish...",
    )
    return el


def cancel_job(driver):
    js = """
    OctoPrint.job.cancel(); // 409 ?
    let vm = ko.dataFor(document.getElementById('ready_to_laser_dialog'));
    vm.state.cancel();
    """
    driver.execute_script(js)


def cleanup_after_conversion(driver):
    wait = WebDriverWait(driver, 10)

    # hide conversion dialog
    js = """
    PNotify.removeAll();
    let vm = ko.dataFor(document.getElementById('material_row'));
    vm.slicing_in_progress(false);
    vm.set_material();
    $("#dialog_vector_graphics_conversion").modal("hide");
    """
    driver.execute_script(js)
    conversion_dialog = wait.until(
        EC.invisibility_of_element_located((By.ID, "dialog_vector_graphics_conversion"))
    )


def clear_working_area(driver):
    wait = WebDriverWait(driver, 10)

    js = """
        let vm = ko.dataFor(document.getElementById('area_preview'));
        vm.clear();
    """
    driver.execute_script(js)

    # driver.find_element(By.ID, "clear_working_area_btn").click()
    designCount = driver.execute_script(
        "return snap.selectAll('#userContent>*').length"
    )
    assert designCount == 0, "WorkingArea not empty after clear(), was " + str(
        designCount
    )


def _fill_input(driver, selector, string):
    input = driver.find_element(By.CSS_SELECTOR, selector)
    # slider
    if input.get_attribute("type") == "range":
        _set_range(driver, input, string)
    else:
        # on Mac we need the command key
        ctrl_key = Keys.COMMAND if platform.system() == "Darwin" else Keys.CONTROL
        # input.clear()
        # time.sleep(1.2)
        input.send_keys(ctrl_key + "a")
        # time.sleep(1.2)
        input.send_keys(string)
        # time.sleep(1.2)
    return input


def _click_on(driver, selector):
    el = WebDriverWait(driver, 10, poll_frequency=0.5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector)),
        message="Waiting for {} to be clickable".format(selector),
    )
    el.click()


def _set_checkbox(driver, selector, checked=True):
    el = WebDriverWait(driver, 10, poll_frequency=0.5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector)),
        message="Waiting for {} to be clickable".format(selector),
    )
    isChecked = el.get_attribute("checked") == "true"
    if isChecked != checked:
        el.click()


def _set_range(driver, el, val):
    # The adjustment helper to drag the slider thumb
    def adjust(deltax):
        if deltax < 0:
            deltax = int(math.floor(min(-1, deltax)))
        else:
            deltax = int(math.ceil(max(1, deltax)))
        ac = ActionChains(driver)
        ac.click_and_hold(None)
        ac.move_by_offset(deltax, 0)
        ac.release(None)
        ac.perform()

    minval = float(el.get_attribute("min") or 0)
    maxval = float(el.get_attribute("max") or 100)
    v = max(0, min(1, (float(val) - minval) / (maxval - minval)))
    width = el.size["width"]
    target = float(width) * v

    ac = ActionChains(driver)

    # drag from min to max value, to ensure oninput event
    ac.move_to_element_with_offset(el, 0, 1)
    ac.click_and_hold()
    ac.move_by_offset(width, 0)

    # drag to the calculated position
    ac.move_to_element_with_offset(el, target, 1)

    ac.release()
    ac.perform()

    # perform a binary search and adjust the slider thumb until the value matches
    while True:
        curval = el.get_attribute("value")
        if float(curval) == float(val):
            return True
        prev_guess = target
        if float(curval) < float(val):
            minguess = target
            target += (maxguess - target) / 2
        else:
            maxguess = target
            target = minguess + (target - minguess) / 2
        deltax = target - prev_guess
        if abs(deltax) < 0.5:
            break  # cannot find a way, fallback to javascript.

        time.sleep(0.1)  # Don't consume CPU too much

        adjust(deltax)

    # Finally, if the binary search algoritm fails to achieve the final value
    # we'll revert to the javascript method so at least the value will be changed
    # even though the browser events wont' be triggered.

    # Fallback
    driver.execute_script("arguments[0].value=arguments[1];", el, val)
    curval = el.get_attribute("value")
    if float(curval) == float(val):
        return True
    else:
        raise Exception("Can't set value %f for the element." % val)
