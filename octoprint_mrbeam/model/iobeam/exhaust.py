class ExhaustModelInitializationError(Exception):
    pass


class Device:
    # dataset_type: int
    # ext_power: bool
    # ext_voltage: float
    # fan_power: float
    # mode: str
    # pressure: int
    # serial_num: int
    # smart_lock: bool
    # type: int

    def __init__(
        self,
        dataset_type,
        ext_power,
        ext_voltage,
        fan_power,
        mode,
        pressure,
        serial_num,
        smart_lock,
        type,
    ):
        self.dataset_type = dataset_type
        self.ext_power = ext_power
        self.ext_voltage = ext_voltage
        self.fan_power = fan_power
        self.mode = mode
        self.pressure = pressure
        self.serial_num = serial_num
        self.smart_lock = smart_lock
        self.type = type

    @staticmethod
    def from_dict(dictonary):
        """

        Args:
            dictonary (dict):

        Returns:

        """
        try:
            return Device(
                dictonary.get("dataset_type"),
                dictonary.get("ext_power"),
                dictonary.get("ext_voltage"),
                dictonary.get("fan_power"),
                dictonary.get("mode"),
                dictonary.get("pressure"),
                dictonary.get("serial_num"),
                dictonary.get("smart_lock"),
                dictonary.get("type"),
            )
        except TypeError as e:
            raise ExhaustModelInitializationError(
                "Can't init device from dict: {}".format(dictonary)
            )
