#!/usr/bin/env python

#from taurus.external.qt import QtGui, QtCore 
from PyQt4 import QtCore, QtGui

import HasyUtils.MgUtils
import tngGui.lib.utils as utils
import tngGui.lib.definitions as definitions

class SelectMcaAndTimer( QtGui.QMainWindow):
    """
    selects MCAs and stores them in parent.selectedMCAs
    selects a timer and stores it in parent.selectedTimer
    """
    def __init__( self, devices = None, parent = None):
        super( SelectMcaAndTimer, self).__init__( parent)
        self.parent = parent
        if devices is None:
            raise ValueError( "SelectMcaAndTimer: devices == None")
        
        self.devices = devices
        self.logWidget = self.parent.logWidget
        self.setWindowTitle( "Select MCA and Timer")

        self.prepareWidgets()

        # 
        #
        self.refreshTimer = QtCore.QTimer(self)
        self.refreshTimer.start( definitions.TIMEOUT_REFRESH_MOTOR) 
        self.refreshTimer.timeout.connect( self.cb_refreshSelectWidget)
        
        return 

    def prepareStatusBar( self): 
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar( self.statusBar)

        self.exit = QtGui.QPushButton(self.tr("Exit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        self.exit.clicked.connect( self.cb_closeWidget)
        self.exit.setShortcut( "Alt+x")
        self.exit.setText( "E&xit")

    def prepareMenuBar( self):

        self.menuBar = QtGui.QMenuBar()
        self.setMenuBar( self.menuBar)

        self.fileMenu = self.menuBar.addMenu('&File')
        
        self.exitAction = QtGui.QAction('E&xit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect( self.cb_closeWidget)
        self.fileMenu.addAction( self.exitAction)

        #
        # the activity menubar: help and activity
        #
        self.menuBarActivity = QtGui.QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarActivity, QtCore.Qt.TopRightCorner)

        self.helpMenu = self.menuBarActivity.addMenu('Help')
        self.helpSelect = self.helpMenu.addAction(self.tr("Select Devices"))
        self.helpSelect.triggered.connect( self.cb_helpSelect)

        self.activityIndex = 0
        self.activity = self.menuBarActivity.addMenu( "_")

        return 

    def prepareWidgets( self): 

        w = QtGui.QWidget()
        self.setCentralWidget( w)
        self.layout_v = QtGui.QVBoxLayout()
        w.setLayout( self.layout_v)

        hBox = QtGui.QHBoxLayout()
        
        vBoxTimer = QtGui.QVBoxLayout()
        for dev in self.devices.allTimers:
            w = QtGui.QCheckBox( dev[ 'name'])
            w.stateChanged.connect( self.make_cb_selected( w, dev, self.parent.selectedTimers))
            for devTemp in self.parent.selectedTimers: 
                if devTemp[ 'name'] == dev[ 'name']: 
                    w.setChecked( True)
                    
            vBoxTimer.addWidget( w)
        hBox.addLayout( vBoxTimer)
        
        vBoxMCA = QtGui.QVBoxLayout()
        for dev in self.devices.allMCAs:
            w = QtGui.QCheckBox( dev[ 'name'])
            w.stateChanged.connect( self.make_cb_selected( w, dev, self.parent.selectedMCAs))
            for devTemp in self.parent.selectedMCAs: 
                if devTemp[ 'name'] == dev[ 'name']: 
                    w.setChecked( True)
            vBoxMCA.addWidget( w)
        hBox.addLayout( vBoxMCA) 
        
        self.layout_v.addLayout( hBox)

        self.prepareMenuBar()
        self.prepareStatusBar()

    def cb_helpSelect(self):
        QtGui.QMessageBox.about(self, self.tr("Help Select"), self.tr(
                "<h3> Help Selecte Timers and MCAs </h3>"
                "<ul>"
                "<li> mg_tnggui stores the selection</li>"
                "</ul>"
                ))

    def cb_refreshSelectWidget( self): 
        #
        # update the widgets
        #

        self.activityIndex += 1
        if self.activityIndex > (len( definitions.ACTIVITY_SYMBOLS) - 1):
            self.activityIndex = 0
        self.activity.setTitle( definitions.ACTIVITY_SYMBOLS[ self.activityIndex])

        return 

    def updateMg( self): 
        """
        the MG mg_tnggui keeps track of the device selection
        after something has changed, this MG will be updated
        """
        if len( self.parent.selectedTimers) == 0:
            raise ValueError( "selectMcaAndTimer: len( selectedTimers) == 0")
        if len( self.parent.selectedMCAs) == 0:
            raise ValueError( "selectMcaAndTimer: len( selectedMCAs) == 0")

        
        masterTimer = self.parent.selectedTimers[0][ 'name']

        extraTimers = ""
        if len( self.parent.selectedTimers) > 1:
            length = len( self.parent.selectedTimers)
            for i in range( 1, length): 
                extraTimers += self.parent.selectedTimers[i][ 'name']
                if i < (length - 1): 
                    extraTimers += ","

        mcas = ""
        length = len( self.parent.selectedMCAs)
        for i in range( length): 
            mcas += self.parent.selectedMCAs[i][ 'name']
            if i < (length - 1): 
                mcas += ","

        HasyUtils.MgUtils.setMg( mgName = "mg_tnggui", timer = masterTimer, extraTimers = extraTimers, mcas = mcas)
        return 
        

    def make_cb_selected( self, w, dev, devList):
        def cb():
            if w.isChecked(): 
                flagFound = False
                for devTemp in devList:
                    if devTemp[ 'name'] == dev[ 'name']: 
                        flagFound = True
                if not flagFound: 
                    devList.append( dev) 
            else: 
                for devTemp in devList:
                    if devTemp[ 'name'] == dev[ 'name']: 
                        devList.remove( devTemp)
            self.updateMg()
        return cb

    def cb_closeWidget( self):
        self.close()
        self.parent.reconfigureWidget()
        return 
