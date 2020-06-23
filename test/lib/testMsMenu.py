#!/usr/bin/env python
'''
python -m unittest discover -v
python ./test/lib/testMsMenu.py testMsMenu.testMsMenu
'''

import sys, time, os
import unittest
import tngGui.lib.tngGuiClass
import PyTango
from PyQt4 import QtCore, QtGui
import tngGui.lib.mcaWidget as mcaWidget
import tngGui.lib.macroServerIfc as macroServerIfc
import PySpectra

class dummy(): 
    counterName = None
    timerName = None
    tags = None
    namePattern = None

class testMsMenu( unittest.TestCase):
    
    @classmethod
    def setUpClass( cls): 
        if os.getenv( "DISPLAY") != ':0':
            QtGui.QApplication.setStyle( 'Cleanlooks')

        cls.app = QtGui.QApplication(sys.argv)

        args = dummy()

        cls.mainWidgetClass = tngGui.lib.tngGuiClass.mainMenu( args)

        cls.msIfcClass = macroServerIfc.MacroServerIfc( logWidget = cls.mainWidgetClass.logWidget,
                                                        parent = cls.mainWidgetClass)
        cls.msIfcClass.show()

    def waitSomeTime( self, xsec): 
        startTime = time.time()
        while (time.time() - startTime) < xsec:
            testMsMenu.app.processEvents()
            time.sleep( 0.01)

    def testMsMenu( self):

        print( "testMsMenu.testMsMenu, start")

        self.waitSomeTime( 1.0)

        testMsMenu.msIfcClass.close()

        print( "testMsMenu.testMsMenu, DONE")

if __name__ == "__main__":
    unittest.main()
