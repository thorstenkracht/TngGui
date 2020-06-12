#!/usr/bin/env python

#from taurus.external.qt import QtGui, QtCore 
from PyQt4 import QtCore, QtGui

import tngGui.lib.utils as utils

class DefineSignal( QtGui.QMainWindow):
    def __init__( self, parent = None, allDevices = None):
        super( DefineSignal, self).__init__( parent)
        self.parent = parent
        if allDevices is None:
            raise ValueError( "defineSignal.DefineSigna: allDevices == None")
        
        self.allDevices = allDevices
        self.logWidget = self.parent.logWidget
        self.setWindowTitle( "Define Signal")
        w = QtGui.QWidget()
        self.setCentralWidget( w)
        self.layout_v = QtGui.QVBoxLayout()
        w.setLayout( self.layout_v)
        #
        # timer
        #
        self.timerName = self.parent.timerName
        hBox = QtGui.QHBoxLayout()
        w = QtGui.QLabel( "Timer")
        w.setMinimumWidth( 100)
        hBox.addWidget( w)
        self.timerComboBox = QtGui.QComboBox()
        count = 0
        for dev in self.allDevices:
            if dev['type'] == 'timer':
                self.timerComboBox.addItem( dev['name'])
                #
                # initialize the timer comboBox to the current timer
                #
                if dev[ 'name'] == self.timerName:
                    self.timerComboBox.setCurrentIndex( count)
                count += 1

        self.timerComboBox.addItem( 'None')
        hBox.addWidget( self.timerComboBox)
        self.layout_v.addLayout( hBox)
        #
        # counter
        #
        self.counterName = self.parent.counterName
        hBox = QtGui.QHBoxLayout()
        w = QtGui.QLabel( "Counter")
        w.setMinimumWidth( 100)
        hBox.addWidget( w)
        self.counterComboBox = QtGui.QComboBox()
        count = 0
        for dev in self.allDevices:
            if dev['type'] == 'counter' and dev['module'].lower() == 'sis3820' or \
               dev['type'] == 'counter' and dev['module'].lower() == 'tangoattributectctrl' or \
               dev['type'] == 'input_register' and dev['module'].lower() == 'sis3610' or \
               dev[ 'module'].lower() == 'vfcadc' or \
               dev[ 'module'].lower() == 'counter_tango':
                self.counterComboBox.addItem( dev['name'])
                #
                # initialize the counter comboBox to the current counter
                #
                if dev[ 'name'] == self.counterName:
                    self.counterComboBox.setCurrentIndex( count)
                count += 1
        hBox.addWidget( self.counterComboBox)
        self.layout_v.addLayout( hBox)
        #
        # sampleTime
        #
        self.sampleTime = self.parent.sampleTime
        hBox = QtGui.QHBoxLayout()
        w = QtGui.QLabel( "Sample time")
        w.setMinimumWidth( 100)
        hBox.addWidget( w)
        
        self.sampleTimeComboBox = QtGui.QComboBox()
        count = 0
        for st in [ "0.001", "0.01", "0.1", "1.0"]:
            self.sampleTimeComboBox.addItem( st)
            #
            # initialize the sample time comboBox to the current value
            #
            if float( st) == self.sampleTime:
                self.sampleTimeComboBox.setCurrentIndex( count)
            count += 1
        hBox.addWidget( self.sampleTimeComboBox)
        self.layout_v.addLayout( hBox)

        #
        # Status Bar
        #
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar( self.statusBar)

        self.exit = QtGui.QPushButton(self.tr("Exit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        QtCore.QObject.connect( self.exit, QtCore.SIGNAL(  utils.fromUtf8("clicked()")), self.cb_closeDefineSignal)
        self.exit.setShortcut( "Alt+x")
        self.exit.setText( "E&xit")

    def cb_closeDefineSignal( self):
        self.timerName = str(self.timerComboBox.currentText())
        self.counterName = str(self.counterComboBox.currentText())
        self.sampleTime = float( str(self.sampleTimeComboBox.currentText()))
        self.logWidget.append( "signal: %s, %s " % ( self.timerName, self.counterName))
        self.parent.timerName = self.timerName
        self.parent.counterName = self.counterName
        self.parent.sampleTime = self.sampleTime
        self.parent.signalChanged()
        self.close()
