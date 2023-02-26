import pytest
from mock.mock import patch, call

from octoprint_mrbeam.camera.label_printer import LabelPrinter


@pytest.mark.parametrize(
    "model, model_short, ean_num_single, ean_num_bundle",
    [
        ("MRBEAM2_DC", "DC", "4260625360156", "4260625360163"),
        ("MRBEAM2_DC_S", "DC [S]", "4260625361023", "4260625361030"),
        ("MRBEAM2_DC_X", "DC [x]", "4260625362136", "4260625362143"),
    ],
    ids=["DC", "DC [S]", "DC [x]"],
)
def test_print_ean_labels(
    model, model_short, ean_num_single, ean_num_bundle, mrbeam_plugin
):
    # Arrange
    with patch(
        "octoprint_mrbeam.util.device_info.DeviceInfo.get_model",
        return_value=model,
    ):
        with patch.object(
            LabelPrinter, "_print", return_value=(True, "")
        ) as mock_print:
            labelprinter = LabelPrinter(mrbeam_plugin)

            # Act
            ean_label_ok, ean_label_out = labelprinter.print_ean_labels()

            # Assert
            calls = [
                call(
                    "192.168.1.202",
                    """
			^XA
			^FWN
			^FO40,20^BY3
			^BEN,100,Y,N
			^FD{ean_num}^FS
			^CF0,30
			^FO10,180^FDMr Beam II {model}^FS
			^CF0,45
			^FO240,168^FD{prod_string}^FS
			^XZ
		""".format(
                        model=model_short, prod_string="single", ean_num=ean_num_single
                    ),
                ),
                call(
                    "192.168.1.202",
                    """
			^XA
			^FWN
			^FO40,20^BY3
			^BEN,100,Y,N
			^FD{ean_num}^FS
			^CF0,30
			^FO10,180^FDMr Beam II {model}^FS
			^CF0,45
			^FO240,168^FD{prod_string}^FS
			^XZ
		""".format(
                        model=model_short, prod_string="bundle", ean_num=ean_num_bundle
                    ),
                ),
            ]
            mock_print.assert_has_calls(calls, any_order=False)
            assert mock_print.call_count == 2
            assert ean_label_ok, ean_label_out == (True, "")


def test_print_ean_label_unknown_model(mrbeam_plugin):
    # Arrange
    with patch(
        "octoprint_mrbeam.util.device_info.DeviceInfo.get_model",
        return_value="UNKNOWN_MODEL",
    ):
        labelprinter = LabelPrinter(mrbeam_plugin)

        # Act
        ean_label_ok, ean_label_out = labelprinter.print_ean_labels()

        # Assert
        assert ean_label_ok is False
        assert ean_label_out == "No EAN numbers for model UNKNOWN_MODEL"
