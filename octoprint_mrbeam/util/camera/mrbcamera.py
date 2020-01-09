from itertools import chain

from picamera import PiCamera # The official picamera package
import time
import threading
from octoprint_mrbeam.mrb_logger import mrb_logger
import logging
# import numpy as np
# import cv2
# from octoprint_mrbeam.util.camera import MrbPicWorker
# from multiprocessing import Pool
# import octoprint_mrbeam.util.camera

BRIGHTNESS_TOLERANCE = 80

class LoopThread(threading.Thread):

    def __init__(self, target, stopFlag, args=(), kwargs=None):
        threading.Thread.__init__(self, target=self.loop,)
        # self.daemon = False
        self.running = threading.Event()
        self.running.clear()
        self.stopFlag = stopFlag
        self._logger = mrb_logger('octoprint.plugins.mrbeam.loopthread')

        self.ret = None
        self.t = target
        self._logger.info("Initialised loopthread!")
        self.__args = args
        self.__kw = kwargs or {}

    def run(self):
        try:
            threading.Thread.run(self)
        except Exception as e:
            self._logger.warning("mrbeam.loopthread : %s, %s", e.__class__.__name__, e)


    def loop(self, *args):
        self.stopFlag.clear()
        self.running.set()
        while not self.stopFlag.isSet():
            try:
                self.ret = self.t(*self.__args, **self.__kw)
            except Exception as e:
                self._logger.error("ERROR %s, %s", e.__class__.__name__, e)
            self.running.clear()
            self.running.wait()


class MrbCamera(PiCamera):
    # TODO do stuff here, like the calibration algo
    def __init__(self, worker, stopEvent=None, image_correction=True, *args, **kwargs):
        now = time.time()
        # TODO set sensor mode and framerate etc...
        super(MrbCamera, self).__init__(*args, **kwargs)
        self.vflip = True
        self.hflip = True
        self.awb_mode = 'auto'
        self.stopEvent = stopEvent or threading.Event() # creates an unset event if not given
        self.image_correction_enabled = image_correction
        if not self.image_correction_enabled:
            # self.brightness = 70
            self.color_effects = (128, 128)
        self.start_preview()
        self._logger = mrb_logger("octoprint.plugins.mrbeam.util.camera.mrbcamera")
        self._logger.debug("_prepare_cam() prepared in %ss", time.time() - now)
        self._logger.info("here my args %s -- and kw %s", args, kwargs)
        self.picReady = threading.Event()
        self.busy = threading.Event()
        self.worker = worker
        self.captureLoop = LoopThread(target=self.capture,
                                      stopFlag=stopEvent,
                                      args=(self.worker,),
                                      kwargs={'format': 'jpeg'},)
        # TODO load the default settings

    def apply_best_shutter_speed(self, shutterSpeedMultDelta=2, shutterSpeedDeltas=None):
        """
        Applies to the camera the best shutter speed to detect all the markers
        :param outputs: path to save merged picture. If None : Does not merge and save
        :type outputs: None or str
        :param fpsAvgDelta:
        :param shutterSpeedDeltas:
        :return:
        """
        self.framerate = 4
        self.sensor_mode = 2
        self.iso = 100
        self.exposure_mode = 'off'
        # Capture at the given cam fps and resolution

        autoShutterSpeed = self.exposure_speed
        lastDeltas = [1] # List of shutter speed offsets used (1 = 1 * normal shutter speed)
        # if shutterSpeedDeltas is None: # Creates default behavior
            # construct fpsDeltas from fpsAvgDelta
            # Go for 3 pics around the given average
            # shutterSpeedDeltas = [shutterSpeedMultDelta ** i for i in [-2, 1, ]]  # new shutter speed = shutterSpeedDelta * auto_shutter_speed

        # Always takes the first picture with the auto calibrated mode
        for i, img in enumerate(self.capture_continuous(self.worker, format='jpeg',
                                                        quality=100, use_video_port=True)):
            self._logger.info("sensor : ", self.sensor_mode, " iso : ", self.iso,
                  " gain : ", self.analog_gain, " digital gain : ", self.digital_gain,
                  " brightness : ", self.brightness, " exposure_speed : ", self.exposure_speed)
            # print(self.framerate_delta)
            # out.times.append(1 / (self.framerate + self.framerate_delta))
            # Then change the shutter speed

            # TODO is shutter speed setting for this img set at i - 1 or i - 2 ?

            # The MrbPicWorker already does the brightness measurements in the picture corners for us
            if len(self.worker.good_corner_bright[-1]) == 4:
                self.shutter_speed = int(autoShutterSpeed * lastDeltas[-1])
                return int(autoShutterSpeed * lastDeltas[-1])
            elif not self.worker.allCornersCovered():
                # TODO take darker or brighter pic
                for qd, brightnessDiff in self.worker.detectedBrightness[-1].items():
                    if qd in chain(self.worker.good_corner_bright):
                        # ignore if a previous picture managed to capture it well
                        pass
                    else:
                        # add a new delta brightness
                        delta = int(shutterSpeedMultDelta ** (brightnessDiff // BRIGHTNESS_TOLERANCE)) * lastDeltas[-1]
                        if delta not in shutterSpeedDeltas or delta not in lastDeltas:
                            shutterSpeedDeltas.append(delta)

            if len(shutterSpeedDeltas) == 0:
                print("This last image was good enough")
                break
            elif len(shutterSpeedDeltas) > 0:
                # remember the previous shutter speeds
                lastDeltas.append(int(autoShutterSpeed * shutterSpeedDeltas.pop()))
                # Set shutter speed for the next pic
                self.shutter_speed = int(autoShutterSpeed * lastDeltas[-1])
                # Need to wait for the shutter speed to take effect ??
                time.sleep(.5)  # self.shutter_speed / 10**6 * 10 # transition to next shutter speed

    def async_capture(self, *args, **kw):
        # TODO asynchronously produce img, return None when done
        # self._logger.info("captureLoop running %s, stopFlag %s, shutter speed %s",
        #                   self.captureLoop.running.isSet(),
        #                   self.captureLoop.stopFlag.isSet(),
        #                   self.shutter_speed)
        time.sleep(.1)
        if not self.captureLoop.isAlive():
            self._logger.info("capture loop not alive")
            self.captureLoop.start()
        else:
            self.captureLoop.running.set() # Asks the loop to continue running, see LoopThread

    def wait(self):
        while self.captureLoop.running.isSet():
            # self._logger.info("camera still running ...")
            # TODO return something special to know it has been killed
            if self.stopEvent.isSet(): return
            time.sleep(.2)
        return

    def lastPic(self):
        return self.worker.latest