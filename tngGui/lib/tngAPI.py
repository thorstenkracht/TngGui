#!/usr/bin/env python

from taurus.external.qt import QtGui, QtCore 
import PyTango
import math, os
import definitions, utils, HasyUtils
import json
import tngGui.lib.helpBox as helpBox
        
class timerWidget( QtGui.QMainWindow):
    def __init__( self, logWidget, allTimers, parent = None):
        super( timerWidget, self).__init__( parent)
        self.parent = parent
        self.setWindowTitle( "Timers")
        self.logWidget = logWidget
        self.allTimers = allTimers
        w = QtGui.QWidget()
        self.layout_v = QtGui.QVBoxLayout()
        w.setLayout( self.layout_v)
        self.setCentralWidget( w)

        layout_grid = QtGui.QGridLayout()
        self.layout_v.addLayout( layout_grid)

        count = 0
        layout_grid.addWidget( QtGui.QLabel( 'Alias'), count, 0)
        layout_grid.addWidget( QtGui.QLabel( 'SampleTime'), count, 1)
        layout_grid.addWidget( QtGui.QLabel( 'StartStop'), count, 2)
        layout_grid.addWidget( QtGui.QLabel( 'Module'), count, 3)
        layout_grid.addWidget( QtGui.QLabel( 'DeviceName'), count, 4)

        for dev in self.allTimers: 
            count += 1
            dev[ 'w_aliasName2'] = QtGui.QLabel( dev[ 'name']) # '2' to avoid conflicts with the main table widgets
            layout_grid.addWidget( dev[ 'w_aliasName2'], count, 0)

            dev[ 'w_sampleTime2'] = utils.QPushButtonTK( "%g" % dev[ 'proxy'].sampleTime)
            dev[ 'w_sampleTime2'].setFixedWidth( definitions.POSITION_WIDTH)
            dev[ 'w_sampleTime2'].setToolTip( "Set sample time")
            dev[ 'w_sampleTime2'].mb1.connect( self.make_cb_setSampleTime( dev, self.logWidget))
            layout_grid.addWidget( dev[ 'w_sampleTime2'], count, 1)

            dev[ 'w_startStop2'] = utils.QPushButtonTK( 'Start')
            dev[ 'w_startStop2'].setToolTip( "MB-1: start timer")
            dev[ 'w_startStop2'].mb1.connect( self.make_cb_startStopTimer( dev, self.logWidget))
            layout_grid.addWidget( dev[ 'w_startStop2'], count, 2)

            layout_grid.addWidget( QtGui.QLabel( dev[ 'module']), count, 3)

            #
            # device name
            #
            devName = QtGui.QLabel()
            devName.setText( "%s/%s" % (dev['hostname'], dev['device']))
            devName.setAlignment( QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter)
            layout_grid.addWidget( devName, count, 4)
            
        #
        # Menu Bar
        #
        self.menuBar = QtGui.QMenuBar()
        self.setMenuBar( self.menuBar)
        self.fileMenu = self.menuBar.addMenu('&File')
        self.exitAction = QtGui.QAction('E&xit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect( self.cb_closeTimerWidget)
        self.fileMenu.addAction( self.exitAction)

        #
        # the activity menubar: help and activity
        #
        self.menuBarActivity = QtGui.QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarActivity, QtCore.Qt.TopRightCorner)

        self.helpMenu = self.menuBarActivity.addMenu('Help')
        self.helpWidget = self.helpMenu.addAction(self.tr("Properties"))
        self.helpWidget.triggered.connect( self.cb_helpWidget)

        self.activityIndex = 0
        self.activity = self.menuBarActivity.addMenu( "_")

        #
        # Status Bar
        #
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar( self.statusBar)

        self.exit = QtGui.QPushButton(self.tr("E&xit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        QtCore.QObject.connect( self.exit, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_closeTimerWidget)
        self.exit.setShortcut( "Alt+x")

        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect( self.cb_refreshTimerWidget)
        self.updateTimer.start( definitions.TIMEOUT_REFRESH)

    def make_cb_setSampleTime( self, dev, logWidget):
        def cb():
            try:
                sts = dev[ 'proxy'].state()
            except Exception as e:
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "make_cb_oreg: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return

            oldValue = dev[ 'proxy'].sampleTime
            value, ok = QtGui.QInputDialog.getText(self, "Enter a value", "New value for %s:" % dev[ 'name'],
                                                   QtGui.QLineEdit.Normal, "%g" % oldValue)
            if ok:
                dev[ 'proxy'].sampleTime = float(value)

        return cb

    def make_cb_startStopTimer( self, dev, logWidget):
        def cb():
            try:
                sts = dev[ 'proxy'].state()
            except Exception as e:
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "make_cb_oreg: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return

            if sts == PyTango.DevState.MOVING:
                dev[ 'proxy'].stop()
            else:
                dev[ 'proxy'].start()
        
        return cb

    def cb_helpWidget( self):
        w = helpBox.HelpBox( self, self.tr("Help Widget"), self.tr(
            "<h3>Properties</h3><p>"
            "Can only be changed with this widget. To create them use <b>jive</b>"
            "<ul>"
            "<li><b>Base</b> VME base address, see the hardware manual"
            "</ul>"
                ))
        w.show()

    def cb_closeTimerWidget( self): 
        self.updateTimer.stop()
        self.close()

    def cb_refreshTimerWidget( self):

        if self.isMinimized(): 
            return

        self.activityIndex += 1
        if self.activityIndex > (len( definitions.ACTIVITY_SYMBOLS) - 1):
            self.activityIndex = 0
        self.activity.setTitle( definitions.ACTIVITY_SYMBOLS[ self.activityIndex])
        
        for dev in self.allTimers:
            if dev[ 'proxy'].state() == PyTango.DevState.MOVING:
                dev[ 'w_aliasName2'].setStyleSheet( "background-color:%s;" % definitions.BLUE_MOVING)
                dev[ 'w_startStop2'].setText( "Stop")
            elif dev[ 'proxy'].state() == PyTango.DevState.ON:
                dev[ 'w_aliasName2'].setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
                dev[ 'w_startStop2'].setText( "Start")
            else:
                dev[ 'w_aliasName2'].setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
            dev[ 'w_sampleTime2'].setText( "%g" % dev[ 'proxy'].sampleTime)

    #
    # the closeEvent is called when the window is closed by 
    # clicking the X at the right-upper corner of the frame
    #
    def closeEvent( self, e):
        self.cb_closeMotorProp()
        #e.ignore()

    def cb_closeMotorProp( self):

        self.updateTimer.stop()
        self.close()

    def cb_applyDeviceProperties( self):
        count = 0
        #
        # check, whether there is some input at all
        #
        for prop in self.props:
            line = self.propDct[ prop][ "w_line"]
            if line is None:
                continue
            if len(line.text()) > 0:
                count += 1
                propFound = prop
        if count == 0:
            self.logWidget.append( "motorProp.cb_apply: no input")
            return 
        #
        # More than one input: clear the input lines
        #
        if count > 1:
            for prop in self.props:
                line = self.propDct[ prop][ "w_line"]
                if line is None:
                    continue
                line.clear()
            self.logWidget.append( "motorProp.cb_apply: more that one input")
            return

        prop = propFound
        line = self.propDct[ prop][ "w_line"]
            
        temp = line.text()
        HasyUtils.putDeviceProperty( self.dev[ 'device'], prop, temp, self.dev[ 'hostname'])
        line.clear()
