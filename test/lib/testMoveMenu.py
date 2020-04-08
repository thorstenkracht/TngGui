#!/usr/bin/env python
'''
python -m unittest discover -v
python ./test/lib/testMoveMenu.py testMoveMenu.testMoveMenu
python ./test/lib/testMoveMenu.py testMoveMenu.testMoveToLine
python ./test/lib/testMoveMenu.py testMoveMenu.testMoveToMax
'''

import sys, time, os
import unittest
import tngGui.lib.tngGuiClass
import PyTango
#from taurus.external.qt import QtGui, QtCore 
from PyQt4 import QtCore, QtGui
import tngGui.lib.devices as devices

mainWidget = None 
dev65 = None
moveWidget = None

class dummy(): 
    counterName = None
    timerName = None
    tags = None
    namePattern = None

class testMoveMenu( unittest.TestCase):
    
    @classmethod
    def setUpClass( cls): 
        global mainWidget, dev65, moveWidget
        if os.getenv( "DISPLAY") != ':0':
            QtGui.QApplication.setStyle( 'Cleanlooks')

        testMoveMenu.app = QtGui.QApplication(sys.argv)

        args = dummy()

        devs = devices.Devices( None)

        mainWidget = tngGui.lib.tngGuiClass.mainMenu( args)

        dev65 = None
        for d in devs.allMotors:
            if d[ 'name'] == 'eh_mot65':
                dev65 = d
                break
        else:
            raise ValueError( "testMoveMenu.setUpClass: eh_mot65 not found")
            
        f = mainWidget.make_cb_move( dev65, mainWidget.logWidget)
        moveWidget = f()

        mainWidget.show()

    def __del__( self):
        pass
        #mainWidget.close()
        #moveWidget.close()
        
    def waitSomeTime( self, xsec): 
        startTime = time.time()
        while (time.time() - startTime) < xsec:
            testMoveMenu.app.processEvents()
            time.sleep( 0.01)

    def testMoveMenu( self):

        w_defSig = moveWidget.cb_defineSignal()
        self.waitSomeTime( 1.0)
        w_defSig.close()
        
        f = mainWidget.make_cb_attributes( dev65, mainWidget.logWidget)
        w_attr = f()
        self.waitSomeTime( 1.0)
        w_attr.close()

        f = mainWidget.make_cb_commands( dev65, mainWidget.logWidget)
        w_com = f()
        self.waitSomeTime( 1.0)
        w_com.close()

        f = mainWidget.make_cb_properties( dev65, mainWidget.logWidget)
        w_prop = f()
        self.waitSomeTime( 1.0)
        w_prop.close()

        f = mainWidget.make_cb_mb3( dev65, mainWidget.logWidget)
        w_mb3 = f()
        self.waitSomeTime( 1.0)
        w_mb3.close()

        pos = moveWidget.motorProxy.position
        moveWidget.logWidget.append( "moving to %g" % (pos - 1))
        moveWidget.moveTarget( pos - 1)
        moveWidget.logWidget.append( "moving back to %g" % (pos))
        moveWidget.moveTarget( pos)

    def testMoveToLine( self):
        #
        # fill move-to-line
        #
        mainWidget.logWidget.append( "testing moveToLine")
        pos = moveWidget.motorProxy.position
        mainWidget.logWidget.append( "insert %g" % (pos - 0.5))
        moveWidget.moveToLine.insert( "%g" % (pos - 0.5))
        mainWidget.logWidget.append( "and start")
        moveWidget.moveTo()
        while moveWidget.motorProxy.state() == PyTango.DevState.MOVING:
            self.waitSomeTime( 0.1)
        mainWidget.logWidget.append( "insert %g" % (pos))
        moveWidget.moveToLine.insert( "%g" % pos )
        mainWidget.logWidget.append( "and start")
        moveWidget.moveTo()
        while moveWidget.motorProxy.state() == PyTango.DevState.MOVING:
            self.waitSomeTime( 0.1)
        mainWidget.logWidget.append( "test done")

    def testMoveToMax( self):
        self.testMoveToLine()
        mainWidget.logWidget.append( "move to max")
        moveWidget.cb_toMax()
        while moveWidget.motorProxy.state() == PyTango.DevState.MOVING:
            self.waitSomeTime( 0.1)
        mainWidget.logWidget.append( "move to max done")

if __name__ == "__main__":
    unittest.main()
