# TODO: this is only to temporally override OpenCV! SW-1270


class FakeModule:
    # def __init__(self):
    __version__ = "0.0"
    RETR_EXTERNAL = ""

    @staticmethod
    def method(a, b):
        return a + b

    def imwrite(self):
        return


import sys

sys.modules["cv2"] = FakeModule
