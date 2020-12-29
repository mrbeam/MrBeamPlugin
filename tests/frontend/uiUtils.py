import time
import re
import json
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
import custom_expected_conditions as CEC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

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


def load_webapp(driver, baseUrl):
    # init
    wait = WebDriverWait(driver, 10, poll_frequency=1.0)

    # Step # | name | target | value
    # 1 | open | / |
    driver.get(baseUrl + "?" + str(time.time()))
    # 2 | setWindowSize | 1280x800 |
    driver.set_window_size(1280, 800)
    loading_overlay = wait.until(
        EC.visibility_of_element_located((By.ID, "loading_overlay"))
    )
    body = wait.until(
        CEC.element_has_css_class(
            (By.TAG_NAME, "body"), "run_loading_overlay_animation"
        )
    )
    loading_overlay.click()
    loading_overlay = wait.until(
        EC.invisibility_of_element_located((By.ID, "loading_overlay"))
    )


def login(driver, user="dev@mr-beam.org", pw="a"):
    wait = WebDriverWait(driver, 10)

    # 3 | click | id=login_screen_email_address_in |
    inputUser = driver.find_element(By.ID, "login_screen_email_address_in")
    inputUser.clear()
    inputUser.send_keys(user)
    # 4 | click | id=login_screen_password_in |
    inputPassword = driver.find_element(By.ID, "login_screen_password_in")
    inputPassword.clear()
    inputPassword.send_keys(pw)
    # 5 | click | id=login_screen_login_btn |
    driver.find_element(By.ID, "login_screen_login_btn").click()
    login_dialog = wait.until(
        EC.invisibility_of_element_located((By.ID, "loginscreen_dialog"))
    )
    return login_dialog


def close_notifications(driver):
    # close PNotifies for: login successful, corner calibration, update notification
    js = "PNotify.removeAll();"
    driver.execute_script(js)


def add_quick_shape_heart(driver, w="99", h="77"):
    wait = WebDriverWait(driver, 10)

    # 12 | click | id=working_area_tab_shape_btn |
    driver.find_element(By.ID, "working_area_tab_shape_btn").click()
    # 13 | click | css=#shape_tab_link_heart > .icon |
    element = wait.until(EC.element_to_be_clickable((By.ID, "shape_tab_link_heart")))
    element.click()
    # 14 | fillInput | id=quick_shape_heart_w |
    inputW = driver.find_element(By.ID, "quick_shape_heart_w")
    inputW.clear()
    inputW.send_keys(w)
    # 15 | fillInput | id=quick_shape_heart_w |
    inputW = driver.find_element(By.ID, "quick_shape_heart_h")
    inputW.clear()
    inputW.send_keys(h)
    # 16 | click | id=quick_shape_shape_done_btn |
    driver.find_element(By.ID, "quick_shape_shape_done_btn").click()
    qsSvgElement = wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "#userContent g.userSVG._freeTransformInProgress")
        )
    )

    return qsSvgElement


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
        vm.placeSVG(file, function(id){{ console.log(id); alert(id); }});
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
    try:
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.ID, "dialog_vector_graphics_conversion")
            )
        )
    finally:
        # log conversion dialog not visible: Did cou call start conversion?
        pass

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

    time.sleep(1)
    materialColor = driver.find_element_by_css_selector(
        SELECTOR_MATERIAL_COLOR["first"]
    )
    materialColor.click()

    time.sleep(1)
    materialThickness = driver.find_element_by_css_selector(
        SELECTOR_MATERIAL_THICKNESS["first"]
    )
    materialThickness.click()

    # enable cutting if desired and material does not provide settings

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


def wait_for_slicing_done(driver, log_callback):
    # log message Example
    # Got event SlicingDone with payload: {\\"gcode_location\\":\\"local\\",\\"gcode\\":\\"httpsmrbeam.github.iotest_rsccritical_designsFillings-in-defs.17.gco\\",\\"stl\\":\\"local/temp.svg\\",\\"time\\":1.9296720027923584,\\"stl_location\\":\\"local\\"}"', u'timestamp': 1609170424979, u'level': u'DEBUG'}
    pattern = r"(.+\"Got event SlicingDone with payload: )(?P<payload>.+)\""
    regex = re.compile(pattern)
    msg = wait_for_console_msg(driver, pattern, log_callback)
    if msg:
        m = regex.match(msg[u"message"])
        payload = m.group("payload")
        payload = payload.replace("\\", "")
        d = json.loads(payload)
        return d
    else:
        return None


def wait_for_console_msg(driver, pattern, log_callback):
    wait = WebDriverWait(driver, 10)
    logEntry = wait.until(CEC.console_log_contains(pattern, log_callback))
    return logEntry


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
