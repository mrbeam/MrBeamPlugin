import pytest

from octoprint_mrbeam.migration.Mig005 import Mig005InstallNTP


@pytest.fixture
def migration005():
    return Mig005InstallNTP(None)


@pytest.mark.parametrize(
    "beamos_version,should_run",
    [
        ("1.21.0", False),
        ("0.21.0", False),
        ("0.20.2", False),
        ("0.20.1", True),
        ("0.20.0", True),
        ("0.19.0", True),
        ("0.18.0", True),
        ("0.18.1", True),
        ("0.18.2", True),
        ("0.14.0", False),
        (None, False),
        ("14.0", False),
        ("0", False),
    ],
)
def test_migration_should_run(beamos_version, should_run, migration005):
    assert migration005.shouldrun(Mig005InstallNTP, beamos_version) == should_run


def test_migration_id(migration005):
    assert migration005.id == "005"


def test_migration_commands_executed(migration005, mocker):
    mocker.patch.object(migration005, "exec_cmd", autospec=True)
    migration005.run()
    migration005.exec_cmd.assert_any_call(
        "sudo apt install {}/files/migrate/Mig005/libopts25_1_5.18.12-4_armhf.deb -y".format(
            __package_path__
        )
    )
    migration005.exec_cmd.assert_any_call(
        "sudo apt install {}/files/migrate/Mig005/ntp_1_4.2.8p12+dfsg-4_armhf.deb -y".format(
            __package_path__
        )
    )
    migration005.exec_cmd.assert_any_call(
        "sudo apt install {}/files/migrate/Mig005/sntp_1_4.2.8p12+dfsg-4_armhf.deb -y".format(
            __package_path__
        )
    )
