#!/usr/bin/env python

#from taurus.external.qt import QtGui, QtCore 
from PyQt4 import QtCore, QtGui

import PyTango
import numpy
import math, time, sys, os
import HasyUtils
import tngGui.lib.utils as utils
import tngGui.lib.definitions as definitions
import PySpectra.graPyspIfc as graPyspIfc
import PySpectra.pySpectraGuiClass
import PySpectra.pyspMonitorClass
import tngGui.lib.devices as devices
import tngGui.lib.selectMcaAndTimer as selectMcaAndTimer

TIMEOUT_MCA_BUSY = 100

class mcaWidget( QtGui.QMainWindow):
    def __init__( self, dev = None, devices = None, logWidget = None, app = None, parent = None):
        super( mcaWidget, self).__init__( parent)

        if PySpectra.InfoBlock.monitorGui is None:
            PySpectra.InfoBlock.setMonitorGui( self)
        self.dev = dev
        self.devices = devices
        if self.devices == None: 
            self.devices = devices.Devices()
        self.logWidget = logWidget
        self.app = app
        self.parent = parent
        lst = HasyUtils.getMgElements( "mg_tnggui")
        if len( lst) == 0: 
            self.selectedTimers = self.devices.allTimers[:]
            self.selectedMCAs = self.devices.allMCAs[:]
        else: 
            #
            # ['eh_t01', 'eh_c01', 'eh_mca01']
            #
            self.selectedTimers = []
            for elm in lst: 
                if elm.find( '_t0') != -1: 
                    self.selectedTimers.append( self.getDev( elm))
            self.selectedMCAs = []
            for elm in lst: 
                if elm.find( '_mca') != -1: 
                    self.selectedMCAs.append( self.getDev( elm))
        self.selectedTimers.sort()
        self.selectedMCAs.sort()
        self.mcaOntop = self.selectedMCAs[0]
        #
        # set the window title
        #
        if self.dev is not None: 
            self.setWindowTitle( "MCA %s" % self.dev[ 'name'])
        else: 
            self.setWindowTitle( "MCA")
        self.move( 10, 750)

        #
        # prepare widgets
        #
        self.prepareWidgets()

        self.flagClosed = False
        self.pyspGui = None
        self.statusMCA = "Idle"
        self.flagTimerWasBusy = False
        #
        # updateTimeMCA: the interval between MCA readings
        #
        self.updateTimeMCA = 1.
        self.timeDead = 0.
        # 
        #
        self.refreshTimer = QtCore.QTimer(self)
        self.refreshTimer.start( definitions.TIMEOUT_REFRESH_MOTOR) 
        self.refreshTimer.timeout.connect( self.cb_refreshMCAWidget)
        #
        # the timer which is busy while the MCAs are active
        #
        self.mcaTimer = QtCore.QTimer( self)
        self.mcaTimer.timeout.connect( self.updateMeasurement)
        
        return 

    def getDev( self, name): 
        """
        return the dictionary belonging to name
        """
        for dev in self.devices.allDevices: 
            if name == dev[ 'name']:
                return dev
        return None

    def cb_refreshMCAWidget( self): 
        #
        # update the widgets
        #

        self.activityIndex += 1
        if self.activityIndex > (len( definitions.ACTIVITY_SYMBOLS) - 1):
            self.activityIndex = 0
        self.activity.setTitle( definitions.ACTIVITY_SYMBOLS[ self.activityIndex])

        #print( "refreshMCAWidget %s" % self.statusMCA)
        return 

    def prepareWidgets( self):
        w = QtGui.QWidget()
        self.layout_v = QtGui.QVBoxLayout()
        w.setLayout( self.layout_v)
        self.setCentralWidget( w)
        #
        # sample time, total time, remaining
        #
        hBox = QtGui.QHBoxLayout()
        hBox.addWidget( QtGui.QLabel( "Sample time"))
        self.sampleTimeLine = QtGui.QLineEdit()
        self.sampleTimeLine.setFixedWidth( 50)
        self.sampleTimeLine.setAlignment( QtCore.Qt.AlignRight)
        self.sampleTimeLine.setText( "3")
        hBox.addWidget( self.sampleTimeLine)
        #
        # total time
        #
        hBox.addWidget( QtGui.QLabel( "Total time"))
        self.totalTimeLabel = QtGui.QLabel( "")
        self.totalTimeLabel.setFixedWidth( 50)
        hBox.addWidget( self.totalTimeLabel)
        #
        # remaining time
        #
        hBox.addWidget( QtGui.QLabel( "Remaining"))
        self.remainingTimeLabel = QtGui.QLabel()
        self.remainingTimeLabel.setFixedWidth( 50)
        hBox.addWidget( self.remainingTimeLabel)
        #
        # dead time
        #
        hBox.addWidget( QtGui.QLabel( "Dead time[%]"))
        self.deadTimeLabel = QtGui.QLabel()
        self.deadTimeLabel.setFixedWidth( 50)
        hBox.addWidget( self.deadTimeLabel)
        #
        # status
        #
        self.statusLabel = QtGui.QLabel( "Idle")
        self.statusLabel.setFixedWidth( 50)
        self.statusLabel.setAlignment( QtCore.Qt.AlignCenter)
        self.statusLabel.setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
        hBox.addWidget( self.statusLabel)
        self.layout_v.addLayout( hBox)

        #
        # the devices frame
        #
        frame = QtGui.QFrame()
        frame.setFrameShape( QtGui.QFrame.Box)
        self.layout_v.addWidget( frame)
        self.layout_frame_v = QtGui.QVBoxLayout()
        frame.setLayout( self.layout_frame_v)

        hBox = QtGui.QHBoxLayout()
        #
        # MCA 
        #
        self.mcaComboBox = QtGui.QComboBox()
        for dev in self.selectedMCAs: 
            self.mcaComboBox.addItem( dev[ 'name'])
        hBox.addWidget( self.mcaComboBox)
        #
        # channels
        #
        hBox.addWidget( QtGui.QLabel( 'Channels:'))
        self.channelsComboBox = QtGui.QComboBox()
        for chan in definitions.channelsArr:
            self.channelsComboBox.addItem( chan)
        self.channelsComboBox.setCurrentIndex( definitions.channelsDct[ '%d' % self.mcaOntop[ 'proxy'].DataLength])
        
        hBox.addWidget( self.channelsComboBox)
        #
        # total counts
        #
        hBox.addWidget( QtGui.QLabel( 'Total:'))
        self.totalLabel = QtGui.QLabel( "")
        hBox.addWidget( self.totalLabel)
        self.layout_frame_v.addLayout( hBox)

        #
        # Menu Bar
        #
        self.menuBar = QtGui.QMenuBar()
        self.setMenuBar( self.menuBar)
        self.prepareMenuBar()

        #
        # Status Bar
        #
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar( self.statusBar)
        self.prepareStatusBar()

        #
        # create the log widget, if necessary
        #
        if self.logWidget is None:
             self.logWidget = QtGui.QTextEdit()
             self.logWidget.setMaximumHeight( 150)
             self.logWidget.setReadOnly( 1)
             self.layout_v.addWidget( self.logWidget)
             self.w_clearLog = QtGui.QPushButton(self.tr("ClearLog")) 
             self.w_clearLog.setToolTip( "Clear log widget")
             self.statusBar.addPermanentWidget( self.w_clearLog) # 'permanent' to shift it right
             self.w_clearLog.clicked.connect( self.logWidget.clear)

        self.exit = QtGui.QPushButton(self.tr("&Exit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        self.exit.clicked.connect( self.cb_closeMCAWidget)
        self.exit.setShortcut( "Alt+x")
        #
        # connect the callback functions at the end because the depend on each other
        #
        self.channelsComboBox.currentIndexChanged.connect( self.cb_channelsChanged)
        self.mcaComboBox.currentIndexChanged.connect( self.cb_mcaChanged)
        return 

    def prepareMenuBar( self):

        self.fileMenu = self.menuBar.addMenu('&File')

        self.writeFileAction = QtGui.QAction('Write .fio file', self)        
        self.writeFileAction.triggered.connect( self.cb_writeFile)
        self.fileMenu.addAction( self.writeFileAction)

        self.hardcopyAction = QtGui.QAction('Hardcopy', self)        
        if graPyspIfc.getSpectra(): 
            self.hardcopyAction.setStatusTip('Create postscript output')
        else:
            self.hardcopyAction.setStatusTip('Create pdf output')
        self.hardcopyAction.triggered.connect( self.cb_hardcopy)
        self.fileMenu.addAction( self.hardcopyAction)

        self.hardcopyActionA6 = QtGui.QAction('Hardcopy A6', self)        
        if graPyspIfc.getSpectra(): 
            self.hardcopyActionA6.setStatusTip('Create postscript output, A6')
        else:
            self.hardcopyActionA6.setStatusTip('Create pdf output, A6')
        self.hardcopyActionA6.triggered.connect( self.cb_hardcopyA6)
        self.fileMenu.addAction( self.hardcopyActionA6)
        
        self.exitAction = QtGui.QAction('E&xit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect( self.cb_closeMCAWidget)
        self.fileMenu.addAction( self.exitAction)

        self.optionsMenu = self.menuBar.addMenu('Options')

        self.selectDevicesAction = QtGui.QAction('Select devices', self)       
        self.selectDevicesAction.triggered.connect( self.cb_selectDevices)
        self.optionsMenu.addAction( self.selectDevicesAction)
        #
        # the activity menubar: help and activity
        #
        self.menuBarActivity = QtGui.QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarActivity, QtCore.Qt.TopRightCorner)

        self.helpMenu = self.menuBarActivity.addMenu('Help')
        self.helpMCA = self.helpMenu.addAction(self.tr("MCA"))
        self.helpMCA.triggered.connect( self.cb_helpMCA)

        self.activityIndex = 0
        self.activity = self.menuBarActivity.addMenu( "_")

        return 

    def prepareStatusBar( self): 
        self.w_startButton = QtGui.QPushButton(self.tr("&Start")) 
        self.w_startButton.setToolTip( "Start the MCAs")
        self.statusBar.addPermanentWidget( self.w_startButton) # 'permanent' to shift it right
        self.w_startButton.clicked.connect( self.cb_startMeasurement)
        self.w_startButton.setShortcut( "Alt+a")

        self.w_clearButton = QtGui.QPushButton(self.tr("Clear")) 
        self.w_clearButton.setToolTip( "Start the MCAs")
        self.statusBar.addPermanentWidget( self.w_clearButton) # 'permanent' to shift it right
        self.w_clearButton.clicked.connect( self.cb_clearMeasurement)
        self.w_clearButton.setShortcut( "Alt+a")

        return 

    def reconfigureWidget( self): 
        """
        called from selectTimerAndMCAs
        """
        lst = HasyUtils.getMgElements( "mg_tnggui")
        if len( lst) == 0:
            self.logWidget.append( "reconfigureWidget: mg_tnggui is empty")
            return 
        #
        # ['eh_t01', 'eh_c01', 'eh_mca01']
        #
        self.selectedTimers = []
        for elm in lst: 
            if elm.find( '_t0') != -1: 
                self.selectedTimers.append( self.getDev( elm))
        self.selectedMCAs = []
        for elm in lst: 
            if elm.find( '_mca') != -1: 
                self.selectedMCAs.append( self.getDev( elm))

        self.selectedTimers.sort()
        self.selectedMCAs.sort()
        self.mcaComboBox.clear()
        for dev in self.selectedMCAs: 
            self.mcaComboBox.addItem( dev[ 'name'])
        self.mcaOntop = self.selectedMCAs[0]
        return 

    def stopMeasurement( self):
        """
        stop the timers
        stop the MCAs
        """
        self.stopTimers()
        self.stopMCAs()
        self.statusMCA = "Idle"
        self.statusLabel.setText( self.statusMCA)
        self.statusLabel.setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
        self.w_startButton.setText( self.tr("&Start")) 
        self.timeRemaining = 0.
        return 
        
    def checkTimers( self): 
        """
        return True, if one of the selectedTimers is busy
        """
        for tm in self.selectedTimers: 
            if tm[ 'proxy'].state() == PyTango.DevState.MOVING: 
                return True
        return False
            
    def resetCounters( self): 
        return 
    def readCounters( self): 
        return 
    def preparePetraCurrent( self): 
        return 

    def calcROIs( self): 
        
        return 

    def updateMeasurement( self): 
        """
        """

        if self.checkTimers(): 
            return 

        if self.flagTimerWasBusy: 
            self.stopMCAs()
            self.readMCAs()
            self.displayMCAs()
            self.calcROIs()
            self.readCounters()
            self.preparePetraCurrent()
            self.flagTimerWasBusy = False

            if self.timeTotal > 0:
                now = time.time()
                timeDeadTemp = 100.*( now - self.timeStartElapsed - self.timeTotal)/(now - self.timeStartElapsed)
                if timeDeadTemp > 0.:
                    self.timeDead = timeDeadTemp
                    self.deadTimeLabel.setText( "%g" % self.timeDead)

        timeGate = 0
        #
        # '-1' -> forever
        #
        if self.timeRemaining != 0: 
            if self.updateTimeMCA < self.timeRemaining or self.timeRemaining == -1.:
                timeGate = self.updateTimeMCA
            else:
                timeGate = self.timeRemaining

            self.clearMCAs()
            self.startMCAs()

            self.resetCounters()
            
            self.startTimers( timeGate)
            self.flagTimerWasBusy = True
            if self.timeRemaining != -1.:
                self.timeRemaining -= timeGate
                self.remainingTimeLabel.setText( "%g" % self.timeRemaining)

            self.timeTotal += timeGate
            self.totalTimeLabel.setText( "%g" % self.timeTotal)

        else: 
            self.statusMCA = "Idle"
            self.statusLabel.setText( self.statusMCA)
            self.statusLabel.setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)

            self.configureWidgetsBusy( False)

        # update the menu and re-call this function
        #self.cb_refreshMCAWidget()

        if timeGate: 
            self.mcaTimer.start( TIMEOUT_MCA_BUSY)
            self.w_startButton.setText( "Stop")
        else: 
            self.mcaTimer.stop()
            self.w_startButton.setText( "Start")

        return 
        
    def cb_clearMeasurement( self):
        """
        """
        self.stopTimers()
        self.stopMCAs()

        graPyspIfc.cls()
        graPyspIfc.delete()

        self.timeDead = 0
        self.deadTimeLabel.setText( "%g" % self.timeDead)
        self.timeTotal = 0
        self.totalTimeLabel.setText( "%g" % self.timeTotal)

        return 

    def cb_startMeasurement( self):
        """
        start MCAs and timers
        """
        if self.statusMCA.upper() == "BUSY":
            print( "cb_startMeasurement: is busy, stopping")
            self.stopTimers()
            self.stopMCAs()
            self.timeRemaining = 0
            self.updateMeasurement()
            return 
        #
        # get the sample time from the QlineEdit
        #
        temp = self.sampleTimeLine.text()
        if len( temp) == 0:
            self.logWidget.append( "startMeasurement: specify sample time")
            return
        self.sampleTime = float( temp)
        
        self.timeRemaining = self.sampleTime
        self.timeStartElapsed = time.time()
        self.timeTotal = 0

        self.configureWidgetsBusy( True)
        self.statusMCA = "Busy"
        self.statusLabel.setText( self.statusMCA)
        self.statusLabel.setStyleSheet( "background-color:%s;" % definitions.BLUE_MOVING)
        
        self.statusLabel.setText( self.statusMCA)
        self.w_startButton.setText( self.tr("&Stop")) 

        graPyspIfc.setTitle( "Started %s" % time.strftime("%d %b %Y %H:%M:%S", time.localtime()))
        self.updateMeasurement()
        
        return

    def stopTimers( self):
        for timer in self.selectedTimers:
            timer[ 'proxy'].stop()
        return
            
    def startTimers( self, gateTime):
        for timer in self.selectedTimers:
            timer[ 'proxy'].sampleTime = gateTime
            timer[ 'proxy'].start()

    def startMCAs( self):
        for mca in self.selectedMCAs:
            mca[ 'proxy'].start()

    def clearMCAs( self):
        for mca in self.selectedMCAs:
            mca[ 'proxy'].clear()

    def stopMCAs( self):
        for mca in self.selectedMCAs:
            mca[ 'proxy'].stop()
        
    def displayMCAs( self): 
        graPyspIfc.cls()
        graPyspIfc.display()
        return 

    def readMCAs( self): 
        for mca in self.selectedMCAs:
            mca[ 'proxy'].read()
            if 'scan' in mca: 
                if len( mca[ 'scan'].x) != mca[ 'proxy'].DataLength:
                    del mca[ 'scan']
                    mca[ 'scan'] = graPyspIfc.Scan( name = mca[ 'name'], 
                                                    y = mca[ 'proxy'].data)
                else: 
                    mca[ 'scan'].y = numpy.copy( mca[ 'proxy'].data)
            else: 
                mca[ 'scan'] = graPyspIfc.Scan( name = mca[ 'name'], 
                                                y = mca[ 'proxy'].data)

        return 

    def cb_channelsChanged( self):
        """
        change the channel number of the current MCA
        """
        print( "channelsChanged %s  to %s " % (self.mcaOntop[ 'name'], self.channelsComboBox.currentText()))
        self.mcaOntop[ 'proxy'].DataLength = int( self.channelsComboBox.currentText())
        return 

    def cb_mcaChanged( self):
        """
        called when the current MCA is changed
        """
        self.mcaOntop = self.getDev( self.mcaComboBox.currentText())
        print( "mcaChanged to %s" % self.mcaOntop[ 'name'])
        print( "mcaChanged channel from HW %d, index %d" % 
               (self.mcaOntop[ 'proxy'].DataLength, definitions.channelsDct[ '%d' % self.mcaOntop[ 'proxy'].DataLength]))
        self.channelsComboBox.setCurrentIndex( definitions.channelsDct[ '%d' % self.mcaOntop[ 'proxy'].DataLength])
        return 
            
    def cb_selectDevices( self): 
        w = selectMcaAndTimer.SelectMcaAndTimer( devices = self.devices, parent = self)
        w.show()

    def cb_helpMCA(self):
        QtGui.QMessageBox.about(self, self.tr("Help MCA"), self.tr(
                "<h3> Help MCA </h3>"
                "<ul>"
                "<li> n.n.</li>"
                "</ul>"
                ))

    def cb_writeFile( self):
        res = graPyspIfc.write()
        self.logWidget.append( "Created %s" % res)

    def _printHelper( self, frmt): 
        '''
        do the visible plot only
        '''
        prnt = os.getenv( "PRINTER")
        if prnt is None: 
            QtGui.QMessageBox.about(self, 'Info Box', "No shell environment variable PRINTER.") 
            return

        fName = graPyspIfc.createHardCopy( printer = prnt, format = frmt, flagPrint = False)
        self.logWidget.append( HasyUtils.getDateTime())
        self.logWidget.append("Created %s (%s)" % (fName, frmt))

        msg = "Send %s to %s" % ( fName, prnt)
        reply = QtGui.QMessageBox.question(self, 'YesNo', msg, 
                                           QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            if os.system( "/usr/bin/lpr -P %s %s" % (prnt, fName)):
                self.logWidget.append( "failed to print %s on %s" % (fName, prnt))
            self.logWidget.append(" printed on %s" % (prnt))
        
    def cb_hardcopy(self):
        self._printHelper( "DINA4")
        
    def cb_hardcopyA6(self):
        self._printHelper( "DINA6")

    #
    # the closeEvent is called when the window is closed by 
    # clicking the X at the right-upper corner of the frame
    #
    def closeEvent( self, e):
        self.cb_closeMCAWidget()
        #e.ignore()

    def cb_closeMCAWidget( self):

        if self.flagClosed:
            return
                    
        self.refreshTimer.stop()

        if self.pyspGui is not None:
            self.pyspGui.close()
        
        self.flagClosed = True
        self.close()

        #
        # do not close the application, if we have been called from pyspMonitor
        #
        if type( self.parent) is PySpectra.pyspMonitorClass.pyspMonitor: 
            return 
        #
        #  
        #
        graPyspIfc.close()
        #
        # we have to close the application, if we arrive here from 
        # TngGui.main() -> TngGuiClass.launchMoveMotor() -> moveMotor()
        #
        if self.app is not None: 
            self.app.quit()
        return

    def configureWidgetsBusy( self, flag):
        #self.w_slider.setEnabled( flag)
        return
    
    def cb_launchPyspGui( self): 
        '''
        launches the pyspGui to allow for actions like the Cursor widget
        '''
        self.pyspGui = PySpectra.pySpectraGuiClass.pySpectraGui()
        self.pyspGui.show()


