# pytest config file

# adds commandline option --baseurl
def pytest_addoption(parser):
    parser.addoption("--baseurl", action="store", default="http://localhost:5000")


# injects param baseurl in every test function
def pytest_generate_tests(metafunc):
    # This is called for every test. Only get/set command line arguments
    # if the argument is specified in the list of test "fixturenames".
    option_value = metafunc.config.option.baseurl
    if "baseurl" in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("baseurl", [option_value])
