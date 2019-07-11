#!/usr/bin/env python

from taurus.external.qt import QtGui, QtCore 
import PyTango
import math, time, sys, os
import definitions, utils, HasyUtils, Spectra
import tngAPI, cursorGui
import IfcGraPysp

class SelectMotor( QtGui.QMainWindow):
    def __init__( self, parent = None):
        super( SelectMotor, self).__init__( parent)
        self.parent = parent
        self.setWindowTitle( "Select Motor")
        w = QtGui.QWidget()
        self.setCentralWidget( w)
        self.layoutGrid = QtGui.QGridLayout()
        w.setLayout( self.layoutGrid)
        i = 0
        j = 0
        for dev in allMotors:
            b = QtGui.QPushButton( dev[ 'name'])
            b.clicked.connect( self.make_cb_select( dev, parent))
            self.layoutGrid.addWidget( b, i, j)
            i += 1
            if i and (i % 17 == 0): 
                j += 1
                i = 0
        #
        # Status Bar
        #
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar( self.statusBar)

        self.exit = QtGui.QPushButton(self.tr("Exit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        self.exit.clicked.connect( self.close)
        self.exit.setShortcut( "Alt+x")

    #
    # create callback functions
    #
    def make_cb_select( self, dev, parent):
        def cb():
            self.parent.recycleMoveMotor( dev)
            self.close()
        return cb

class moveMotor( QtGui.QMainWindow):
    def __init__( self, dev, timerName, counterName, 
                  logWidget, allDevices, parent = None):
        super( moveMotor, self).__init__( parent)

        self.dev = dev
        self.allDevices = allDevices
        self.logWidget = logWidget
        self.scan = None

        self.setWindowTitle( "Move %s" % dev[ 'name'])
        self.move( 10, 750)

        #
        # prepare widgets
        #
        self.flagDisplaySignal = True
        self.prepareWidgets()
        self.timerName = timerName
        self.counterName = counterName
        self.timer = None
        self.counter = None
        self.flagClosed = False
        self.flagOffline = False
        #
        # we don't want to getSignal(), if a motor is moved from another
        # application, like spock
        #
        self.motorMoving = False
        self.cursorIsActive = False
        self.goingRight = True
        self.nameGQE = None
        self.lastX = -1.0e35
        self.sliderPosition = None

        self.updateCounts = 0

        self.motor = dev[ 'proxy']
        self.slewRateFactor = 1.
        #
        # store the original motor attributes
        #
        try:
            self.positionOld = utils.getPosition( self.dev)
        except Exception, e:
            self.logWidget.append( "%s, reading the position causes an error" % (self.dev[ 'name'])) 
            self.logWidget.append( "%s:" % repr( e))
            return
        #
        # Signal
        #
        self.sampleTime = 0.1
        self.signalMax = -1e35
        signalMaxX = None
        self.timerName = timerName
        if self.timerName is None:
            self.findTimer()
        self.counterName = counterName
        if self.counterName is None:
            self.findCounter()
        #
        # 
        #
        self.updateWidgets()
        self.signalChanged() # needs self.signalMaxString
        self.updateTimer.start( definitions.TIMEOUT_REFRESH_MOTOR)

        self.targetPosition.setText( "n.a.")
        self.setSliderScale()
        self.targetPosition.setText( "n.a.")
        self.w_slider.setFocus()
        self.configureIncrCB()
 
    def updateWidgets( self): 
        self.updateCounts += 1
        #
        # update the widgets
        #
        self.w_alias.setText( self.dev[ 'name'])
        self.w_motorPosition.setText( utils.getPositionString( self.dev))

        try:
            sts = self.dev[ 'proxy'].state()
        except Exception, e:
            self.w_motorPosition.setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
            self.flagOffline = True
            return 

        self.flagOffline = False
        
        if (self.updateCounts % 5)  == 0:
            if self.dev[ 'module'].lower() == "oms58":
                if self.dev[ 'proxy'].cwlimit == 1:
                    self.w_cw.setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
                else:
                    self.w_cw.setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
                if self.dev[ 'proxy'].ccwlimit == 1:
                    self.w_ccw.setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
                else:
                    self.w_ccw.setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
            
        if sts == PyTango.DevState.MOVING:
            self.w_motorPosition.setStyleSheet( "background-color:%s;" % definitions.BLUE_MOVING)
        elif sts == PyTango.DevState.DISABLE:
            self.w_motorPosition.setStyleSheet( "background-color:%s;" % definitions.MAGENTA_DISABLE)
        elif sts == PyTango.DevState.ON:
            self.w_motorPosition.setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
        else:
            self.w_motorPosition.setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
        
        self.w_stop.setToolTip( "Stop %s" % self.dev[ 'name'])

        self.w_motorLimitMin.setText( utils.getUnitLimitMinString( self.dev, self.logWidget))
        self.w_motorLimitMax.setText( utils.getUnitLimitMaxString( self.dev, self.logWidget))
        lst = HasyUtils.getDeviceProperty( self.dev['device'], "FlagEncoder", self.dev[ 'hostname'])
        if len(lst) > 0  and lst[0] == "1":
            self.w_encAttrButton.setEnabled( True)
            self.w_encoderPosition.setText( utils.getPositionEncoderString( self.dev))
        else:
            self.w_encAttrButton.setEnabled( False)
            self.w_encoderPosition.setText( 'n.a.')

        if self.dev[ 'module'].lower() == "oms58":
            self.w_controllerRegister.setText( "%d" % utils.getControllerRegister( self.dev))
        else:
            self.w_controllerRegister.setText( 'n.a.')

        if utils.hasSlewRate( self.dev, self.logWidget):
            self.slewRateComboBox.setEnabled( True)
        else:
            self.slewRateComboBox.setEnabled( False)

        if self.dev[ 'module'].lower() == 'oms58':
            self.w_toLeftStep.setEnabled( True)
            self.w_toRightStep.setEnabled( True)
        else:
            self.w_toLeftStep.setEnabled( False)
            self.w_toRightStep.setEnabled( False)

        if self.dev.has_key( 'zmxdevice'):
            self.w_zmxAttrButton.setEnabled( True)
        else:
            self.w_zmxAttrButton.setEnabled( False)

        self.w_signalLabel.setText( "(%s, %s, %g)" % ( self.timerName, self.counterName, self.sampleTime))

    def prepareWidgets( self):
        w = QtGui.QWidget()
        self.layout_v = QtGui.QVBoxLayout()
        w.setLayout( self.layout_v)
        self.setCentralWidget( w)
        #
        # the alias line
        #
        hBox = QtGui.QHBoxLayout()
        self.w_alias = QtGui.QPushButton()
        self.w_alias.clicked.connect( self.cb_selectMotor)
        hBox.addWidget( self.w_alias)
        hBox.addStretch()            
        self.w_cw = QtGui.QLabel("cw")
        self.w_ccw = QtGui.QLabel( "ccw")
        hBox.addWidget( self.w_cw)
        hBox.addWidget( self.w_ccw)
        self.layout_v.addLayout( hBox)
        #
        # position, moveTo
        #
        hBox = QtGui.QHBoxLayout()
        hBox.addWidget( QtGui.QLabel( "Position"))
        self.w_motorPosition = QtGui.QLabel()
        self.w_motorPosition.setFixedWidth( definitions.POSITION_WIDTH)
        self.w_motorPosition.setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
        hBox.addWidget( self.w_motorPosition)
        hBox.addStretch()            
        hBox.addWidget( QtGui.QLabel( "Target"))
        self.targetPosition = QtGui.QLabel()
        self.targetPosition.setFixedWidth( definitions.POSITION_WIDTH)
        self.targetPosition.setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
        hBox.addWidget( self.targetPosition)
        hBox.addStretch()            
        self.moveButton = QtGui.QPushButton(self.tr("&Move")) 
        self.moveButton.setShortcut( "Alt+m")
        self.moveButton.setToolTip( "Start move with backlash")
        hBox.addWidget( self.moveButton)
        self.moveButton.clicked.connect( self.moveTo)
        self.moveToLine = QtGui.QLineEdit()
        self.moveToLine.setFixedWidth( definitions.POSITION_WIDTH)
        self.moveToLine.setAlignment( QtCore.Qt.AlignRight)
        hBox.addWidget( self.moveToLine)
        self.layout_v.addLayout( hBox)
        #
        # encoder position
        #
        hBox = QtGui.QHBoxLayout()
        hBox.addWidget( QtGui.QLabel( "Encoder"))
        self.w_encoderPosition = QtGui.QLabel()
        self.w_encoderPosition.setFixedWidth( definitions.POSITION_WIDTH)
        self.w_encoderPosition.setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
        hBox.addWidget( self.w_encoderPosition)
        hBox.addStretch()
        hBox.addWidget( QtGui.QLabel( "Controller"))
        self.w_controllerRegister = QtGui.QLabel()
        self.w_controllerRegister.setFixedWidth( definitions.POSITION_WIDTH)
        self.w_controllerRegister.setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
        hBox.addWidget( self.w_controllerRegister)
        self.layout_v.addLayout( hBox)
        #
        # the slider
        #
        frame = QtGui.QFrame()
        frame.setFrameShape( QtGui.QFrame.Box)
        self.layout_v.addWidget( frame)
        self.layout_frame_v = QtGui.QVBoxLayout()
        frame.setLayout( self.layout_frame_v)
        self.w_slider = QtGui.QSlider()
        #
        # install an event filter for the slider, basically to catch 
        # arrow-up and arrow-down events. Up/Down are not caught, if
        # the filter is applied to self.
        #
        self.w_slider.installEventFilter( self)
        self.w_slider.setOrientation( 1) # 1 horizontal, 2 vertical
        self.w_slider.setToolTip( "Moving the slider moves the motor, upon mouse-release. \nIf the slider has the focus (is highlighted)\n Key_Right/Key_Left are active.\nKey_Up/Down change the slew rate.\n spaceBar stops the move.\nUse Alt-o to set the focus to the slider.")
        self.layout_frame_v.addWidget( self.w_slider)
        self.w_slider.sliderReleased.connect( self.cb_sliderReleased)
        self.w_slider.valueChanged.connect( self.cb_sliderValueChanged)
        #
        # the slider: min, sliderPosition, max
        #
        hBox = QtGui.QHBoxLayout()
        self.w_motorLimitMin = QtGui.QLabel()
        self.w_motorLimitMin.setMinimumWidth( definitions.POSITION_WIDTH)
        self.w_motorLimitMin.setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
        hBox.addWidget( self.w_motorLimitMin)
        hBox.addStretch()
        self.w_sliderPosition = QtGui.QLabel()
        hBox.addWidget( self.w_sliderPosition)
        hBox.addStretch()
        self.w_motorLimitMax = QtGui.QLabel()
        self.w_motorLimitMax.setMinimumWidth( definitions.POSITION_WIDTH)
        self.w_motorLimitMax.setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
        hBox.addWidget( self.w_motorLimitMax)
        self.layout_frame_v.addLayout( hBox)

        #
        # Increment, Slew
        #
        hBox = QtGui.QHBoxLayout()
        self.incrComboBox = QtGui.QComboBox()
        self.incrComboBox.currentIndexChanged.connect( self.cb_incrChanged)
        hBox.addStretch()            
        hBox.addWidget( QtGui.QLabel( "Increment:"))
        hBox.addWidget( self.incrComboBox)

        self.slewRateComboBox = QtGui.QComboBox()
        self.slewRateComboBox.addItem( "100%")
        self.slewRateComboBox.addItem( "50%")
        self.slewRateComboBox.addItem( "25%")
        self.slewRateComboBox.addItem( "10%")
        self.slewRateComboBox.addItem( "5%")
        self.slewRateComboBox.addItem( "2.5%")
        self.slewRateComboBox.addItem( "1%")
        self.slewRateComboBox.addItem( "0.5%")
        self.slewRateComboBox.addItem( "0.25%")
        self.slewRateComboBox.addItem( "0.1%")
        hBox.addWidget( QtGui.QLabel( "Slew:"))
        self.slewRateComboBox.currentIndexChanged.connect( self.cb_slewChanged)
        self.slewRateComboBox.setToolTip( "Can also be changed by Key_Up/Down\nwhen the slider is in focus.")
        hBox.addWidget( self.slewRateComboBox)
        hBox.addStretch()            
        self.layout_v.addLayout( hBox)
        #
        # |<, <<, Stop, >>, >|
        #
        frame = QtGui.QFrame()
        frame.setFrameShape( QtGui.QFrame.Box)
        self.layout_v.addWidget( frame)
        hBox = QtGui.QHBoxLayout()
        frame.setLayout( hBox)
        hBox.addStretch()            
        # |< 
        self.w_toLeftLimit = QtGui.QPushButton(self.tr("|<")) 
        self.w_toLeftLimit.setFixedWidth( 50)
        self.w_toLeftLimit.setToolTip( "Move to lower limit")
        self.w_toLeftLimit.clicked.connect( self.cb_toLeftLimit)
        hBox.addWidget( self.w_toLeftLimit)
        # <<
        self.w_toLeftIncr = QtGui.QPushButton(self.tr("<<")) 
        self.w_toLeftIncr.setToolTip( "Move left by increment, no backlash")
        self.w_toLeftIncr.setFixedWidth( 50)
        self.w_toLeftIncr.clicked.connect( self.cb_toLeftIncr)
        hBox.addWidget( self.w_toLeftIncr)
        # <
        self.w_toLeftStep = QtGui.QPushButton(self.tr("<")) 
        self.w_toLeftStep.setFixedWidth( 50)
        self.w_toLeftStep.setToolTip( "Move left by one step, no backlash")
        self.w_toLeftStep.clicked.connect( self.cb_toLeftStep)
        hBox.addWidget( self.w_toLeftStep)
        # stop
        self.w_stop = QtGui.QPushButton(self.tr("&Stop")) 
        self.w_stop.setFixedWidth( 70)
        self.w_stop.clicked.connect( self.cb_stop)
        self.w_stop.setShortcut( "Alt+s")
        hBox.addWidget( self.w_stop)
        # >
        self.w_toRightStep = QtGui.QPushButton(self.tr(">")) 
        self.w_toRightStep.setFixedWidth( 50)
        self.w_toRightStep.setToolTip( "Move right by one step, no backlash")
        self.w_toRightStep.clicked.connect( self.cb_toRightStep)
        hBox.addWidget( self.w_toRightStep)
        # >>
        self.w_toRightIncr = QtGui.QPushButton(self.tr(">>")) 
        self.w_toRightIncr.setFixedWidth( 50)
        self.w_toRightIncr.setToolTip( "Move right by increment, no backlash")
        self.w_toRightIncr.clicked.connect( self.cb_toRightIncr)
        hBox.addWidget( self.w_toRightIncr)
        # >|
        self.w_toRightLimit = QtGui.QPushButton(self.tr(">|")) 
        self.w_toRightLimit.setFixedWidth( 50)
        self.w_toRightLimit.setToolTip( "Move to upper limit")
        self.w_toRightLimit.clicked.connect( self.cb_toRightLimit)
        hBox.addWidget( self.w_toRightLimit)
        hBox.addStretch()            
        #self.layout_v.addLayout( hBox)
        #
        # Frame: 
        #   signal max at ... move to max
        #
        frame = QtGui.QFrame()
        frame.setFrameShape( QtGui.QFrame.Box)
        self.layout_v.addWidget( frame)
        self.layout_frame_v = QtGui.QVBoxLayout()
        frame.setLayout( self.layout_frame_v)
        hBox = QtGui.QHBoxLayout()
        self.layout_frame_v.addLayout( hBox)
        self.w_signalMaxString = QtGui.QLabel( "Signal Max.:")
        hBox.addWidget( self.w_signalMaxString)
        self.w_signalMaxLabel = QtGui.QLabel()
        self.w_signalMaxLabel.setFixedWidth( definitions.POSITION_WIDTH)
        hBox.addWidget( self.w_signalMaxLabel)
        hBox.addWidget( QtGui.QLabel( "at"))
        self.w_signalMaxXLabel = QtGui.QLabel()
        self.w_signalMaxXLabel.setFixedWidth( definitions.POSITION_WIDTH)
        hBox.addWidget( self.w_signalMaxXLabel)
        hBox.addStretch()
        #self.layout_v.addLayout( hBox)
        self.layout_v.addStretch()        
        self.toMax = QtGui.QPushButton(self.tr("Move to max.")) 
        self.toMax.clicked.connect( self.cb_toMax)
        hBox.addWidget( self.toMax)
        #
        # enable/disable signal, change signal
        #
        hBox = QtGui.QHBoxLayout()
        self.layout_frame_v.addLayout( hBox)

        self.w_signalCheckBox = QtGui.QCheckBox()
        self.w_signalCheckBox.setChecked( self.flagDisplaySignal)
        self.w_signalCheckBox.setToolTip( "Enable/disable signal display.")
        hBox.addWidget( self.w_signalCheckBox) 
        self.w_signalCheckBox.stateChanged.connect( self.cb_flagDisplaySignalChanged)

        self.w_signalLabel = QtGui.QLabel("")
        hBox.addWidget( self.w_signalLabel) 
        
        self.w_signalButton = QtGui.QPushButton(self.tr("Change Signal")) 
        self.w_signalButton.setToolTip( "Change signal")
        hBox.addWidget( self.w_signalButton) 
        self.w_signalButton.clicked.connect( self.cb_defineSignal)
        hBox.addStretch()

       
        #
        # the update timer, don't want to poll all devices at high speed
        #
        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect( self.cb_refreshMoveMotor)

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

        self.w_attrButton = QtGui.QPushButton(self.tr("&Attr")) 
        self.w_attrButton.setToolTip( "Change OmsVme58 attributes")
        self.statusBar.addPermanentWidget( self.w_attrButton) # 'permanent' to shift it right
        self.w_attrButton.clicked.connect( self.cb_launchAttr)
        self.w_attrButton.setShortcut( "Alt+a")

        self.w_commandButton = QtGui.QPushButton(self.tr("Cmd")) 
        self.w_commandButton.setToolTip( "Execute OmsVme58 commands")
        self.statusBar.addPermanentWidget( self.w_commandButton) # 'permanent' to shift it right
        self.w_commandButton.clicked.connect( self.cb_launchCommand)

        self.w_propButton = QtGui.QPushButton(self.tr("&Prop")) 
        self.w_propButton.setToolTip( "Change Properties")
        self.statusBar.addPermanentWidget( self.w_propButton) # 'permanent' to shift it right
        self.w_propButton.clicked.connect( self.cb_launchProp) #
        self.w_propButton.setShortcut( "Alt+p")

        self.w_encAttrButton = QtGui.QPushButton(self.tr("&EncAttr")) 
        self.w_encAttrButton.setToolTip( "Change motor encoder attributes")
        self.statusBar.addPermanentWidget( self.w_encAttrButton) # 'permanent' to shift it right
        self.w_encAttrButton.clicked.connect( self.cb_launchEncAttr)
        self.w_encAttrButton.setShortcut( "Alt+e")

        self.w_zmxAttrButton = QtGui.QPushButton(self.tr("ZMXAttr")) 
        self.w_zmxAttrButton.setToolTip( "Change ZMX attributes, uses <zmxdevice> tag in online.xml, e.g.: \n\
<device> \n\
 <name>exp_mot65</name> \n\
 <type>stepping_motor</type> \n\
 <zmxdevice>haspp99:10000/p99/zmx/exp.01</zmxdevice> \n\
 <module>oms58</module> \n\
 <device>p99/motor/exp.65</device> \n\
 <control>tango</control> \n\
 <hostname>haspp99:10000</hostname> \n\
</device> \n\
")
        self.statusBar.addPermanentWidget( self.w_zmxAttrButton) # 'permanent' to shift it right
        self.w_zmxAttrButton.clicked.connect( self.cb_launchZmxAttr)

        self.cursor = QtGui.QPushButton(self.tr("&Cursor")) 
        self.cursor.setToolTip( "Launch cursor widget")
        self.statusBar.addPermanentWidget( self.cursor) # 'permanent' to shift it right
        self.cursor.clicked.connect( self.cb_launchCursor)
        self.cursor.setShortcut( "Alt+c")
        #
        # create the log widget, if necessary
        #
        if self.logWidget is None:
             self.logWidget = QtGui.QTextEdit()
             self.logWidget.setMaximumHeight( 150)
             self.logWidget.setReadOnly( 1)
             self.layout_v.addWidget( self.logWidget)
             self.w_clear = QtGui.QPushButton(self.tr("Clear")) 
             self.w_clear.setToolTip( "Clear log widget")
             self.statusBar.addPermanentWidget( self.w_clear) # 'permanent' to shift it right
             self.w_clear.clicked.connect( self.logWidget.clear)

        self.exit = QtGui.QPushButton(self.tr("&Exit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        self.exit.clicked.connect( self.cb_closeMoveMotor)
        self.exit.setShortcut( "Alt+x")

    def prepareMenuBar( self):

        self.fileMenu = self.menuBar.addMenu('&File')

        #self.spectraAction = QtGui.QAction('&Spectra', self)        
        #self.spectraAction.setStatusTip('Spectra')
        #self.spectraAction.triggered.connect( self.cb_launchSpectra)
        #self.spectraAction.setShortcut( "Alt+s")
        #self.fileMenu.addAction( self.spectraAction)

        self.writeFileAction = QtGui.QAction('Write .fio file', self)        
        self.writeFileAction.triggered.connect( self.cb_writeFile)
        self.fileMenu.addAction( self.writeFileAction)

        self.postscriptAction = QtGui.QAction('Postscript', self)        
        self.postscriptAction.setStatusTip('Create postscript output')
        self.postscriptAction.triggered.connect( self.cb_postscript)
        self.fileMenu.addAction( self.postscriptAction)

        self.postscriptActionA6 = QtGui.QAction('Postscript A6', self)        
        self.postscriptActionA6.setStatusTip('Create postscript output, A6')
        self.postscriptActionA6.triggered.connect( self.cb_postscriptA6)
        self.fileMenu.addAction( self.postscriptActionA6)


        self.clipboardAction = self.fileMenu.addAction(self.tr("SpectraGraphic to Clipboard"))
        self.connect(self.clipboardAction, QtCore.SIGNAL("triggered()"), self.cb_clipboard)

        self.exitAction = QtGui.QAction('E&xit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(QtGui.QApplication.quit)
        self.fileMenu.addAction( self.exitAction                  )

        self.miscMenu = self.menuBar.addMenu('Misc')

        self.focusSliderAction = QtGui.QAction('F&ocus Slider', self)       
        self.focusSliderAction.triggered.connect( self.w_slider.setFocus)
        self.miscMenu.addAction( self.focusSliderAction)
        self.focusSliderAction.setShortcut( "Alt+o")

        self.restartTimerAction = QtGui.QAction('Restart Timer', self)        
        self.restartTimerAction.setStatusTip('Restart update timer')
        self.restartTimerAction.triggered.connect( self.cb_restartTimer)
        self.miscMenu.addAction( self.restartTimerAction)

        self.stopTimerAction = QtGui.QAction('Stop Timer', self)        
        self.stopTimerAction.setStatusTip('Stop update timer')
        self.stopTimerAction.triggered.connect( self.cb_stopTimer)
        self.miscMenu.addAction( self.stopTimerAction)

        #
        # the activity menubar: help and activity
        #
        self.menuBarActivity = QtGui.QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarActivity, QtCore.Qt.TopRightCorner)

        self.helpMenu = self.menuBarActivity.addMenu('Help')
        self.helpMove = self.helpMenu.addAction(self.tr("Move"))
        self.helpMove.triggered.connect( self.cb_helpMove)
        self.helpUpdateRate = self.helpMenu.addAction(self.tr("Update rate"))
        self.helpUpdateRate.triggered.connect( self.cb_helpUpdateRate)
        self.helpColorCode = self.helpMenu.addAction(self.tr("Color code"))
        self.helpColorCode.triggered.connect( self.cb_colorCode)

        self.activityIndex = 0
        self.activity = self.menuBarActivity.addMenu( "_")

    def cb_launchSpectra( self):
        '''
        make sure that main() is started as a foreground process
        '''
        if os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno()):
            Spectra.gra_input()
        else:
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "cb_launchSpectra: no TTY connected.\nMain runs as  a background process",
                                       QtGui.QMessageBox.Ok)
            
    def cb_restartTimer( self):
        self.updateTimer.stop()
        self.updateTimer.start( definitions.TIMEOUT_REFRESH_MOTOR)
        
    def cb_stopTimer( self):
        self.updateTimer.stop()

    def recycleMoveMotor( self, dev): 
        '''
        called from SelectMotor()
        '''
        self.dev = dev
        self.motor = dev[ 'proxy']
        self.setWindowTitle( "Move %s" % dev[ 'name'])
        self.flagDisplaySignal = True
        self.cursorIsActive = False
        self.goingRight = True
        self.nameGQE = None
        self.lastX = -1.0e35
        self.sliderPosition = None
        self.updateWidgets()
        if self.scan is not None:
            self.deleteScan()
        if self.cursorIsActive:
            self.cursorGUI.close()
        self.signalChanged() # needs self.signalMaxString
        self.w_slider.setFocus()
        self.setSliderScale()
        
        
    def cb_selectMotor( self): 
        w = SelectMotor( self)
        w.show()

    def cb_helpMove( self):
        w = helpBox.HelpBox( self, title = self.tr("Help Move"), text = self.tr(
            "\
<p><b>To move a motor</b><br>\
- Specify the target in the entry widget, then press Move (or Alt-m) <br>\
- Use the |&lt;, &lt;&lt;, &gt;&gt;, &gt;| buttons <br>\
- Move the slider with the mouse (mouse-release event) <br>\
- Set the focus to the slider (Alt-o) then press Key_Left and Key_Right <br>\
<br>\
Btw: Key_Up/Down change the slew rate. <br>" 
                ))
        w.show()

    def cb_helpUpdateRate( self):
        w = helpBox.HelpBox( self, title = self.tr("Help Update Rate"), text = self.tr(
            "<h3>Update Rate</h3>"
            "<p>"
            "The move widget is updated every %d msecs. During the execution "
            "of the update function the timer is stopped." % definitions.TIMEOUT_REFRESH
                ))
        w.show()

    def cb_colorCode( self):
        w = helpBox.HelpBox( self, title = self.tr("Help Update Rate"), text = self.tr(
            "<h3>Color Code</h3>"
            "<ul>"
            "<li> blue    MOVING"
            "<li> green   OK"
            "<li> magenta DISABLE"
            "<li> red     ALARM"
            "</ul>"
                ))
        w.show()

    def cb_flagDisplaySignalChanged( self):
        self.flagDisplaySignal = self.w_signalCheckBox.isChecked()
        if not self.flagDisplaySignal:
            if self.scan is None:
                self.deleteScan()
            self.signalMax = -1e35
            signalMaxX = None

    def findTimer( self):
        '''
        make a guess: take the first timer 
        the user should see the name, e.g. d1_t01, only. 
        the device, e.g. p09/dgg2/d1.01, is for the proxy only
        '''
        for dev in self.allDevices:
            if dev['type'] == 'timer':
                self.timerName = dev['name']
                break
        else:
            self.logWidget.append( "findTimer: no timer found")

    def findCounter( self):
        '''
        make a guess: take the counter
        the user should see the name, e.g. d1_c01, only. 
        the device, e.g. p09/counter/d1.01, is for the proxy only
        '''
        for dev in self.allDevices:
            if dev['type'] == 'counter' and dev['module'].lower() == 'sis3820':
                self.counterName = dev['name']
                break        
        else:
            self.logWidget.append( "findCounter: no counter found")
        
    def signalChanged( self):
        '''
        called also from defineSignal.DefineSignal
        '''
        #print "signalChanged, timer", self.timerName, "counter", self.counterName
        #
        # d1_t01 -> p09/dgg2/d1.01
        # d1_c01 -> p09/counter/d1.01
        #
        timerDevice = None
        counterDevice = None
        if self.timerName == 'None':
            timerDevice = None
            self.timerDev = None
        else:
            for dev in self.allDevices:
                if dev['name'] == self.timerName:
                    self.timerDev = dev
                    timerDevice = "%s/%s" % (dev[ 'hostname'], dev['device']) 
                    break

        for dev in self.allDevices:
            if dev['name'] == self.counterName:
                self.counterDev = dev
                #
                # It is better to use the alias (dev['name']) for counterDevice to 
                # handle this attribute synstax:
                #   <device>
                #   <name>petraCurrent</name>
                #   <type>counter</type>
                #   <module>tangoattributectctrl</module>
                #   <device>petra/globals/keyword/BeamCurrent</device>
                #   <control>tango</control>
                #   <hostname>haso107d1:10000</hostname>
                #   </device>
                #
                if dev['module'].lower() == 'tangoattributectctrl':
                    lst = dev[ 'device'].split( "/")
                    #
                    #   <device>petra/globals/keyword/BeamCurrent</device>
                    #
                    if len( lst) == 4:
                        counterDevice = "%s/%s" % (dev[ 'hostname'], "/".join( lst[:3]))
                        self.counterAttributeName = lst[3]
                    #
                    #   <name>petra_BeamCurrent</name>
                    #
                    else:
                        lst = dev[ 'name'].split( "_")
                        if len(lst) == 2:
                            self.counterAttributeName = lst[1]
                            counterDevice = "%s/%s" % (dev[ 'hostname'], dev['device'])
                        else:
                            QtGui.QMessageBox.critical(self, 'Error', 
                                                       "signalChanges: cannot parse %s" % self.dev[ 'name'], 
                                       QtGui.QMessageBox.Ok)
                            self.counter == None
                            return
                else:
                    counterDevice = "%s/%s" % (dev[ 'hostname'], dev['device'])
                    if dev[ 'module'].lower() == 'sis3820':
                        self.counterAttributeName = 'Counts'
                    elif dev[ 'module'].lower() == 'vfcadc':
                        self.counterAttributeName = 'Counts'
                    elif dev[ 'module'].lower() == 'sis3610':
                        self.counterAttributeName = 'Value'
                    else:
                            QtGui.QMessageBox.critical(self, 'Error', 
                                                       "signalChanges: failed to identify %s" % self.dev[ 'name'], 
                                       QtGui.QMessageBox.Ok)
                            self.counter == None
                            return
                break
        if counterDevice is None:
            self.logWidget.append( "signalChanged: no counter device")
            return
        
        if timerDevice is None:
            self.logWidget.append( "signalChanged: no timer device")
            self.timer = None
        else:
            try:
                self.timer = PyTango.DeviceProxy( timerDevice)
            except Exception, e:
                self.logWidget.append( "signalChanged: no proxy to %s" % timerDevice)
                exceptionToLog( e, self.logWidget)
                self.timer = None
                return

        try:
            self.counter = PyTango.DeviceProxy( counterDevice)
        except Exception, e:
            self.logWidget.append( "signalChanged: no proxy to %s" % counterDevice)
            utils.ExceptionToLog( e, self.logWidget)
            self.counter = None
            return

        if self.scan is not None:
            self.deleteScan()

    def cb_writeFile( self):
        #Spectra.gra_command( "write/fio %s" % self.nameGQE)
        IfcGraPysp.writeFile( self.nameGQE)
        self.logWidget.append( "write/nocon/fio %s" % self.nameGQE)

    def cb_postscript(self):
        '''
        do the visible plot only
        '''
        prnt = os.getenv( "PRINTER")
        if prnt is None: 
            QtGui.QMessageBox.about(self, 'Info Box', "No shell environment variable PRINTER.") 
            return

        IfcGraPysp.createHardCopy( prnt)
        #Spectra.gra_command(" postscript/redisplay/nolog/nocon/print/lp=%s" % prnt)
        self.logWidget.append( HasyUtils.getDateTime())
        self.logWidget.append(" Sent postscript file to %s, selected dataset" % prnt)

    def cb_postscriptA6(self):
        '''
        do the visible plot only
        '''
        prnt = os.getenv( "PRINTER")
        if prnt is None: 
            QtGui.QMessageBox.about(self, 'Info Box', "No shell environment variable PRINTER.") 
            return

        Spectra.gra_command(" set 0.1/border=1")
        Spectra.gra_command(" postscript/dina6/redisplay/nolog/nocon/print/lp=%s" % prnt)
        Spectra.gra_command(" set 0.1/border=0")
        self.logWidget.append( HasyUtils.getDateTime())
        self.logWidget.append(" Sent postscript file to %s, selected dataset" % prnt)
    
    def cb_clipboard( self):
        import gtk

        if not os.access( "/usr/bin/shutter", os.X_OK):
            self.logWidget.append( "clipboard: /usr/bin/shutter does not exist")
            return False
        
        if os.system( "/usr/bin/shutter -w=SpectraGraphic -e -o /tmp/spectraGraphic.png > /dev/null 2>&1"):
            self.logWidget.append( "clipboard: shutter command failed")
            return False

        image = gtk.gdk.pixbuf_new_from_file( "/tmp/spectraGraphic.png")
        clipboard = gtk.clipboard_get()
        clipboard.set_image(image)
        clipboard.store()
        self.logWidget.append("SpectraGraphic copied to clipboard")

    def cb_defineSignal( self):
        w = defineSignal.DefineSignal( self, self.allDevices)
        w.show()

    def cb_sliderReleased( self):
        value = self.w_slider.value()

        if self.motor.state() == PyTango.DevState.MOVING:
            utils.execStopMove( self.dev)
            while self.motor.state() == PyTango.DevState.MOVING:
                time.sleep(0.01)

        posReq = (utils.getUnitLimitMax( self.dev, self.logWidget) - utils.getUnitLimitMin( self.dev, self.logWidget))*value/\
                 float(definitions.SLIDER_RESOLUTION) + utils.getUnitLimitMin( self.dev, self.logWidget)
        self.moveTarget( posReq)

    def eventFilter(self, obj, event):
        
        #
        # Only watch for specific slider keys.
        # Everything else is pass-thru
        #
        if obj is self.w_slider and event.type() == event.KeyPress:
            key = event.key()
            if key == QtCore.Qt.Key_Up:
                self.cb_slewDown()
                return True
            elif key == QtCore.Qt.Key_Down:
                self.cb_slewUp()
                return True
            elif key == QtCore.Qt.Key_Right:
                self.cb_toRightIncr()
                return True
            elif key == QtCore.Qt.Key_Left:
                self.cb_toLeftIncr()
                return True
            elif key == 32:
                utils.execStopMove( self.dev)
                return True
            return False
        return False

    def cb_sliderValueChanged( self, value):
        #
        # set the slider position label on valueChanged
        #
        posSlider = (utils.getUnitLimitMax( self.dev, self.logWidget) - utils.getUnitLimitMin( self.dev, self.logWidget))*value/\
                    float(definitions.SLIDER_RESOLUTION) + utils.getUnitLimitMin( self.dev, self.logWidget)
        if self.w_sliderPosition:
            self.w_sliderPosition.setText( "%g" % posSlider)

    def setSliderScale( self):
        self.w_slider.setMinimum( 0)
        self.w_slider.setMaximum( int(definitions.SLIDER_RESOLUTION))
        try:
            value = int( float(definitions.SLIDER_RESOLUTION)*(utils.getPosition( self.dev) - utils.getUnitLimitMin( self.dev, self.logWidget))/
                         (utils.getUnitLimitMax( self.dev, self.logWidget) - utils.getUnitLimitMin( self.dev, self.logWidget)))
            self.w_slider.setValue( value)
        except: 
            self.logWidget.append( "setSliderScale: Failed to set slider scale")


    #
    # the closeEvent is called when the window is closed by 
    # clicking the X at the right-upper corner of the frame
    #
    def closeEvent( self, e):
        self.cb_closeMoveMotor()
        #e.ignore()

    def cb_closeMoveMotor( self):
        #
        # we don't want to call restoreOriginalAttributes several times
        #
        if self.flagClosed:
            return
        
        try: 
            if self.motor.state() == PyTango.DevState.MOVING:
                utils.execStopMove( self.dev)
                while self.motor.state() == PyTango.DevState.MOVING:
                    time.sleep(0.01)
        except Exception, e:
            self.logWidget.append( "cb_closeMoveMotor: caught exception for %s" % (self.dev[ 'fullName']))
            utils.ExceptionToLog( e, self.logWidget)
            
                    
        if self.scan is not None:
            self.deleteScan()

        self.updateTimer.stop()
        
        self.flagClosed = True
        self.close()

    def cb_refreshMoveMotor( self):
        '''
        - update the motor position
        - update the signal plot
        '''

        x = utils.getPosition( self.dev) 

        self.activityIndex += 1
        if self.activityIndex > (len( definitions.ACTIVITY_SYMBOLS) - 1):
            self.activityIndex = 0
        self.activity.setTitle( definitions.ACTIVITY_SYMBOLS[ self.activityIndex])
        
        self.w_motorPosition.setText( "%g" % x)

        self.updateWidgets()

        if not self.flagDisplaySignal:
            return

        if self.cursorIsActive:
            return
        #
        # if the position did not change, don't do anything
        #
        if self.lastX == x:
            return 
        if math.fabs( (self.lastX - x) / (self.lastX + x)) < 0.00001:
            return 

        self.updateTimer.stop()

        #
        # set the slider scale here. Otherwise we might
        # interfere with the user dragging the slider
        # 
        # always call setSliderScale() because e.g. DACs never 
        # become MOVING
        #
        if self.motorMoving or True:
            self.setSliderScale()

        y = self.getSignal()
        if y is None:
            self.updateTimer.start( definitions.TIMEOUT_REFRESH_MOTOR)
            return

        if self.scan is None:
            try:
                self.createScan()
            except Exception, e:
                self.logWidget.append( "cb_refresh, exception from createScan")
                self.logWidget.append( repr( e))
                print "moveMotor.refreshMoveMotor: caught exception\n", repr( e)
                sys.exit(255)
            #print "cb_refresh: created", self.scan.name
            self.curr_index = 0
        #
        # the second point determines the direction
        #
        if self.curr_index == 1:
            if x > self.scan.getX( 0):
                self.goingRight = True
            else:
                self.goingRight = False
        #
        # direction changed? if so, create a new scan
        #
        if self.curr_index > 1:
            #print "goingRight", self.goingRight, "curr_index", self.curr_index, "x", x, "lastX ", self.lastX
            if self.goingRight and x < self.lastX or not self.goingRight and x > self.lastX:   
                #print "cb_refresh: direction changed, creating new scan"
                self.deleteScan()
                self.createScan()
                self.curr_index = 0
                self.signalMax = y

        #print "cb_refresh: storing index %x, x %g, y %g " % (self.curr_index, x, y)
        self.scan.setX( self.curr_index, x)
        self.scan.setY( self.curr_index, y)
        self.scan.setCurrent( self.curr_index)

        self.curr_index += 1
        if not self.goingRight:
            self.scan.sort()
        self.scan.autoscale()
        self.scan.display()
        self.lastX = x

        self.updateTimer.start( definitions.TIMEOUT_REFRESH_MOTOR)

        return 

    def deleteScan( self): 
        '''
        use the IfcGraPysp module to abstract Spectra/PySpectra
        '''
        IfcGraPysp.deleteScan( self.scan)
        #+++del self.scan
        self.scan = None
        return 

    def createScan( self):

        self.nameGQE = HasyUtils.createScanName( "scanplot")

        if self.scan is not None:
            self.deleteScan()

        if self.cursorIsActive:
            self.cursorGUI.close()

        try:
            self.scan = IfcGraPysp.Scan( name = self.nameGQE,
                                       start = utils.getUnitLimitMin( self.dev, self.logWidget),
                                       stop = utils.getUnitLimitMax( self.dev, self.logWidget), 
                                       np = 1000, 
                                       ylabel = self.counterName,
                                       xlabel = "%s/%s" % (self.dev[ 'hostname'],self.dev[ 'device']), 
                                       comment = "Timer: %s, SampleTime: %g" % (self.timerName, 
                                                                                self.sampleTime),
                                       NoDelete = False, 
                                       colour = 2,
                                       at = "(1,1,1)")
        except Exception, e:
            print "moveMotor.createScan caught an exception"
            print repr( e)
            self.logWidget.append( "createScan: caught error")
            utils.ExceptionToLog( e, self.logWidget)
            return 

        self.scan.setCurrent( 0)

        return 

    def configureIncrCB( self):
        '''
        called from the constructor, configures the combobox for the increment
        '''
        res = (utils.getUnitLimitMax( self.dev, self.logWidget) - utils.getUnitLimitMin( self.dev, self.logWidget))/1000.
        if res == 0.:
            res = 0.1
        else:
            res = math.pow( 10, math.floor( math.log10(res) + 0.5))
        lst = range( 5)
        lst.reverse()
        
        self.incrComboBox.clear()
        for i in lst:
            temp = "%g" % (res*math.pow( 10, i - 2.))
            self.incrComboBox.addItem( temp)
        self.incr =  (res*math.pow( 10, lst[0] - 2.))
        self.incrComboBox.setCurrentIndex( 1)

    def cb_incrChanged( self):
        #
        # cb_incrChanged is invoked, also when the widget is newly configured
        #
        temp = self.incrComboBox.currentText()
        if len(temp) == 0:
            return
        self.incr = float( self.incrComboBox.currentText())

    def cb_slewUp( self):
        if not utils.hasSlewRate( self.dev, self.logWidget): 
            return
        index = self.slewRateComboBox.currentIndex()
        index += 1
        if index < self.slewRateComboBox.count():
            self.slewRateComboBox.setCurrentIndex( index)
    def cb_slewDown( self):
        if not utils.hasSlewRate( self.dev, self.logWidget): 
            return
        index = self.slewRateComboBox.currentIndex()
        index -= 1
        if index >= 0:
            self.slewRateComboBox.setCurrentIndex( index)

    def cb_slewChanged( self):
        if self.motor.state() == PyTango.DevState.MOVING:
            utils.execStopMove( self.dev)
            while self.motor.state() == PyTango.DevState.MOVING:
                time.sleep(0.01)
        temp = self.slewRateComboBox.currentText()
        # 100% -> 100
        temp = temp[:-1]
        self.slewRateFactor = (float(temp)/100.)

    def cb_toLeftLimit( self): 

        if self.motor.state() == PyTango.DevState.MOVING:
            utils.execStopMove( self.dev)
            self.logWidget.append( "toLeftLimit: moving, sent Stop")
            return
        #
        # involve some rounding
        #
        posReq = float( "%g" % utils.getUnitLimitMin( self.dev, self.logWidget))
        if hasattr( self.motor, "unitbacklash"):
            if self.motor.unitBacklash > 0:
                posReq += self.motor.unitBacklash*1.5 # beware of rounding errors

        self.moveTarget( posReq)

    def cb_toLeftIncr( self): 

        if self.motor.state() == PyTango.DevState.MOVING:
            utils.execStopMove( self.dev)
            self.logWidget.append( "toLeftIncr: moving, sent Stop")
            return

        posReq = utils.getPosition( self.dev) - self.incr
        if posReq > utils.getUnitLimitMin( self.dev, self.logWidget):
            self.moveTargetNoBL( posReq)
        else:
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "%s/%s target position, %g, below unitLimitMin: %g" % (self.dev[ 'hostname'], 
                                                                                              self.dev[ 'device'],
                                                                                              posReq, utils.getUnitLimitMin( self.dev, self.logWidget)), 
                                       QtGui.QMessageBox.Ok)
            

    def cb_toLeftStep( self): 

        if self.motor.state() == PyTango.DevState.MOVING:
            utils.execStopMove( self.dev)
            self.logWidget.append( "toLeftStep: moving, sent Stop")
            return

        blOrig = None
        if hasattr( self.motor, "unitbacklash"):
            blOrig = self.motor.unitbacklash
            self.motor.unitbacklash = 0
        posSteps = self.motor.StepPositionController
        if self.motor.conversion > 0:
            posSteps -= 1
        else:
            posSteps += 1
        self.motor.setupStepMove( posSteps)
        self.motor.startMove()

        while self.motor.state() == PyTango.DevState.MOVING:
            time.sleep(0.01)
        if blOrig is not None:
            self.motor.unitbacklash = bLOrig

    def cb_stop( self): 
        if self.motor.state() == PyTango.DevState.MOVING:
            utils.execStopMove( self.dev)
            while self.motor.state() == PyTango.DevState.MOVING:
                time.sleep(0.01)
        
    def cb_toRightLimit( self): 

        if self.motor.state() == PyTango.DevState.MOVING:
            utils.execStopMove( self.dev)
            self.logWidget.append( "toRightLimit: moving, sent Stop")
            return

        #
        # involve some rounding
        #
        posReq = float( "%g" % utils.getUnitLimitMax( self.dev, self.logWidget))
        if hasattr( self.motor, "unitbacklash"):
            if self.motor.unitBacklash < 0:
                posReq += self.motor.unitBacklash*1.5 # beware of rounding errors

        self.moveTarget( posReq)

    def cb_toRightIncr( self): 

        if self.motor.state() == PyTango.DevState.MOVING:
            utils.execStopMove( self.dev)
            self.logWidget.append( "toRightIncr: moving, sent Stop")
            return

        posReq = utils.getPosition( self.dev) + self.incr
        if posReq < utils.getUnitLimitMax( self.dev, self.logWidget):
            self.moveTargetNoBL( posReq)
        else:
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "%s/%s target position, %g, above unitLimitMax: %g" % (self.dev[ 'hostname'],
                                                                                              self.dev[ 'device'],
                                                                                            posReq, utils.getUnitLimitMax( self.dev, self.logWidget)), 
                                       QtGui.QMessageBox.Ok)

    def cb_toRightStep( self): 

        if self.motor.state() == PyTango.DevState.MOVING:
            utils.execStopMove( self.dev)
            self.logWidget.append( "toRightStep: moving, sent Stop")
            return

        blOrig = None
        if hasattr( self.motor, "unitbacklash"):
            blOrig = self.motor.unitbacklash 
            self.motor.unitbacklash = 0
        posSteps = self.motor.StepPositionController
        if self.motor.conversion > 0:
            posSteps += 1
        else:
            posSteps -= 1
        self.motor.setupStepMove( posSteps)
        self.motor.startMove()

        while self.motor.state() == PyTango.DevState.MOVING:
            time.sleep(0.01)

        if blOrig is not None:
            self.motor.unitbacklash = blOrig

    def getSignal( self):

        #
        # we need at least a counter, the timer may be missing
        #
        if not self.counter:
            return None
        #
        # do not getSignal(), if the motor is moved by some other application
        # the reason why we now execute getSignal() is because the motor might
        # have been moves by '<<' or '>>' meaning it is not moving but in fact
        # has been moved
        #
        #if not self.motorMoving:
        #    return None

        if (self.counterDev[ 'module'] == 'sis3820' or 
            self.counterDev[ 'module'] == 'vfcadc'):
            self.counter.reset()

        if self.timer is not None:
            self.timer.sampleTime = self.sampleTime
            self.timer.start()
            while self.timer.state() == PyTango.DevState.MOVING:
                time.sleep(0.01)
        else:
            time.sleep( self.sampleTime)

        try:
            cts = self.counter.read_attribute( self.counterAttributeName).value
        except Exception, e:
            self.logWidget.append( "getSignal, failed to read_attribte %s (%s)" % 
                                   (self.counterAttributeName, self.counterDev[ 'name']))
            utils.ExceptionToLog( e, self.logWidget)
            return None
 
        if cts > self.signalMax:
            self.signalMax = cts
            self.signalMaxX = utils.getPosition( self.dev)
            self.w_signalMaxLabel.setText( "%g" % cts)
            self.w_signalMaxXLabel.setText( "%g" % self.signalMaxX)

        return cts

    def cb_toMax( self):
        if self.motor.state() == PyTango.DevState.MOVING:
            utils.execStopMove( self.dev)
            while self.motor.state() == PyTango.DevState.MOVING:
                time.sleep(0.01)

        msg = "Move %s to %g" % ( self.dev[ 'name'], self.signalMaxX)
        reply = QtGui.QMessageBox.question(self, 'YesNo', msg, 
                                           QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.moveTarget( self.signalMaxX)

    def enableInputWidgets( self, flag):
        self.w_slider.setEnabled( flag)
        self.moveButton.setEnabled( flag)
        self.w_toLeftLimit.setEnabled( flag)
        self.w_toLeftIncr.setEnabled( flag)
        self.w_toLeftStep.setEnabled( flag)
        self.w_toRightLimit.setEnabled( flag)
        self.w_toRightIncr.setEnabled( flag)
        self.w_toRightStep.setEnabled( flag)

    def cb_launchCursor( self):

        if self.cursorIsActive:
            self.cursorGUI.activateWindow()
            return

        if self.nameGQE is None: 
            self.logWidget.append( "launchCursor: no data")
            return

        self.enableInputWidgets( False)
        self.cursorIsActive = True

        self.cursorGUI = cursorGui.CursorGUI( self.nameGQE, 
                                              self.dev,
                                              logWidget = self.logWidget, 
                                              parent = self)        
        self.cursorGUI.show()
        
    def moveTo( self):
        '''
        read the moveToLine widget and move the motor
        '''
        temp = self.moveToLine.text()
        self.moveToLine.clear()
        if len(temp) == 0:
            return
        posReq = float(temp)
        if hasattr( self.motor, "unitbacklash"):
            if posReq > utils.getUnitLimitMax( self.dev, self.logWidget):
                posReq = utils.getUnitLimitMax( self.dev, self.logWidget)
                if self.motor.unitBacklash < 0:
                    posReq += self.motor.unitBacklash
            if posReq < utils.getUnitLimitMin( self.dev, self.logWidget):
                posReq = utils.getUnitLimitMin( self.dev, self.logWidget)
                if self.motor.unitBacklash > 0:
                    posReq += self.motor.unitBacklash
        self.moveTarget( posReq)

    def moveTarget( self, posReq):

        if self.motor.state() != PyTango.DevState.ON:
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "moveTarget: state != ON (%s)" % self.dev[ 'name'], 
                                       QtGui.QMessageBox.Ok)
            return
            
        self.motorMoving = True
        slewRateOrig = utils.getSlewRate( self.dev, self.logWidget)
        if slewRateOrig is not None:
            utils.setSlewRate( self.dev, slewRateOrig*self.slewRateFactor, self.logWidget) 

        self.targetPosition.setText( "%g" % posReq)
        try:
            utils.setPosition( self.dev, posReq)
        except Exception, e:
            self.logWidget.append( "%s, setting the position causes an error" % (self.dev[ 'name'])) 
            utils.ExceptionToLog( e, self.logWidget)

            if self.motor.state() == PyTango.DevState.MOVING:
                utils.execStopMove( self.dev)
                while self.motor.state() == PyTango.DevState.MOVING:
                    time.sleep(0.01)
            
            self.motorMoving = False
            if slewRateOrig is not None:
                utils.setSlewRate( self.dev, slewRateOrig, self.logWidget) 
            return

        while self.motor.state() == PyTango.DevState.MOVING:
            time.sleep( 0.01)
            QtCore.QCoreApplication.processEvents()
        self.motorMoving = False

        if slewRateOrig is not None:
            utils.setSlewRate( self.dev, slewRateOrig, self.logWidget) 
        
        return 

    def moveTargetNoBL( self, posReq):
        '''
        move to a target position without backlash
        '''
        if self.motor.state() != PyTango.DevState.ON:
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "moveTarget: state != ON (%s)" % self.dev[ 'name'], 
                                       QtGui.QMessageBox.Ok)
            return
            
        self.motorMoving = True
        self.targetPosition.setText( "%g" % posReq)
        blOrig = None
        slewRateOrig = None
        if hasattr( self.motor, "unitbacklash"):
            blOrig = self.motor.unitbacklash 
            self.motor.unitbacklash = 0
        slewRateOrig = utils.getSlewRate( self.dev, self.logWidget)
        if slewRateOrig is not None:
            utils.setSlewRate( self.dev, slewRateOrig*self.slewRateFactor, self.logWidget) 
        try:
            utils.setPosition( self.dev, posReq)
        except Exception, e:
            self.logWidget.append( "%s, setting the position causes an error" % (self.dev[ 'name'])) 
            utils.ExceptionToLog( e, self.logWidget)

            self.motorMoving = False
            if blOrig is not None:
                self.motor.unitBacklash = blOrig
            if slewRateOrig is not None:
                utils.setSlewRate( self.dev, slewRateOrig, self.logWidget)
            return

        #self.w_slider.setFocus()

        while self.motor.state() == PyTango.DevState.MOVING:
            time.sleep( 0.01)
            QtCore.QCoreApplication.processEvents()
        self.motorMoving = False
        if blOrig is not None:
            self.motor.unitBacklash = blOrig
        if slewRateOrig is not None:
            utils.setSlewRate( self.dev, slewRateOrig, self.logWidget)
        
        return 

    def cb_launchAttr( self):

        if self.flagOffline:
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "launchAttr: %s, device is offline" % self.dev[ 'name'], 
                                       QtGui.QMessageBox.Ok)
            return
        # 
        # remove 'self.' to allow for one widget only
        # 
        self.w_attr = tngAPI.deviceAttributes( self.dev, self.logWidget, self)
        self.w_attr.show()

    def cb_launchCommand( self):

        try:
            sts = self.dev[ 'proxy'].state()
        except Exception, e:
            utils.ExceptionToLog( e, self.logWidget)
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "cb_commands: %s, device is offline" % self.dev[ 'name'], 
                                       QtGui.QMessageBox.Ok)
            return 
                
        # 
        # remove 'self.' to allow for one widget only
        # 
        self.w_commands = tngAPI.deviceCommands( self.dev, self.logWidget, self)
        self.w_commands.show()
        return 


    def cb_launchProp( self):

        self.w_prop = tngAPI.deviceProperties( self.dev, self.logWidget, self)
        self.w_prop.show()


    def cb_launchEncAttr( self):

        if self.flagOffline:
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "launchEncAttr: %s, device is offline" % self.dev[ 'name'], 
                                       QtGui.QMessageBox.Ok)
            return
        self.w_encAttr = motorEncAttributes( self.dev, self.logWidget, self)
        self.w_encAttr.show()


    def cb_launchZmxAttr( self):

        self.w_zmxAttr = motorZmxAttributes( self.dev, self.logWidget, self)
        self.w_zmxAttr.show()
