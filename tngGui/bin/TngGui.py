#!/usr/bin/env python

import argparse, sys, os, time
import tngGui.lib.tngGuiClass
import PySpectra.graPyspIfc as graPyspIfc
import tngGui.lib.devices as devices
#from taurus.external.qt import QtGui, QtCore 
from PyQt4 import QtCore, QtGui
import tngGui.lib.mcaWidget as mcaWidget
        
def parseCLI():
    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description="TngGui", 
        epilog='''\
Examples:
  TngGui.py 
    select all devices from online.xml
  TngGui.py exp_mot01 exp_mot02
    select only two motors, but all other devices
  TngGui.py exp_mot0
    select 9 motors, but all other devices
  TngGui.py -t expert
    select all devices tagged with expert

  The Python regular expression rules apply.
    ''')
    #
    # notice that 'pattern' is a positional argument
    #
    parser.add_argument( 'namePattern', nargs='*', help='pattern to match the motor names, not applied to other devices')
    #parser.add_argument( '-c', dest='counterName', nargs='?', help='signal counter')
    #parser.add_argument( '-t', dest='timerName', nargs='?', help='signal timer')
    parser.add_argument( '--mca', dest='mca', action="store_true", help='start the MCA widget')
    parser.add_argument( '-t', dest='tags', nargs='?', help='tags matching online.xml tags')
    #parser.add_argument( '-l', dest="list", action="store_true", help='list server and devices')
    #parser.add_argument( '-p', dest="pysp", action="store_true", help='use PySpectra for graphics')
    parser.add_argument( '-s', dest="spectra", action="store_true", help='use Spectra for graphics')
    args = parser.parse_args()

    # 
    args.counterName = None
    args.timerName = None
    # 

    return args

def main():

    args = parseCLI()

    if args.spectra:
        #
        # open spectra here to avoid x-errors on image exit
        #
        graPyspIfc.setSpectra( True)
    else: 
        graPyspIfc.setSpectra( False)

    #
    # before you uncomment the following line check
    #   - whether you can create a pdf file via pysp
    #     this was the error message: 
    #       File "/usr/lib/python2.7/lib-tk/Tkinter.py", line 1819, in __init__
    #         baseName = os.path.basename(sys.argv[0])

    #sys.argv = []
    
    #app = TaurusApplication( sys.argv)
    #
    # if .setStyle() is not called, if TngGui is running
    # locally (not via ssh), the function app.style().metaObject().className()
    # returns QGtkStyle. If this string is supplied to .setStyle()
    # a segmentation fault is generated, locally and remotely.
    # so for remote running we use 'Ceanlooks' which is quite OK.
    #
    if os.getenv( "DISPLAY") != ':0':
        QtGui.QApplication.setStyle( 'Cleanlooks')

    app = QtGui.QApplication(sys.argv)

    devs = devices.Devices( args)

    if args.mca:
        w = mcaWidget.mcaWidget( devices = devs, app = app)
        w.show()
    else:
        if len( devs.allMotors) == 1:
            w = tngGui.lib.tngGuiClass.launchMoveMotor( devs.allMotors[0], devs, app)
            w.show()
        else: 
            mainW = tngGui.lib.tngGuiClass.mainMenu(args, app)
            mainW.show()

    try:
        sys.exit( app.exec_())
    except Exception as e:
        print( repr( e))

if __name__ == "__main__":
    main()
    
