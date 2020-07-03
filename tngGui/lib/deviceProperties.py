#!/usr/bin/env python

#from taurus.external.qt import QtGui, QtCore 
from PyQt4 import QtCore, QtGui
import PyTango
import math, os
import HasyUtils
import tngGui.lib.utils as utils
import tngGui.lib.definitions as definitions
import json
import tngGui.lib.helpBox as helpBox

class deviceProperties( QtGui.QMainWindow):
    def __init__( self, dev, logWidget, parent = None):
        super( deviceProperties, self).__init__( parent)
        self.parent = parent
        self.dev = dev
        self.setWindowTitle( "Properties of %s" % self.dev[ 'name'])
        self.logWidget = logWidget
        self.selectWidthDone = False # set the widget sizes only once
        w = QtGui.QWidget()
        self.layout_v = QtGui.QVBoxLayout()
        w.setLayout( self.layout_v)
        self.setCentralWidget( w)
        alias_l = QtGui.QLabel( self.dev[ 'name'])
        name_l = QtGui.QLabel( self.dev[ 'fullName'])
        layout_h = QtGui.QHBoxLayout()
        layout_h.addWidget( alias_l)
        layout_h.addWidget( name_l)
        self.layout_v.addLayout( layout_h)
        self.layout_grid = QtGui.QGridLayout()
        self.layout_v.addLayout( self.layout_grid)
        count = 0
        propNames = self.dev[ 'proxy'].get_property_list( "*")
        self.props = []
        for p in propNames:
            if p.find( "_") == 0:
                continue
            self.props.append( p)
        
        self.propDct = {}

        for prop in self.props:
            name = QtGui.QLabel( prop)
            self.layout_grid.addWidget( name, count, 0)
            
            value = QtGui.QLabel()
            value.setFixedWidth( definitions.POSITION_WIDTH_PROP)
            value.setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
            self.layout_grid.addWidget( value, count, 1)

            line = QtGui.QLineEdit()
            line.setFixedWidth( 200)
            line.setAlignment( QtCore.Qt.AlignRight)
            self.layout_grid.addWidget( line, count, 2)
            
            self.propDct[ prop] = { "w_value": value, "w_line": line}

            if prop == 'VcCode' or prop == 'VmCode': 
                b = QtGui.QPushButton(self.tr("Edit")) 
                self.layout_grid.addWidget( b, count, 3)
                fName = HasyUtils.getDeviceProperty( self.dev[ 'device'], prop, self.dev[ 'hostname'])
                b.setToolTip( "Edit %s" % fName[0])
                QtCore.QObject.connect( b, QtCore.SIGNAL( utils.fromUtf8("clicked()")), self.make_cb_editCallback( fName[0]))
                b = QtGui.QPushButton(self.tr("Restart")) 
                self.layout_grid.addWidget( b, count, 4)
                srv = HasyUtils.getServerNameByDevice( self.dev[ 'device'], self.dev[ 'hostname'])
                b.setToolTip( "Restart %s on %s" % (srv, self.dev[ 'hostname']))
                QtCore.QObject.connect( b, QtCore.SIGNAL( utils.fromUtf8("clicked()")), self.make_cb_restartCallback( srv, self.dev[ 'hostname']))
            else: 
                self.layout_grid.addWidget( QtGui.QLabel(), count, 3)
                self.layout_grid.addWidget( QtGui.QLabel(), count, 4)
                
            count += 1
        #
        # Menu Bar
        #
        self.menuBar = QtGui.QMenuBar()
        self.setMenuBar( self.menuBar)
        self.fileMenu = self.menuBar.addMenu('&File')
        self.exitAction = QtGui.QAction('E&xit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect( self.cb_closeMotorProp)
        self.fileMenu.addAction( self.exitAction)

        #
        # the activity menubar: help and activity
        #
        self.menuBarActivity = QtGui.QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarActivity, QtCore.Qt.TopRightCorner)

        self.helpMenu = self.menuBarActivity.addMenu('Help')

        if self.dev[ 'module'].lower() == 'oms58':
            self.helpWidget = self.helpMenu.addAction(self.tr("Properties"))
            self.helpWidget.triggered.connect( self.cb_helpWidget)

        self.activityIndex = 0
        self.activity = self.menuBarActivity.addMenu( "_")

        #
        # Status Bar
        #
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar( self.statusBar)


        self.attributes = QtGui.QPushButton(self.tr("Attributes")) 
        self.statusBar.addWidget( self.attributes)
        QtCore.QObject.connect( self.attributes, QtCore.SIGNAL( utils.fromUtf8("clicked()")), self.cb_launchAttributes)

        self.commands = QtGui.QPushButton(self.tr("Commands")) 
        self.statusBar.addWidget( self.commands)
        QtCore.QObject.connect( self.commands, QtCore.SIGNAL( utils.fromUtf8("clicked()")), self.cb_launchCommands)
        
        self.apply = QtGui.QPushButton(self.tr("&Apply")) 
        self.statusBar.addPermanentWidget( self.apply) # 'permanent' to shift it right
        QtCore.QObject.connect( self.apply, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_applyDeviceProperties)
        self.apply.setShortcut( "Alt+a")

        self.exit = QtGui.QPushButton(self.tr("E&xit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        QtCore.QObject.connect( self.exit, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_closeMotorProp)
        self.exit.setShortcut( "Alt+x")

        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect( self.cb_refreshProp)
        self.updateTimer.start( definitions.TIMEOUT_REFRESH)

    def make_cb_editCallback( self, fName): 
        def sub(): 
            editor = os.getenv( "EDITOR")
            if editor is None:
                editor = "emacs"
            self.logWidget.append( "%s %s&" % (editor, fName))
            os.system( "%s %s&" % (editor, fName))
            return 
        return sub

    def make_cb_restartCallback( self, srvName, hostName): 
        def sub(): 
            self.logWidget.append( "restart %s on %s" % (srvName, hostName))
            HasyUtils.restartServer( srvName, hostName)
            return 
        return sub

            
    def cb_helpWidget( self):
        w = helpBox.HelpBox( self, self.tr("Help Widget"), self.tr(
            "<h3>Properties</h3><p>"
            "Can only be changed with this widget. To create them use <b>jive</b>"
            "<ul>"
            "<li><b>Base</b> VME base address, see the hardware manual"
            "<li><b>Channel</b> 0 - 7"
            "<li><b>FlagCutOrMap</b> 0- ignore, 1 - cut, 2 - map <br>"
            "Cutting point: cannot be passed through, the position stays in [cut, cut + 360[<br>"
            "Mapping point: the position is kept in [map, map + 360[, automatic recalibrations<br>"
            "Cut/map: CutOrMap attribute"
            "<li><b>FlagEncoder</b> 0 - no encoder, 1 - encoder connected"
            "<li><b>HomeDefinition</b> def.: EH111<br>"
            "EHhiba: h - home, i - index, b - phase, a - phase"
            "<li><b>HomeIndexDefinition</b> def. 1, 1 - enable encoder index, phase a and B, 0 - disables I, A, B"
            "<li><b>IgnoreLimitSw</b> expert feature, 0 - the server will sense limit switch signal, "
            "1 - the server ignores any limit switch signal"
            "<li><b>MaxVSerie</b> 0 - OmsVme58 (Doris hardware), 1 - MaxV (Petra hardware)"
            "<li><b>SimulationMode</b> expert feature, 0 - no simulation, 1 - simulation (only for office PCs)"
            "<li><b>AccuMax</b> maximum step register value, MaxV: 2147483647, OmsVme58: 33500000"
            "<li><b>AccuMin</b> minimum step register value, MaxV: -2147483647, OmsVme58: 33500000"
            "<li><b>AccelerationMaxHw</b> 1000000000"
            "<li><b>AccelerationMinHw</b> 0"
            "<li><b>SlewRateMaxHw</b> MaxV: 4194303, OmsVme58: 104400, this property can be used as a safety measure"
            "<li><b>SlewRateMinHw</b> 0"
            "<li><b>Type</b> 0 - stepper, 1 - servo"
            "<li><b>ZMXDevice</b> the device name of a connected ZMX, will be checked before moves"
            "</ul>"
                ))
        w.show()


    def cb_launchAttributes( self):
        import tngGui.lib.deviceAttributes as deviceAttributes
        self.w_attr = deviceAttributes.deviceAttributes( self.dev, self.logWidget, self)
        self.w_attr.show()
        return 

    def cb_launchCommands( self):
        # 
        # remove 'self.' to allow for one widget only
        # 
        import tngGui.lib.deviceCommands as deviceCommands
        self.w_commands = deviceCommands.deviceCommands( self.dev, self.logWidget, self)
        self.w_commands.show()
        return 
        
    def cb_refreshProp( self):

        if self.isMinimized(): 
            return

        self.activityIndex += 1
        if self.activityIndex > (len( definitions.ACTIVITY_SYMBOLS) - 1):
            self.activityIndex = 0
        self.activity.setTitle( definitions.ACTIVITY_SYMBOLS[ self.activityIndex])
        
        if not self.selectWidthDone: 
            self.selectWidthDone = True
            #
            # find maximum length
            #
            lenMax = 0
            for prop in self.props:
                propValue = HasyUtils.getDeviceProperty( self.dev[ 'device'], prop, self.dev[ 'hostname'])
                if propValue is None:
                    print( "deviceProperties, %s %s %s has value None" % ( self.dev[ 'device'], self.dev[ 'hostname'], prop))
                    continue
                if len( propValue) == 1:
                    if len( str( propValue[0])) > lenMax:
                        lenMax = len( str( propValue[0]))

            widthProp = definitions.POSITION_WIDTH_PROP
            if lenMax*9 > definitions.POSITION_WIDTH_PROP:
                widthProp = lenMax*9
            if widthProp > 500:
                widthProp = 500

            for prop in self.props:
                w_value = self.propDct[ prop][ "w_value"]
                w_value.setFixedWidth( widthProp)

        for prop in self.props:
            w_value = self.propDct[ prop][ "w_value"]
            propValue = HasyUtils.getDeviceProperty( self.dev[ 'device'], prop, self.dev[ 'hostname'])
            if propValue is None:
                print( "deviceProperties (1), %s %s %s has value None" % ( self.dev[ 'device'], self.dev[ 'hostname'], prop))
                continue
            if len( propValue) == 0:
                w_value.setText( "None")
            elif len( propValue) == 1:
                w_value.setText( str(propValue[0]))
            else:
                w_value.setText( 'Failed to display')

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
