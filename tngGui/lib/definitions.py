#!/usr/bin/env python

TIMEOUT_REFRESH = 500
TIMEOUT_REFRESH_MOTOR = 500
ACTIVITY_SYMBOLS = ['|', '/', '-', '\\', '|', '/', '-', '\\'] 
SLIDER_RESOLUTION = 500
POSITION_WIDTH = 150
POSITION_WIDTH_PROP = 200
BLUE_MOVING = "#a0b0ff"
RED_ALARM = "#ff8080"
MAGENTA_DISABLE = "#ff1dce"
GREEN_OK = "#70ff70"
GREY_NORMAL = "#f0f0f0"

channelsDct = { 
    '512': 0,
    '1024': 1,
    '2048': 2,
    '4096': 3,
    '8192': 4,
}

channelsArr = [ '512', '1024', '2048', '4096', '8192']
