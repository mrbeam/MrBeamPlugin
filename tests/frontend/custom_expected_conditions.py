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


class console_log_contains(object):
    """An expectation for checking that an element has a particular css class.

    locator - used to find the element
    returns the WebElement once it has the particular css class
    """

    def __init__(self, pattern, since=0):
        # self.level = "ALL"
        self.timestamp = since
        self.regex = re.compile(pattern)
        self.log = logging.getLogger()

    def __call__(self, driver):
        # log entry example
        # {u'source': u'console-api',
        #  u'message': u'http://localhost:5000/?1609167298.58 110:33 "Could not instantiate the following view models due to unresolvable dependencies:"',
        #  u'timestamp': 1609167299977,
        #  u'level': u'SEVERE'}
        for entry in driver.get_log("browser"):
            # self.log.info(entry[u'message'])
            if self.timestamp > entry[u"timestamp"]:
                pass

            if self.regex.match(entry[u"message"]):
                return entry

        return False
