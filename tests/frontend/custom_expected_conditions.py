import re
import logging


class element_has_css_class(object):
    """An expectation for checking that an element has a particular css class.

    locator - used to find the element
    returns the WebElement once it has the particular css class
    """

    def __init__(self, locator, css_class):
        self.log = logging.getLogger()
        self.locator = locator
        self.css_class = css_class

    def __call__(self, driver):
        element = driver.find_element(*self.locator)  # Finding the referenced element
        # self.log.debug("CSS" + str(element))
        if self.css_class in element.get_attribute("class"):
            return element
        else:
            return False


class document_ready(object):
    """An expectation for checking that page has fully loaded.

    returns the WebElement once it has the particular css class
    """

    def __init__(self):
        self.log = logging.getLogger()
        self.js = "return document.readyState === 'complete';"

    def __call__(self, driver):
        fullyLoaded = driver.execute_script(self.js)
        return fullyLoaded


class js_expression_true(object):
    """An expectation for checking a particular js expression value.

    returns the js return value
    """

    def __init__(self, js):
        self.log = logging.getLogger()
        self.js = js

    def __call__(self, driver):
        # self.log.info(self.js+" = {}".format(driver.execute_script("return mrbeam.mrb_state;")))
        evaluation = driver.execute_script(self.js)
        return evaluation


class console_log_contains(object):
    """An expectation for checking that console.log contains a message matching
    particular pattern.

    pattern - used to match the log message
    consumed_logs_callback - callback to do something / preserve the consumed logs
    returns the WebElement once it has the particular css class
    """

    def __init__(self, pattern, consumed_logs_callback=None):

        self.regex = re.compile(pattern)
        self.log = logging.getLogger()
        self.log_callback = consumed_logs_callback

    def __call__(self, driver):
        # log entry example
        # {u'source': u'console-api',
        #  u'message': u'http://localhost:5000/?1609167298.58 110:33 "Could not instantiate the following view models due to unresolvable dependencies:"',
        #  u'timestamp': 1609167299977,
        #  u'level': u'SEVERE'}
        logs = driver.get_log("browser")
        if self.log_callback != None:
            self.log_callback(logs)
        # self.log.debug("got {} console log lines".format(len(logs)))
        for entry in logs:
            # self.log.debug("__{}: {}".format(entry[u"level"], entry[u"message"]))

            if self.regex.match(entry[u"message"]):
                return entry

        return False
