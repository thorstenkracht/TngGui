#!/usr/bin/env python
'''
python -m unittest discover -v
python ./test/lib/testMCAMenu.py testMCAMenu.testMCAMenu
'''

import sys, time, os
import unittest
import tngGui.lib.tngGuiClass
import PyTango
#from taurus.external.qt import QtGui, QtCore 
from PyQt4 import QtCore, QtGui
import tngGui.lib.devices as devices
import tngGui.lib.mcaWidget as mcaWidget

class dummy(): 
    counterName = None
    timerName = None
    tags = None
    namePattern = None

class testMCAMenu( unittest.TestCase):
    
    @classmethod
    def setUpClass( cls): 
        global mainWidget, mcaWidget
        if os.getenv( "DISPLAY") != ':0':
            QtGui.QApplication.setStyle( 'Cleanlooks')

        cls.app = QtGui.QApplication(sys.argv)

        args = dummy()

        cls.mainWidgetClass = tngGui.lib.tngGuiClass.mainMenu( args)

        cls.mcaWidgetClass = mcaWidget.mcaWidget( devices = cls.mainWidgetClass.devices, 
                                              logWidget = cls.mainWidgetClass.logWidget, 
                                              app = cls.app)
        cls.mcaWidgetClass.show()

    def __del__( self):
        pass
        #mainWidget.close()
        #moveWidget.close()
        
    def waitSomeTime( self, xsec): 
        startTime = time.time()
        while (time.time() - startTime) < xsec:
            testMCAMenu.app.processEvents()
            time.sleep( 0.01)

    def testMCAMenu( self):

        print( "testMCAMenu.testMCAMenu, start")

        testMCAMenu.mcaWidgetClass.cb_startMeasurement()
        self.waitSomeTime( 2.0)
        testMCAMenu.mcaWidgetClass.cb_stopMeasurement()
        self.waitSomeTime( 1.0)

        testMCAMenu.mcaWidgetClass.close()

        print( "testMCAMenu.testMCAMenu, DONE")

if __name__ == "__main__":
    unittest.main()
