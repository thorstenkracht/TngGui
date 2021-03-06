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
import PySpectra
import HasyUtils.MgUtils 

class dummy(): 
    counterName = None
    timerName = None
    tags = None
    namePattern = None

class testMCAMenu( unittest.TestCase):
    
    @classmethod
    def setUpClass( cls): 
        if os.getenv( "DISPLAY") != ':0':
            QtGui.QApplication.setStyle( 'Cleanlooks')

        cls.app = QtGui.QApplication(sys.argv)

        args = dummy()

        cls.mainWidgetClass = tngGui.lib.tngGuiClass.mainMenu( args)

        cls.mcaWidgetClass = mcaWidget.mcaWidget( devices = cls.mainWidgetClass.devices, 
                                              logWidget = cls.mainWidgetClass.logWidget, 
                                              app = cls.app)
        cls.mcaWidgetClass.show()

    def waitSomeTime( self, xsec): 
        startTime = time.time()
        while (time.time() - startTime) < xsec:
            testMCAMenu.app.processEvents()
            time.sleep( 0.01)

    def testMCAMenu( self):
        print( "testMCAMenu.testMCAMenu, start")

        PySpectra.cls()
        PySpectra.delete()

        mg = HasyUtils.MgUtils.MgConf( None, "mg_tnggui", True)
        mg.addTimer( "eh_t01")
        mg.addMCA( "eh_mca01")
        mg.updateConfiguration()
        #
        self.assertEqual( len(PySpectra.getGqeList()), 0)

        self.assertEqual( testMCAMenu.mcaWidgetClass.statusMCA, "Idle")
        testMCAMenu.mcaWidgetClass.sampleTimeLine.setText( "3")
        testMCAMenu.mcaWidgetClass.cb_startMeasurement()
        self.waitSomeTime( 1.0)
        self.assertEqual( testMCAMenu.mcaWidgetClass.statusMCA, "Busy")
        self.waitSomeTime( 3.0)

        lst = PySpectra.getGqeList()
        #
        # now and then len(lst) is not == 1
        #
        if len( lst) != 1: 
            for elm in lst: 
                print( "+++testMCAMenu: %s" % elm.name)
        self.assertEqual( len( lst), 1)
        self.assertEqual( lst[0].name, "eh_mca01")
        testMCAMenu.mcaWidgetClass.cb_clearMeasurement()
        lst = PySpectra.getGqeList()
        self.assertEqual( len( lst), 0)

        testMCAMenu.mcaWidgetClass.sampleTimeLine.setText( "-1")
        testMCAMenu.mcaWidgetClass.cb_startMeasurement()
        self.waitSomeTime( 1.0)
        self.assertEqual( testMCAMenu.mcaWidgetClass.statusMCA, "Busy")

        
        testMCAMenu.mcaWidgetClass.cb_startMeasurement()
        self.waitSomeTime( 1.0)
        self.assertEqual( testMCAMenu.mcaWidgetClass.statusMCA, "Idle")

        testMCAMenu.mcaWidgetClass.close()

        print( "testMCAMenu.testMCAMenu, DONE")

if __name__ == "__main__":
    unittest.main()
