#!/usr/bin/env python
'''

python -m unittest discover -v

python ./test/lib/testTopLevel.py testTopLevel.testTables
python ./test/lib/testTopLevel.py testTopLevel.testMsIfc
python ./test/lib/testTopLevel.py testTopLevel.testLogWidget
python ./test/lib/testTopLevel.py testTopLevel.testCounterWidgets
python ./test/lib/testTopLevel.py testTopLevel.testTimerWidget
python ./test/lib/testTopLevel.py testTopLevel.testStopMove
python ./test/lib/testTopLevel.py testTopLevel.testLogWidget
python ./test/lib/testTopLevel.py testTopLevel.testMotorSelection
'''

import sys, time, os
import unittest
import tngGui.lib.tngGuiClass
import PyTango
from taurus.external.qt import QtGui, QtCore 

mainWidget = None

class dummy(): 
    counterName = None
    timerName = None
    tags = None
    namePattern = None

class testTopLevel( unittest.TestCase):
    
    @classmethod
    def setUpClass( cls): 
        global mainWidget
        if os.getenv( "DISPLAY") != ':0':
            QtGui.QApplication.setStyle( 'Cleanlooks')

        testTopLevel.app = QtGui.QApplication(sys.argv)

        args = dummy()

        mainWidget = tngGui.lib.tngGuiClass.mainMenu( args)
        mainWidget.show()

    def __del__( self): 
        global mainWidget
        if mainWidget is not None:
            mainWidget.close()
            mainWidget = None

    def waitSomeTime( self, xsec): 
        startTime = time.time()
        while (time.time() - startTime) < xsec:
            testTopLevel.app.processEvents()
            time.sleep( 0.01)

    def testTables( self):
        mainWidget.cb_adcDacTable()
        mainWidget.logWidget.append( "Table: ADC/DAC")
        self.waitSomeTime( 1.0)
        mainWidget.cb_counterTable()
        mainWidget.logWidget.append( "Table: Counters")
        self.waitSomeTime( 1.0)
        mainWidget.cb_ioregTable()
        mainWidget.logWidget.append( "Table: IOREGs")
        self.waitSomeTime( 1.0)
        mainWidget.cb_mcaTable()
        mainWidget.logWidget.append( "Table: MCA")
        self.waitSomeTime( 1.0)
        mainWidget.cb_moduleTangoTable()
        mainWidget.logWidget.append( "Table: module Tango")
        self.waitSomeTime( 1.0)
        mainWidget.cb_motorTable()
        mainWidget.logWidget.append( "Table: motors")
        self.waitSomeTime( 1.0)
        mainWidget.cb_vfcadcTable()
        mainWidget.logWidget.append( "Table: vfcadc")
        self.waitSomeTime( 1.0)
        mainWidget.cb_mgTable()
        mainWidget.logWidget.append( "Table: MGs")
        self.waitSomeTime( 1.0)
        
        mainWidget.cb_clear()

    def testMsIfc( self): 
        mainWidget.cb_msIfc()
        mainWidget.logWidget.append( "Widget: launch MS interface")
        self.waitSomeTime( 1.0)
        mainWidget.logWidget.append( "Widget: and close it")
        mainWidget.ms.close()

    def testLogWidget( self):
        mainWidget.logWidget.append( "this text has been sent to the log widget")
        self.waitSomeTime( 1.0)

    def testCounterWidgets( self): 
        '''
        call the attributes widget for a counter
        '''
        dev = None
        for d in tngGui.lib.tngGuiClass.allCounters:
            if d[ 'name'] == 'eh_c01':
                dev = d
                break
        
        f = mainWidget.make_cb_attributes( dev, mainWidget.logWidget)
        mainWidget.logWidget.append( "open attributes widget for eh_c01")
        w_attr = f()
        self.waitSomeTime( 1.0)
        w_attr.close()
        
        f = mainWidget.make_cb_commands( dev, mainWidget.logWidget)
        mainWidget.logWidget.append( "open commands widget for eh_c01")
        w_com = f()
        self.waitSomeTime( 1.0)
        w_com.close()
        
        f = mainWidget.make_cb_properties( dev, mainWidget.logWidget)
        mainWidget.logWidget.append( "open properties widget for eh_c01")
        w_prop = f()
        self.waitSomeTime( 1.0)
        w_prop.close()

    def testTimerWidget( self): 
        '''
        call the timer widget
        '''
        for d in tngGui.lib.tngGuiClass.allTimers:
            if d[ 'name'] == 'eh_t01':
                dev = d
                break
        mainWidget.logWidget.append( "sample time to 3 secs")
        dev[ 'proxy'].sampleTime = 3.

        w_timer = mainWidget.cb_launchTimer()
        mainWidget.logWidget.append( "starting timer")
        dev[ 'proxy'].start()
        while dev[ 'proxy'].state() == PyTango.DevState.MOVING:
            self.waitSomeTime( 0.1)
        mainWidget.logWidget.append( "timer expired")
        self.waitSomeTime( 1.0)
        w_timer.close()

    def testStopMove( self): 
        '''
        call the attributes widget for a counter
        '''
        mainWidget.cb_motorTable()
        dev = None
        for d in tngGui.lib.tngGuiClass.selectedMotors:
            if d[ 'name'] == 'eh_mot65':
                dev = d
                break

        
        f = mainWidget.make_cb_move( dev, mainWidget.logWidget)
        w_move = f()
        self.waitSomeTime( 1.0)

        mainWidget.logWidget.append( "starting at %g" % dev[ 'proxy'].position)
        pos = dev[ 'proxy'].position
        mainWidget.logWidget.append( "moving to %g" % (pos + 1))
        dev[ 'proxy'].position = pos + 1
        self.waitSomeTime( 1.0)
        mainWidget.logWidget.append( "stopping move")
        mainWidget.cb_stopMove()
        self.waitSomeTime( 1.0)
        mainWidget.logWidget.append( "moving back to %g" % pos)
        dev[ 'proxy'].position = pos
        while dev[ 'proxy'].state() == PyTango.DevState.MOVING:
            self.waitSomeTime( 0.1)
        mainWidget.logWidget.append( "we are back at %g" % dev[ 'proxy'].position)
        self.waitSomeTime( 3.0)


    def testLogWidget( self): 
        '''
        test the log widget
        '''
        mainWidget.logWidget.append( "here is some test in the log widget")
        self.waitSomeTime( 1.0)
        mainWidget.logWidget.append( "will be cleared")
        self.waitSomeTime( 1.0)
        mainWidget.logWidget.clear()
        self.waitSomeTime( 1.0)

    def testMotorSelection( self): 
        args = dummy()
        args.namePattern = [ 'eh_mot0']
        tngGui.lib.tngGuiClass.findAllMotors( args)
        self.assertEqual( len( tngGui.lib.tngGuiClass.allMotors), 9)
        args.namePattern = [ 'eh_mot0', 'eh_mot2']
        tngGui.lib.tngGuiClass.findAllMotors( args)
        self.assertEqual( len( tngGui.lib.tngGuiClass.allMotors), 19)

        return 

if __name__ == "__main__":
    unittest.main()
