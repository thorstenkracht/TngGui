$ TngGui.py -h
usage: TngGui.py [-h] [--mca] [-t [TAGS]] [-s] [namePattern [namePattern ...]]

TngGui

positional arguments:
  namePattern  pattern to match the motor names, not applied to other devices

optional arguments:
  -h, --help   show this help message and exit
  --mca        start the MCA widget
  -t [TAGS]    tags matching online.xml tags
  -s           use Spectra for graphics

Examples:
  TngGui.py 
    select all devices from online.xml
  TngGui.py exp_mot01 exp_mot02
    select only two motors, but all other devices
  TngGui.py exp_mot0
    select 9 motors, but all other devices
  TngGui.py -t expert
    select all devices tagged with expert





