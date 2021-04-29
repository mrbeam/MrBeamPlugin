class JobParams:
    class Default:
        INTENSITY_WHITE = 0
        INTENSITY_BLACK = 50
        FEEDRATE_WHITE = 1500
        FEEDRATE_BLACK = 250
        CONTRAST = 1.0
        SHARPENING = 1.0
        DITHERING = False
        BEAM_DIAMETER = 0.15
        PIERCE_TIME = 0
        PIERCE_INTENSITY = 1000
        ENG_COMPRESSOR = 100
        PASSES = 1
        ENG_PASSES = 1

    class Max:
        SPEED = 3000
        COMPRESSOR = 100
        PASSES = 10
        PIERCE_TIME = 300
        LINE_DISTANCE = 1.0
        INTENSITY = 1300
        ENG_PASSES = 4

    class Min:
        SPEED = 50
        COMPRESSOR = 10
        PASSES = 1
        PIERCE_TIME = 0
        LINE_DISTANCE = 0.1
        INTENSITY = 0
        ENG_PASSES = 1
