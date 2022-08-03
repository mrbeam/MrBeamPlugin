
def test_get_navbar_label_stable_empty(mrbeam_plugin):
    # The default setting (get_settings_defaults) is software_tier=stable
    assert mrbeam_plugin.get_navbar_label() == ""


def test_get_navbar_label_beta_link(mrbeam_plugin, mocker):
    mocker.patch('octoprint_mrbeam.MrBeamPlugin.is_beta_channel', return_value=True)
    assert mrbeam_plugin.get_navbar_label() == '<a href="https://mr-beam.freshdesk.com/support/solutions/articles/43000507827" target="_blank">BETA</a>'


def test_get_navbar_label_alpha(mrbeam_plugin, mocker):
    mocker.patch('octoprint_mrbeam.MrBeamPlugin.is_alpha_channel', return_value=True)
    assert mrbeam_plugin.get_navbar_label() == "ALPHA"


def test_get_navbar_label_dev(mrbeam_plugin, mocker):
    mocker.patch('octoprint_mrbeam.MrBeamPlugin.is_develop_channel', return_value=True)
    assert mrbeam_plugin.get_navbar_label() == "DEV"


def test_get_navbar_label_combined(mrbeam_plugin, mocker):
    # Change settings to have an initial value in navbar_label
    initial_label = "abcde"
    mrbeam_plugin._settings.set(["navbar_label"], initial_label, force=True)

    mocker.patch('octoprint_mrbeam.MrBeamPlugin.is_alpha_channel', return_value=True)
    assert mrbeam_plugin.get_navbar_label() == initial_label + " | ALPHA"
