#!/usr/bin/env python

import sys, math, time, os, json, signal, argparse
import Spectra, HasyUtils
#from PyQt4 import QtGui
#from PyQt4 import QtCore
from taurus.external.qt import QtGui, QtCore 
import numpy as np

import lib.helpBox as helpBox
import lib.defineSignal as defineSignal
import lib.moveMotor as moveMotor
import lib.tngAPI as tngAPI
import lib.utils as utils
import lib.definitions as definitions

import PyTango

allDevices = []
selectedMotors = []
allMotors = []
allIRegs = []
allORegs = []
allAdcs = []
allMCAs = []
allVfcAdcs = []
allCameras = []
allPiLCModules = []
allModuleTangos = []
allDacs = []
allTimers = []
allCounters = []        # sis3820
allTangoAttrCtrls = []
allTangoCounters = []   # VcExecutors
#
# list those modules that have the attribite widget prepared
#
cameraNames = ['eigerdectris', 'lambda','pilatus100k', 'pilatus300k', 'pilatus1m', 'pilatus2m', 'pilatus6m']

PiLCModuleNames = ['pilc_module']

modulesRoiCounters = ['mca8715roi', 
                      'vortex_roi1', 'vortex_roi2', 'vortex_roi3', 'vortex_roi4', 
                      'amptekroi',
                      'mythenroi']



class motorMenu( QtGui.QMainWindow):
    '''
    the main class of the TngTool application
    '''
    def __init__( self, timerName, counterName, parent = None):
        super( motorMenu, self).__init__( parent)
        self.setWindowTitle( "TngTool")
        
        self.timerName = timerName
        self.counterName = counterName
        self.move( 700, 20)

        self.prepareWidgets()

        self.prepareMenuBar()

        self.prepareStatusBar()

        self.updateCount = 0

        self.refreshFunc = self.refreshMotors

        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect( self.cb_refreshMain)
        self.updateTimer.start( definitions.TIMEOUT_REFRESH)

    #
    # the central part
    #
    def prepareWidgets( self):
        self.centralWidget = QtGui.QWidget()
        self.setCentralWidget( self.centralWidget)
        self.layout_v = QtGui.QVBoxLayout()
        self.centralWidget.setLayout( self.layout_v)

        #
        # log widget, used by fillMotorList()
        #
        self.logWidget = QtGui.QTextEdit()
        self.logWidget.setMinimumHeight( 200)
        self.logWidget.setReadOnly( 1)

        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setMinimumWidth( 800)
        if len( selectedMotors) < 5:
            self.scrollArea.setMinimumHeight( 200)
        elif len( selectedMotors) < 9:
            self.scrollArea.setMinimumHeight( 400)
        else:
            self.scrollArea.setMinimumHeight( 600)

        self.base = None
        #
        # fill-in the motors
        #
        self.fillMotorList()

        self.layout_v.addWidget( self.scrollArea)
        self.layout_v.addWidget( self.logWidget)
    #
    # the menubar
    #
    def prepareMenuBar( self):
        #
        # Menu Bar
        #
        self.menuBar = QtGui.QMenuBar()
        self.setMenuBar( self.menuBar)

        #
        # File menu
        #
        self.fileMenu = self.menuBar.addMenu('&File')

        self.exitAction = QtGui.QAction('E&xit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect( QtGui.QApplication.quit)
        self.fileMenu.addAction( self.exitAction)

        #
        # Tools menu
        #
        self.toolsMenu = self.menuBar.addMenu('&Tools')

        self.nxselectorAction = QtGui.QAction('Nxselector', self)        
        self.nxselectorAction.triggered.connect( self.cb_launchNxselector)

        self.macroguiAction = QtGui.QAction('Macrogui', self)        
        self.macroguiAction.triggered.connect( self.cb_launchMacrogui)

        self.motorMonitorAction = QtGui.QAction('SardanaMotorMonitor', self)        
        self.motorMonitorAction.triggered.connect( self.cb_launchMotorMonitor)

        self.sardanaMonitorAction = QtGui.QAction('SardanaMonitor', self)        
        self.sardanaMonitorAction.triggered.connect( self.cb_launchSardanaMonitor)

        self.spockAction = QtGui.QAction('Spock', self)        
        self.spockAction.triggered.connect( self.cb_launchSpock)

        self.toolsMenu.addAction( self.spockAction)
        self.toolsMenu.addAction( self.nxselectorAction)
        self.toolsMenu.addAction( self.sardanaMonitorAction)
        self.toolsMenu.addAction( self.motorMonitorAction)
        self.toolsMenu.addAction( self.macroguiAction)
        #self.toolsMenu.addAction( self.spectraAction)

        #
        # Files
        #
        self.miscMenu = self.menuBar.addMenu('Files')
        self.editOnlineXmlAction = QtGui.QAction('online.xml', self)        
        self.editOnlineXmlAction.triggered.connect( self.cb_editOnlineXml)
        self.miscMenu.addAction( self.editOnlineXmlAction)

        self.editTangoDumpLisAction = QtGui.QAction('TangoDump.lis', self)        
        self.editTangoDumpLisAction.triggered.connect( self.cb_editTangoDumpLis)
        self.miscMenu.addAction( self.editTangoDumpLisAction)

        self.editMotorLogLisAction = QtGui.QAction('motorLog.lis', self)        
        self.editMotorLogLisAction.triggered.connect( self.cb_editMotorLogLis)
        self.miscMenu.addAction( self.editMotorLogLisAction)

        self.editIpythonLogAction = QtGui.QAction('/online_dir/ipython_log.py', self)        
        self.editIpythonLogAction.triggered.connect( self.cb_editIpythonLog)
        self.miscMenu.addAction( self.editIpythonLogAction)

        self.editSardanaConfigAction = self.miscMenu.addAction(self.tr("SardanaConfig.py"))   
        self.editSardanaConfigAction.triggered.connect( self.cb_editSardanaConfig)

        self.edit00StartAction = QtGui.QAction('00-start.py', self)  
        self.edit00StartAction.triggered.connect( self.cb_edit00Start)
        self.miscMenu.addAction( self.edit00StartAction)

        self.helpFilesAction = self.miscMenu.addAction(self.tr("Help Files"))
        self.connect(self.helpFilesAction, QtCore.SIGNAL("triggered()"), self.cb_helpFiles)

        #
        # Misc
        #
        self.miscMenu = self.menuBar.addMenu('Misc')

        self.restartTimerAction = QtGui.QAction('Restart Timer', self)        
        self.restartTimerAction.setStatusTip('Restart update timer')
        self.restartTimerAction.triggered.connect( self.cb_restartTimer)
        self.miscMenu.addAction( self.restartTimerAction)

        self.stopTimerAction = QtGui.QAction('Stop Timer', self)        
        self.stopTimerAction.setStatusTip('Stop update timer')
        self.stopTimerAction.triggered.connect( self.cb_stopTimer)
        self.miscMenu.addAction( self.stopTimerAction)

        self.logToTempFileAction = QtGui.QAction('Write log widget to file and edit it.', self)
        self.logToTempFileAction.triggered.connect( self.cb_logToTempFile)
        self.miscMenu.addAction( self.logToTempFileAction)

        #
        # selected MacroServer variables
        #
        self.macroServerAction = QtGui.QAction('MacroServer (Selected Vars)', self)        
        self.macroServerAction.setStatusTip('Selected MacroServer variables')
        self.macroServerAction.triggered.connect( self.cb_msIfc)
        self.miscMenu.addAction( self.macroServerAction)
        #
        # Table
        #
        self.tableMenu = self.menuBar.addMenu('Table')

        self.motorTableAction = QtGui.QAction('Motors', self)        
        self.motorTableAction.triggered.connect( self.cb_motorTable)
        self.tableMenu.addAction( self.motorTableAction)

        if len( allAdcs) > 0 or len(allDacs) > 0:
            self.adcDacTableAction = QtGui.QAction('ADC/DACs', self)        
            self.adcDacTableAction.triggered.connect( self.cb_adcDacTable)
            self.tableMenu.addAction( self.adcDacTableAction)

        if len( allCameras) > 0:
            self.cameraTableAction = QtGui.QAction('Cameras', self)        
            self.cameraTableAction.triggered.connect( self.cb_cameraTable)
            self.tableMenu.addAction( self.cameraTableAction)

        if len( allCounters) or len( allTangoAttrCtrls) > 0 or len( allTangoCounters) > 0:
            self.counterTableAction = QtGui.QAction('Counters', self)        
            self.counterTableAction.triggered.connect( self.cb_counterTable)
            self.tableMenu.addAction( self.counterTableAction)

        if len( allIRegs) > 0 or len(allORegs) > 0:
            self.ioregTableAction = QtGui.QAction('IORegs', self)        
            self.ioregTableAction.triggered.connect( self.cb_ioregTable)
            self.tableMenu.addAction( self.ioregTableAction)

        if len( allMCAs) > 0:
            self.mcaTableAction = QtGui.QAction('MCAs', self)        
            self.mcaTableAction.triggered.connect( self.cb_mcaTable)
            self.tableMenu.addAction( self.mcaTableAction)

        if len( allModuleTangos) > 0:
            self.moduleTangoTableAction = QtGui.QAction('ModuleTango', self)        
            self.moduleTangoTableAction.triggered.connect( self.cb_moduleTangoTable)
            self.tableMenu.addAction( self.moduleTangoTableAction)

        if len( allPiLCModules) > 0:
            self.PiLCModulesTableAction = QtGui.QAction('PiLCModules', self)        
            self.PiLCModulesTableAction.triggered.connect( self.cb_PiLCModulesTable)
            self.tableMenu.addAction( self.PiLCModulesTableAction)

        if len( allTimers) > 0:
            self.timerTableAction = QtGui.QAction('Timers (extra widget)', self)        
            self.timerTableAction.triggered.connect( self.cb_launchTimer)
            self.tableMenu.addAction( self.timerTableAction)

        if len( allVfcAdcs) > 0:
            self.vfcadcTableAction = QtGui.QAction('VFCADCs', self)        
            self.vfcadcTableAction.triggered.connect( self.cb_vfcadcTable)
            self.tableMenu.addAction( self.vfcadcTableAction)

        #
        # the activity menubar: help and activity
        #
        self.menuBarActivity = QtGui.QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarActivity, QtCore.Qt.TopRightCorner)

        #
        # Help menu 
        #
        self.helpMenu = self.menuBarActivity.addMenu('Help')
        self.versionAction = self.helpMenu.addAction(self.tr("Version"))
        self.versionAction.triggered.connect( self.cb_version)
        self.colorCodeAction = self.helpMenu.addAction(self.tr("Color code"))
        self.colorCodeAction.triggered.connect( self.cb_colorCode)

        self.activityIndex = 0
        self.activity = self.menuBarActivity.addMenu( "_")

    def cb_launchTimer( self): 
        self.w_timer = tngAPI.timerWidget( self.logWidget, allTimers, self)
        self.w_timer.show()

    def cb_motorTable( self):
        self.fillMotorList()
        
    def cb_ioregTable( self):
        self.fillIORegs()
        
    def cb_adcDacTable( self):
        self.fillAdcDacs()
        
    def cb_cameraTable( self):
        self.fillCameras()
        
    def cb_PiLCModulesTable( self):
        self.fillPiLCModules()
        
    def cb_moduleTangoTable( self):
        self.fillModuleTangos()
        
    def cb_mcaTable( self):
        self.fillMCAs()
        
    def cb_counterTable( self):
        self.fillCounters()
        
    def cb_vfcadcTable( self):
        self.fillVfcAdcs()
    #
    # the closeEvent is called when the window is closed by 
    # clicking the X at the right-upper corner of the frame
    #
    def closeEvent( self, e):
        self.cb_closeMotorMenu()
        #e.ignore()
    
    def cb_closeMotorMenu( self):
        self.cb_stopMove()

    def cb_editOnlineXml( self):
        if not os.access( "/online_dir/online.xml", os.R_OK):
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "/online_dir/online.xml does not exist",
                                       QtGui.QMessageBox.Ok)
            return
        os.system( "test -e /usr/local/bin/vrsn && /usr/local/bin/vrsn -s /online_dir/online.xml")
        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s /online_dir/online.xml&" % editor)

    def cb_editTangoDumpLis( self):
        if not os.access( "/online_dir/TangoDump.lis", os.R_OK):
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "/online_dir/TangoDump.lis does not exist",
                                       QtGui.QMessageBox.Ok)
            return
        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s /online_dir/TangoDump.lis&" % editor)

    def cb_editMotorLogLis( self):
        if not os.access( "/online_dir/MotorLogs/motorLog.lis", os.R_OK):
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "/online_dir/MotorLogs/motorLog.lis does not exist",
                                       QtGui.QMessageBox.Ok)
            return
        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s /online_dir/MotorLogs/motorLog.lis&" % editor)

    def cb_editIpythonLog( self):
        if not os.access( "/online_dir/ipython_log.py", os.R_OK):
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "/online_dir/ipython_log.py does not exist",
                                       QtGui.QMessageBox.Ok)
            return
        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s /online_dir/ipython_log.py&" % editor)


    def cb_editSardanaConfig( self):
        if not os.access( "/online_dir/SardanaConfig.py", os.R_OK):
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "/online_dir/SardanaConfig.py does not exist",
                                       QtGui.QMessageBox.Ok)
            return
        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s /online_dir/SardanaConfig.py&" % editor)

    def cb_edit00Start( self):
        home = os.getenv( "HOME")
        fName = "%s/.ipython/profile_spockdoor/startup/00-start.py" % home
        if not os.access( fName, os.R_OK):
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "%s does not exist" % fName,
                                       QtGui.QMessageBox.Ok)
            return
        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s %s&" % (editor, fName))
        
    def cb_helpFiles( self): 
        w = helpBox.HelpBox(self, self.tr("HelpWidget"), self.tr(
            "\
<p><b>Help Files</b><p>\
<ul>\
<li> the files are opened by EDITOR (environment variable) or emacs\
<li> TangoDump.lis, motorLog.lis: mind that\
<ul>\
<li> these files are versioned\
<li>also have python versions\
</ul>\
<li> /online_dir/SardanaConfig.py is executed at the end of the SardanaStartup.py (implicitly also by SardanaAIO.py)\
<li> 00-start.py: spock startup script \
</ul>"
                ))
        w.show()
        
    def cb_restartTimer( self):
        self.updateTimer.stop()
        self.updateTimer.start( definitions.TIMEOUT_REFRESH)
        
    def cb_stopTimer( self):
        self.updateTimer.stop()

    def cb_logToTempFile( self):
        fName = HasyUtils.createScanName( "smm") + ".lis"
        try:
            out = open( fName, "w")
        except Exception, e:
            self.logWidget( "Failed to open %s" % fName)
            self.logWidget( repr( e))
            return
        lst = self.logWidget.toPlainText()
        out.writelines(lst)
        out.close()
        self.logWidget.append( "Save log widget contents to %s" % fName)
        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s %s&" % (editor, fName))

    #
    # the status bar
    #
    def prepareStatusBar( self):
        #
        # Status Bar
        #
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar( self.statusBar)

        self.stopMove = QtGui.QPushButton(self.tr("&Stop")) 
        self.stopMove.setToolTip( "Stop m1oving motors")
        self.statusBar.addWidget( self.stopMove) 
        self.stopMove.clicked.connect( self.cb_stopMove)
        self.stopMove.setShortcut( "Alt+s")
        #
        # MacroServer Ifc
        #
        #self.msIfc = QtGui.QPushButton(self.tr("MacroServer")) 
        #self.msIfc.setToolTip( "Selected MacroServer variables")
        #self.statusBar.addPermanentWidget( self.msIfc) # 'permanent' to shift it right
        #self.msIfc.clicked.connect( self.cb_msIfc)

        #self.clear.setShortcut( "Alt+c")
        #
        # clear log widget
        #
        self.clear = QtGui.QPushButton(self.tr("Clear")) 
        self.statusBar.addPermanentWidget( self.clear) # 'permanent' to shift it right
        QtCore.QObject.connect( self.clear, QtCore.SIGNAL( utils.fromUtf8("clicked()")), self.cb_clear)
        #
        # exit
        #
        self.exit = QtGui.QPushButton(self.tr("E&xit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        QtCore.QObject.connect( self.exit, QtCore.SIGNAL( utils.fromUtf8("clicked()")), self.close)
        self.exit.setShortcut( "Alt+x")

    def cb_stopMove( self):
        for dev in selectedMotors:
            if dev[ 'proxy'].state() == PyTango.DevState.MOVING:
                execStopMove( dev)

    def cb_msIfc( self):
        ms = MacroServerIfc( self.logWidget, self)
        ms.show()

    def cb_launchNxselector( self):
        #import imp
        #a = imp.load_source( '', '/usr/bin/nxselector')
        #self.nxselector = a.main()
        os.system( "/usr/bin/nxselector &")

    def cb_launchMacrogui( self):
        os.system( "/usr/bin/taurusgui macrogui &")

    def cb_launchMotorMonitor( self):
        os.system( "/usr/bin/SardanaMotorMonitor.py &")

    def cb_launchSardanaMonitor( self):
        os.system( "/usr/bin/SardanaMonitor.py &")

    def cb_launchSpock( self):
        display = os.getenv( "DISPLAY")
        if display == ':0':
            sts = os.system( "gnome-terminal -e /usr/bin/spock -t spock &")
        else:
            sts = os.system( "xterm -e /usr/bin/spock &")

    def __del__( self):
        print "the destructor of main()"

    def cb_clear( self):
        self.logWidget.clear()

    def cb_version(self):
        w = helpBox.HelpBox(self, self.tr("HelpWidget"), self.tr(
            "<h3> Version history</h3>"
            "<ul>"
            "<li> 13.06.2019: Attributes and properties available for various devices </li>"
            "<li> 06.06.2019: Color orange for status == DISABLE (e.g. undulator) </li>"
            "<li> 11.06.2018: Pool motors not appearing in online.xml are included (e.g.: exp_dmy01, e6cctrl_h) </li>"
            "<li> 11.06.2018: Signal can be without timer </li>"
            "<li> 11.06.2018: tangoattributectctrl can be used as signal </li>"
            "<li> 11.04.2018: EDITOR online.xml </li>"
            "<li> 10.04.2018: Selected MacroServer Variables </li>"
            "<li> 23.03.2018: vfcadcs and vcexecutors can be signal counters </li>"
            "</ul>"
                ))
        w.show()

    def cb_colorCode( self):
        w = helpBox.HelpBox( self, title = self.tr("Help Update Rate"), text = self.tr(
            "<h3>Color Code</h3>"
            "<ul>"
            "<li> blue    MOVING"
            "<li> green   OK"
            "<li> magenta DISABLE (position) "
            "<li> red     ALARM or Upper/lower limit"
            "</ul>"
                ))
        w.show()

    def fillMotorList( self):

        if self.base is not None:
            self.base.destroy( True, True)

        self.base = QtGui.QWidget()
        layout_grid = QtGui.QGridLayout()
        
        layout_grid.addWidget( QtGui.QLabel( "Alias"), 0, 0)
        layout_grid.addWidget( QtGui.QLabel( "Position"), 0, 1)
        layout_grid.addWidget( QtGui.QLabel( "Min"), 0, 2)
        layout_grid.addWidget( QtGui.QLabel( "Max"), 0, 3)
        layout_grid.addWidget( QtGui.QLabel( "Module"), 0, 4)
        layout_grid.addWidget( QtGui.QLabel( "DeviceName"), 0, 5)

        count = 1
        hndlr = signal.getsignal( signal.SIGALRM)
        signal.signal( signal.SIGALRM, self.handlerALRM)

        for dev in selectedMotors:
            #print "connecting to", dev[ 'name']
            signal.alarm( 2)
            try:
                b = utils.QPushButtonTK(self.tr("%s" % dev[ 'name'])) 
                b.setToolTip( "MB-1: move menu\nMB-2: attributes (oms58, dac, motor_tango)\nMB-3: encAttributes (if FlagEncoder)")
                
                b.mb1.connect( self.make_cb_move( dev, self.logWidget))
                b.mb2.connect( self.make_cb_attributes( dev, self.logWidget))
                b.mb3.connect( self.make_cb_mb3( dev, self.logWidget))
                layout_grid.addWidget( b, count, 0)
                #
                # position
                #
                # Note: we have to store the widget in dev, not in self because
                #       we have many of them
                #
                dev[ 'w_pos'] = QtGui.QLabel( "0.0")
                dev[ 'w_pos'].setObjectName( dev['name'])
                dev[ 'w_pos'].setFixedWidth( definitions.POSITION_WIDTH)
                dev[ 'w_pos'].setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
                layout_grid.addWidget( dev[ 'w_pos'], count, 1 )
                #
                # unitlimitmin, ~max
                #
                dev[ 'w_unitlimitmin'] = QtGui.QLabel( "0.0")
                dev[ 'w_unitlimitmin'].setFixedWidth( definitions.POSITION_WIDTH)
                dev[ 'w_unitlimitmin'].setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
                dev[ 'w_unitlimitmax'] = QtGui.QLabel( "0.0")
                dev[ 'w_unitlimitmax'].setFixedWidth( definitions.POSITION_WIDTH)
                dev[ 'w_unitlimitmax'].setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
                layout_grid.addWidget( dev[ 'w_unitlimitmin'], count, 2 )
                layout_grid.addWidget( dev[ 'w_unitlimitmax'], count, 3 )
                #
                # module
                #
                moduleName = QtGui.QLabel()
                moduleName.setText( "%s" % (dev['module']))
                moduleName.setAlignment( QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter)
                layout_grid.addWidget( moduleName, count, 4 )
                #
                # device name
                #
                devName = QtGui.QLabel()
                devName.setText( "%s/%s" % (dev['hostname'], dev['device']))
                devName.setAlignment( QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter)
                layout_grid.addWidget( devName, count, 5 )

                count += 1
                    
            except utils.TMO, e:
                print "fillMotorList: failed to connect to", dev[ 'name']
                del dev
            signal.alarm(0)
        signal.signal( signal.SIGALRM, hndlr)
        self.base.setLayout( layout_grid)
        self.scrollArea.setWidget( self.base)
        self.refreshFunc = self.refreshMotors

        #print "launching widget"

    def fillIORegs( self):

        if self.base is not None:
            self.base.destroy( True, True)

        self.base = QtGui.QWidget()
        layout_grid = QtGui.QGridLayout()

        layout_grid.addWidget( QtGui.QLabel( "Alias"), 0, 0)
        layout_grid.addWidget( QtGui.QLabel( "State"), 0, 1)
        layout_grid.addWidget( QtGui.QLabel( "Module"), 0, 2)
        layout_grid.addWidget( QtGui.QLabel( "DeviceName"), 0, 3)

        #
        # <device>
        # <name>d1_ireg01</name>
        # <type>input_register</type>
        # <module>sis3610</module>
        # <device>p09/register/d1.in01</device>
        # <control>tango</control>
        # <hostname>haso107d1:10000</hostname>
        # <channel>1</channel>
        # </device>
        #
        count = 1
        for dev in allIRegs:
            aliasName = utils.QPushButtonTK( dev['name'])
            aliasName.setToolTip( "MB-1: Attributes\nMB-2: Commands\nMB-3: Properties")
            aliasName.mb1.connect( self.make_cb_attributes( dev, self.logWidget))
            aliasName.mb2.connect( self.make_cb_commands( dev, self.logWidget))
            aliasName.mb3.connect( self.make_cb_properties( dev, self.logWidget)) 
            layout_grid.addWidget( aliasName, count, 0)

            dev[ 'w_value'] = QtGui.QLabel( "0")
            dev[ 'w_value'].setFixedWidth( 50)
            dev[ 'w_value'].setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
            layout_grid.addWidget( dev[ 'w_value'], count, 1)

            moduleName = QtGui.QLabel()
            moduleName.setText( "%s" % (dev['module']))
            moduleName.setAlignment( QtCore.Qt.AlignLeft)
            moduleName.setFixedWidth( definitions.POSITION_WIDTH)
            layout_grid.addWidget( moduleName, count, 2 )
            #
            # device name
            #
            devName = QtGui.QLabel()
            devName.setText( "%s/%s" % (dev['hostname'], dev['device']))
            devName.setAlignment( QtCore.Qt.AlignLeft)
            layout_grid.addWidget( devName, count, 3 )
            
            count += 1

        for dev in allORegs:
            aliasName = utils.QPushButtonTK(self.tr("%s" % dev[ 'name'])) 
            aliasName.setToolTip( "MB-1: Attributes\nMB-2: Commands\nMB-3: Properties")
            aliasName.mb1.connect( self.make_cb_attributes( dev, self.logWidget))
            aliasName.mb2.connect( self.make_cb_commands( dev, self.logWidget))
            aliasName.mb3.connect( self.make_cb_properties( dev, self.logWidget)) 
            layout_grid.addWidget( aliasName, count, 0)

            dev[ 'w_value'] = utils.QPushButtonTK( dev['name'])
            dev[ 'w_value'].setToolTip( "MB-1: toggle ouput state")
            dev[ 'w_value'].mb1.connect( self.make_cb_oreg( dev, self.logWidget))
            dev[ 'w_value'].setFixedWidth( 50)
            layout_grid.addWidget( dev[ 'w_value'], count, 1)

            moduleName = QtGui.QLabel()
            moduleName.setText( "%s" % (dev['module']))
            moduleName.setAlignment( QtCore.Qt.AlignLeft)
            moduleName.setFixedWidth( definitions.POSITION_WIDTH)
            layout_grid.addWidget( moduleName, count, 2 )
            #
            # device name
            #
            devName = QtGui.QLabel()
            devName.setText( "%s/%s" % (dev['hostname'], dev['device']))
            devName.setAlignment( QtCore.Qt.AlignLeft)
            layout_grid.addWidget( devName, count, 3 )
            
            count += 1

        self.base.setLayout( layout_grid)
        self.scrollArea.setWidget( self.base)
        self.refreshFunc = self.refreshIORegs

    def fillAdcDacs( self):

        if self.base is not None:
            self.base.destroy( True, True)

        self.base = QtGui.QWidget()
        layout_grid = QtGui.QGridLayout()

        layout_grid.addWidget( QtGui.QLabel( "Alias"), 0, 0)
        layout_grid.addWidget( QtGui.QLabel( "Value"), 0, 1)
        layout_grid.addWidget( QtGui.QLabel( "Module"), 0, 2)
        layout_grid.addWidget( QtGui.QLabel( "DeviceName"), 0, 3)

        #
        # <device>
        # <name>d1_ireg01</name>
        # <type>input_register</type>
        # <module>sis3610</module>
        # <device>p09/register/d1.in01</device>
        # <control>tango</control>
        # <hostname>haso107d1:10000</hostname>
        # <channel>1</channel>
        # </device>
        #
        count = 1
        for dev in allAdcs:
            aliasName = utils.QPushButtonTK( dev['name'])
            aliasName.setToolTip( "MB-1: Attributes\nMB-2: Commands\nMB-3: Properties")
            aliasName.mb1.connect( self.make_cb_attributes( dev, self.logWidget))
            aliasName.mb2.connect( self.make_cb_commands( dev, self.logWidget))
            aliasName.mb3.connect( self.make_cb_properties( dev, self.logWidget)) 
            layout_grid.addWidget( aliasName, count, 0)

            dev[ 'w_value'] = QtGui.QLabel( "0")
            dev[ 'w_value'].setFixedWidth( definitions.POSITION_WIDTH)
            dev[ 'w_value'].setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
            layout_grid.addWidget( dev[ 'w_value'], count, 1)

            moduleName = QtGui.QLabel()
            moduleName.setText( "%s" % (dev['module']))
            moduleName.setAlignment( QtCore.Qt.AlignLeft)
            moduleName.setFixedWidth( definitions.POSITION_WIDTH)
            layout_grid.addWidget( moduleName, count, 2 )
            #
            # device name
            #
            devName = QtGui.QLabel()
            devName.setText( "%s/%s" % (dev['hostname'], dev['device']))
            devName.setAlignment( QtCore.Qt.AlignLeft)
            layout_grid.addWidget( devName, count, 3 )
            
            count += 1

        for dev in allDacs:
            aliasName = utils.QPushButtonTK( dev['name'])
            aliasName.setToolTip( "MB-1: Attributes\nMB-2: Commands\nMB-3: Properties")
            aliasName.mb1.connect( self.make_cb_attributes( dev, self.logWidget))
            aliasName.mb2.connect( self.make_cb_commands( dev, self.logWidget))
            aliasName.mb3.connect( self.make_cb_properties( dev, self.logWidget)) 
            layout_grid.addWidget( aliasName, count, 0)

            dev[ 'w_value'] = utils.QPushButtonTK( dev['name'])
            dev[ 'w_value'].setToolTip( "MB-2: change voltage")
            dev[ 'w_value'].mb1.connect( self.make_cb_dac( dev, self.logWidget))
            layout_grid.addWidget( dev[ 'w_value'], count, 1)

            moduleName = QtGui.QLabel()
            moduleName.setText( "%s" % (dev['module']))
            moduleName.setAlignment( QtCore.Qt.AlignLeft)
            moduleName.setFixedWidth( definitions.POSITION_WIDTH)
            layout_grid.addWidget( moduleName, count, 2 )
            #
            # device name
            #
            devName = QtGui.QLabel()
            devName.setText( "%s/%s" % (dev['hostname'], dev['device']))
            devName.setAlignment( QtCore.Qt.AlignLeft)
            layout_grid.addWidget( devName, count, 3 )
            
            count += 1

        self.base.setLayout( layout_grid)
        self.scrollArea.setWidget( self.base)
        self.refreshFunc = self.refreshAdcDacs

    def fillCameras( self):

        if self.base is not None:
            self.base.destroy( True, True)

        self.base = QtGui.QWidget()
        layout_grid = QtGui.QGridLayout()

        layout_grid.addWidget( QtGui.QLabel( "Alias"), 0, 0)
        layout_grid.addWidget( QtGui.QLabel( "Value"), 0, 1)
        layout_grid.addWidget( QtGui.QLabel( "Module"), 0, 2)
        layout_grid.addWidget( QtGui.QLabel( "DeviceName"), 0, 3)
        #
        # <device>
        # <name>lmbd</name>
        # <sardananame>lmbd</sardananame>
        # <type>DETECTOR</type>
        # <module>lambda</module>
        # <device>p23/lambda/01</device>
        # <control>tango</control>
        # <hostname>hasep23oh:10000</hostname>
        # </device>
        #
        count = 1
        for dev in allCameras:
            aliasName = utils.QPushButtonTK( dev['name'])
            aliasName.setToolTip( "MB-1: Attributes\nMB-2: Commands\nMB-3: Properties")
            aliasName.mb1.connect( self.make_cb_attributes( dev, self.logWidget))
            aliasName.mb2.connect( self.make_cb_commands( dev, self.logWidget))
            aliasName.mb3.connect( self.make_cb_properties( dev, self.logWidget)) 
            layout_grid.addWidget( aliasName, count, 0)

            moduleName = QtGui.QLabel()
            moduleName.setText( "%s" % (dev['module']))
            moduleName.setAlignment( QtCore.Qt.AlignLeft)
            moduleName.setFixedWidth( definitions.POSITION_WIDTH)
            layout_grid.addWidget( moduleName, count, 1 )
            #
            # device name
            #
            devName = QtGui.QLabel()
            devName.setText( "%s/%s" % (dev['hostname'], dev['device']))
            devName.setAlignment( QtCore.Qt.AlignLeft)
            layout_grid.addWidget( devName, count, 2 )
            
            count += 1

        self.base.setLayout( layout_grid)
        self.scrollArea.setWidget( self.base)
        self.refreshFunc = self.refreshCameras

    def fillPiLCModules( self):

        if self.base is not None:
            self.base.destroy( True, True)

        self.base = QtGui.QWidget()
        layout_grid = QtGui.QGridLayout()

        layout_grid.addWidget( QtGui.QLabel( "Alias"), 0, 0)
        layout_grid.addWidget( QtGui.QLabel( "Value"), 0, 1)
        layout_grid.addWidget( QtGui.QLabel( "Module"), 0, 2)
        layout_grid.addWidget( QtGui.QLabel( "DeviceName"), 0, 3)
        #
        # <device>
        # <name>lmbd</name>
        # <sardananame>lmbd</sardananame>
        # <type>DETECTOR</type>
        # <module>lambda</module>
        # <device>p23/lambda/01</device>
        # <control>tango</control>
        # <hostname>hasep23oh:10000</hostname>
        # </device>
        #
        count = 1
        for dev in allPiLCModules:
            aliasName = utils.QPushButtonTK( dev['name'])
            aliasName.setToolTip( "MB-1: Attributes\nMB-2: Commands\nMB-3: Properties")
            aliasName.mb1.connect( self.make_cb_attributes( dev, self.logWidget))
            aliasName.mb2.connect( self.make_cb_commands( dev, self.logWidget))
            aliasName.mb3.connect( self.make_cb_properties( dev, self.logWidget)) 
            layout_grid.addWidget( aliasName, count, 0)

            moduleName = QtGui.QLabel()
            moduleName.setText( "%s" % (dev['module']))
            moduleName.setAlignment( QtCore.Qt.AlignLeft)
            moduleName.setFixedWidth( definitions.POSITION_WIDTH)
            layout_grid.addWidget( moduleName, count, 1 )
            #
            # device name
            #
            devName = QtGui.QLabel()
            devName.setText( "%s/%s" % (dev['hostname'], dev['device']))
            devName.setAlignment( QtCore.Qt.AlignLeft)
            layout_grid.addWidget( devName, count, 2 )
            
            count += 1

        self.base.setLayout( layout_grid)
        self.scrollArea.setWidget( self.base)
        self.refreshFunc = self.refreshPiLCModules

    def fillModuleTangos( self):

        if self.base is not None:
            self.base.destroy( True, True)

        self.base = QtGui.QWidget()
        layout_grid = QtGui.QGridLayout()

        layout_grid.addWidget( QtGui.QLabel( "Alias"), 0, 0)
        layout_grid.addWidget( QtGui.QLabel( "Value"), 0, 1)
        layout_grid.addWidget( QtGui.QLabel( "Module"), 0, 2)
        layout_grid.addWidget( QtGui.QLabel( "DeviceName"), 0, 3)
        count = 1
        for dev in allModuleTangos:
            aliasName = utils.QPushButtonTK( dev['name'])
            aliasName.setToolTip( "MB-1: Attributes\nMB-2: Commands\nMB-3: Properties")
            aliasName.mb1.connect( self.make_cb_attributes( dev, self.logWidget))
            aliasName.mb2.connect( self.make_cb_commands( dev, self.logWidget))
            aliasName.mb3.connect( self.make_cb_properties( dev, self.logWidget)) 
            layout_grid.addWidget( aliasName, count, 0)

            moduleName = QtGui.QLabel()
            moduleName.setText( "%s" % (dev['module']))
            moduleName.setAlignment( QtCore.Qt.AlignLeft)
            moduleName.setFixedWidth( definitions.POSITION_WIDTH)
            layout_grid.addWidget( moduleName, count, 1 )
            #
            # device name
            #
            devName = QtGui.QLabel()
            devName.setText( "%s/%s" % (dev['hostname'], dev['device']))
            devName.setAlignment( QtCore.Qt.AlignLeft)
            layout_grid.addWidget( devName, count, 2 )
            
            count += 1

        self.base.setLayout( layout_grid)
        self.scrollArea.setWidget( self.base)
        self.refreshFunc = self.refreshModuleTangos

    def fillMCAs( self):

        if self.base is not None:
            self.base.destroy( True, True)

        self.base = QtGui.QWidget()
        layout_grid = QtGui.QGridLayout()

        layout_grid.addWidget( QtGui.QLabel( "Alias"), 0, 0)
        layout_grid.addWidget( QtGui.QLabel( "Module"), 0, 1)
        layout_grid.addWidget( QtGui.QLabel( "DeviceName"), 0, 2)

        #
        # <device>
        # <name>d1_mca01</name>
        # <type>mca</type>
        # <module>mca_8701</module>
        # <device>p09/mca/d1.01</device>
        # <control>tango</control>
        # <hostname>haso107d1:10000</hostname>
        # <channel>1</channel>
        # </device>
        #
        count = 1
        for dev in allMCAs:
            if dev[ 'module'].lower() == 'mca_8701':
                aliasName = utils.QPushButtonTK( dev['name'])
                aliasName.setToolTip( "MB-1: Attributes\nMB-2: Commands\nMB-3: Properties")
                aliasName.mb1.connect( self.make_cb_attributes( dev, self.logWidget))
                aliasName.mb2.connect( self.make_cb_commands( dev, self.logWidget))
                aliasName.mb3.connect( self.make_cb_properties( dev, self.logWidget)) 
                layout_grid.addWidget( aliasName, count, 0)

            moduleName = QtGui.QLabel()
            moduleName.setText( "%s" % (dev['module']))
            moduleName.setAlignment( QtCore.Qt.AlignLeft)
            moduleName.setFixedWidth( definitions.POSITION_WIDTH)
            layout_grid.addWidget( moduleName, count, 1 )
            #
            # device name
            #
            devName = QtGui.QLabel()
            devName.setText( "%s/%s" % (dev['hostname'], dev['device']))
            devName.setAlignment( QtCore.Qt.AlignLeft)
            layout_grid.addWidget( devName, count, 2 )
            
            count += 1

        self.base.setLayout( layout_grid)
        self.scrollArea.setWidget( self.base)
        self.refreshFunc = self.refreshMCAs

    def fillVfcAdcs( self):

        if self.base is not None:
            self.base.destroy( True, True)

        self.base = QtGui.QWidget()
        layout_grid = QtGui.QGridLayout()

        count = 0
        layout_grid.addWidget( QtGui.QLabel( "Alias"), count, 0)
        layout_grid.addWidget( QtGui.QLabel( "Counts"), count, 1)
        layout_grid.addWidget( QtGui.QLabel( "Reset"), count, 2)
        layout_grid.addWidget( QtGui.QLabel( "Module"), count, 4)
        layout_grid.addWidget( QtGui.QLabel( "DeviceName"), count, 5)
        count += 1

        for dev in allVfcAdcs:
            dev[ 'w_aliasName'] = utils.QPushButtonTK( dev['name'])
            dev[ 'w_aliasName'].setToolTip( "MB-1: Attributes\nMB-2: Commands\nMB-3: Properties")
            dev[ 'w_aliasName'].mb1.connect( self.make_cb_attributes( dev, self.logWidget))
            dev[ 'w_aliasName'].mb2.connect( self.make_cb_commands( dev, self.logWidget))
            dev[ 'w_aliasName'].mb3.connect( self.make_cb_properties( dev, self.logWidget))
            
            layout_grid.addWidget( dev[ 'w_aliasName'], count, 0)

            dev[ 'w_counts'] = QtGui.QLabel()
            dev[ 'w_counts'].setFixedWidth( definitions.POSITION_WIDTH)
            layout_grid.addWidget( dev[ 'w_counts'], count, 1)

            dev[ 'w_reset'] = utils.QPushButtonTK( 'Reset')
            dev[ 'w_reset'].setToolTip( "MB-1: reset counter")
            dev[ 'w_reset'].mb1.connect( self.make_cb_resetCounter( dev, self.logWidget))
            layout_grid.addWidget( dev[ 'w_reset'], count, 2)

            moduleName = QtGui.QLabel()
            moduleName.setText( "%s" % (dev['module']))
            moduleName.setAlignment( QtCore.Qt.AlignLeft)
            moduleName.setFixedWidth( definitions.POSITION_WIDTH)
            layout_grid.addWidget( moduleName, count, 4 )
            #
            # device name
            #
            devName = QtGui.QLabel()
            devName.setText( "%s/%s" % (dev['hostname'], dev['device']))
            devName.setAlignment( QtCore.Qt.AlignLeft)
            layout_grid.addWidget( devName, count, 5 )
            
            count += 1

        self.base.setLayout( layout_grid)
        self.scrollArea.setWidget( self.base)
        self.refreshFunc = self.refreshVfcAdcs

    def fillCounters( self):

        if self.base is not None:
            self.base.destroy( True, True)

        self.base = QtGui.QWidget()
        layout_grid = QtGui.QGridLayout()

        count = 0
        layout_grid.addWidget( QtGui.QLabel( "Alias"), count, 0)
        layout_grid.addWidget( QtGui.QLabel( "Counts"), count, 1)
        layout_grid.addWidget( QtGui.QLabel( "Reset"), count, 2)
        layout_grid.addWidget( QtGui.QLabel( "Module"), count, 4)
        layout_grid.addWidget( QtGui.QLabel( "DeviceName"), count, 5)
        count += 1

        for dev in allCounters + allTangoAttrCtrls + allTangoCounters:

            aliasName = utils.QPushButtonTK( dev['name'])
            aliasName.setToolTip( "MB-1: Attributes\nMB-2: Commands\nMB-3: Properties")
            aliasName.mb1.connect( self.make_cb_attributes( dev, self.logWidget))
            aliasName.mb2.connect( self.make_cb_commands( dev, self.logWidget))
            aliasName.mb3.connect( self.make_cb_properties( dev, self.logWidget)) 
            layout_grid.addWidget( aliasName, count, 0)
            #
            #dev[ 'w_aliasName'] = QtGui.QLabel( dev['name'])
            #layout_grid.addWidget( dev[ 'w_aliasName'], count, 0)

            dev[ 'w_counts'] = QtGui.QLabel()
            dev[ 'w_counts'].setFixedWidth( definitions.POSITION_WIDTH)
            layout_grid.addWidget( dev[ 'w_counts'], count, 1)

            dev[ 'w_reset'] = utils.QPushButtonTK( 'Reset')
            dev[ 'w_reset'].setToolTip( "MB-1: reset counter")
            dev[ 'w_reset'].mb1.connect( self.make_cb_resetCounter( dev, self.logWidget))
            layout_grid.addWidget( dev[ 'w_reset'], count, 2)

            moduleName = QtGui.QLabel()
            moduleName.setText( "%s" % (dev['module']))
            moduleName.setAlignment( QtCore.Qt.AlignLeft)
            moduleName.setFixedWidth( definitions.POSITION_WIDTH)
            layout_grid.addWidget( moduleName, count, 4 )
            #
            # device name
            #
            devName = QtGui.QLabel()
            devName.setText( "%s/%s" % (dev['hostname'], dev['device']))
            devName.setAlignment( QtCore.Qt.AlignLeft)
            layout_grid.addWidget( devName, count, 5 )
            
            count += 1

        self.base.setLayout( layout_grid)
        self.scrollArea.setWidget( self.base)
        self.refreshFunc = self.refreshCounters
        
    def cb_refreshMain( self):

        if self.isMinimized(): 
            return
        
        self.activityIndex += 1
        if self.activityIndex > (len( definitions.ACTIVITY_SYMBOLS) - 1):
            self.activityIndex = 0
        self.activity.setTitle( definitions.ACTIVITY_SYMBOLS[ self.activityIndex])
        self.updateTimer.stop()

        self.refreshFunc()
        #self.refreshMotors()
        #self.refreshIORegs()

        self.updateTimer.start( definitions.TIMEOUT_REFRESH)

    def refreshMotors( self):
        hndlr = signal.getsignal( signal.SIGALRM)
        signal.signal( signal.SIGALRM, self.handlerALRM)
        #
        # for the old OmsVme58 cards, 1s is not enough
        #
        signal.alarm( 2)
        self.updateCount += 1
        try:
            for dev in selectedMotors:
                if dev[ 'flagOffline']:
                    continue
                if dev[ 'w_pos'].visibleRegion().isEmpty():
                    continue
                #
                # see, if state() responds. If not ignore the motor
                #
                try:
                    sts = dev[ 'proxy'].state()
                except Exception, e:
                    dev[ 'w_pos'].setText( "None")
                    dev[ 'w_unitlimitmin'].setText( "None")
                    dev[ 'w_unitlimitmax'].setText( "None")
                    continue
                
                # handle the position
                #
                dev[ 'w_pos'].setText( utils.getPositionString( dev))
                if dev[ 'proxy'].state() == PyTango.DevState.MOVING:
                    dev[ 'w_pos'].setStyleSheet( "background-color:%s;" % definitions.BLUE_MOVING)
                elif dev[ 'proxy'].state() == PyTango.DevState.ON:
                    dev[ 'w_pos'].setStyleSheet( "background-color:%s;" % definitions.GREY_NORMAL)
                elif dev[ 'proxy'].state() == PyTango.DevState.DISABLE:
                    dev[ 'w_pos'].setStyleSheet( "background-color:%s;" % definitions.MAGENTA_DISABLE)
                else:
                    dev[ 'w_pos'].setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)

                if (self.updateCount % 10) != 0:
                    continue
                #
                # and the limit widgets
                #
                dev[ 'w_unitlimitmin'].setText( utils.getUnitLimitMinString( dev, self.logWidget))
                if utils.getLowerLimit( dev, self):
                    dev[ 'w_unitlimitmin'].setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
                else:
                    dev[ 'w_unitlimitmin'].setStyleSheet( "background-color:%s;" % definitions.GREY_NORMAL)
                dev[ 'w_unitlimitmax'].setText( utils.getUnitLimitMaxString( dev, self.logWidget))
                if utils.getUpperLimit( dev, self):
                    dev[ 'w_unitlimitmax'].setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
                else:
                    dev[ 'w_unitlimitmax'].setStyleSheet( "background-color:%s;" % definitions.GREY_NORMAL)
        except utils.TMO, e:
            self.logWidget.append( "main.cb_refresh: expired, dev %s, ignoring" % dev[ 'name'])
            dev[ 'flagOffline'] = True
            self.updateTimer.start( definitions.TIMEOUT_REFRESH)
            return

        signal.alarm(0)

    def refreshIORegs( self):
        hndlr = signal.getsignal( signal.SIGALRM)
        signal.signal( signal.SIGALRM, self.handlerALRM)
        signal.alarm( 1)
        startTime = time.time()
        self.updateCount += 1
        try:
            for dev in allIRegs + allORegs:
                if dev[ 'flagOffline']:
                    continue
                if dev[ 'w_value'].visibleRegion().isEmpty():
                    continue
                #
                # see, if state() responds. If not ignore the motor
                #
                try:
                    sts = dev[ 'proxy'].state()
                except Exception, e:
                    dev[ 'w_value'].setText( "None")
                    continue
                
                # handle the position
                #
                dev[ 'w_value'].setText( "%d" % dev ['proxy'].Value)

        except utils.TMO, e:
            self.logWidget.append( "main.cb_refresh: expired, dev %s, ignoring" % dev[ 'name'])
            dev[ 'flagOffline'] = True
            self.updateTimer.start( definitions.TIMEOUT_REFRESH)
            return
        # 
        #self.logWidget.append( "time-diff %g" % ( time.time() - startTime))
        signal.alarm(0)

    def refreshVfcAdcs( self):

        hndlr = signal.getsignal( signal.SIGALRM)
        signal.signal( signal.SIGALRM, self.handlerALRM)
        signal.alarm( 1)
        startTime = time.time()
        self.updateCount += 1
        try:
            for dev in allVfcAdcs:
                if dev[ 'flagOffline']:
                    continue
                if dev[ 'w_counts'].visibleRegion().isEmpty():
                    continue
                #
                # see, if state() responds. If not ignore the motor
                #
                try:
                    sts = dev[ 'proxy'].state()
                except Exception, e:
                    dev[ 'w_counts'].setText( "None")
                    continue
                try:
                    dev[ 'w_counts'].setText( utils.getCounterValueStr( dev))
                except Exception, e:
                    dev[ 'w_counts'].setText( "None")
                    print "refreshTimerCounters: trouble reading Value of %s" % dev[ 'name']
                    

        except utils.TMO, e:
            self.logWidget.append( "main.cb_refresh: expired, dev %s, ignoring" % dev[ 'name'])
            dev[ 'flagOffline'] = True
            self.updateTimer.start( definitions.TIMEOUT_REFRESH)
            return
        # 
        #self.logWidget.append( "time-diff %g" % ( time.time() - startTime))
        signal.alarm(0)

    def refreshCounters( self):

        hndlr = signal.getsignal( signal.SIGALRM)
        signal.signal( signal.SIGALRM, self.handlerALRM)
        signal.alarm( 1)
        startTime = time.time()
        self.updateCount += 1
        try:
            for dev in allCounters + allTangoAttrCtrls + allTangoCounters:
                if dev[ 'flagOffline']:
                    continue
                if dev[ 'w_counts'].visibleRegion().isEmpty():
                    continue
                #
                # see, if state() responds. If not ignore the motor
                #
                try:
                    sts = dev[ 'proxy'].state()
                except Exception, e:
                    dev[ 'w_counts'].setText( "None")
                    continue
                try:
                    dev[ 'w_counts'].setText( utils.getCounterValueStr( dev))
                except Exception, e:
                    dev[ 'w_counts'].setText( "None")
                    print "refreshTimerCounters: trouble reading Value of %s" % dev[ 'name']
                    

        except utils.TMO, e:
            self.logWidget.append( "main.cb_refresh: expired, dev %s, ignoring" % dev[ 'name'])
            dev[ 'flagOffline'] = True
            self.updateTimer.start( definitions.TIMEOUT_REFRESH)
            return
        # 
        #self.logWidget.append( "time-diff %g" % ( time.time() - startTime))
        signal.alarm(0)

    def refreshAdcDacs( self):
        hndlr = signal.getsignal( signal.SIGALRM)
        signal.signal( signal.SIGALRM, self.handlerALRM)
        signal.alarm( 1)
        startTime = time.time()
        self.updateCount += 1
        try:
            for dev in allAdcs + allDacs:
                if dev[ 'flagOffline']:
                    continue
                if dev[ 'w_value'].visibleRegion().isEmpty():
                    continue
                #
                # see, if state() responds. If not ignore the motor
                #
                try:
                    sts = dev[ 'proxy'].state()
                except Exception, e:
                    dev[ 'w_value'].setText( "None")
                    continue
                #
                # handle the value
                #
                dev[ 'w_value'].setText( "%g" % utils.getDacValue( dev))

        except utils.TMO, e:
            self.logWidget.append( "main.cb_refresh: expired, dev %s, ignoring" % dev[ 'name'])
            dev[ 'flagOffline'] = True
            self.updateTimer.start( definitions.TIMEOUT_REFRESH)
            return
        # 
        #self.logWidget.append( "time-diff %g" % ( time.time() - startTime))
        signal.alarm(0)

    def refreshCameras( self):
        pass

    def refreshPiLCModules( self):
        pass

    def refreshModuleTangos( self):
        pass

    def refreshMCAs( self):
        pass

    def handlerALRM( signum, frame, arg3):
        #print "handlerALRM: called with signal", signum
        raise utils.TMO( "tmo-excepttion")

    def make_cb_resetCounter( self, dev, logWidget):
        def cb():
            try:
                sts = dev[ 'proxy'].state()
            except Exception, e:
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "make_cb_oreg: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return

            try:
                dev[ 'proxy'].reset()
            except Exception, e:
                print "Trouble to reset %s" % dev[ 'name']
                print repr( e)

        return cb

    def make_cb_setSampleTime( self, dev, logWidget):
        def cb():
            try:
                sts = dev[ 'proxy'].state()
            except Exception, e:
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
            except Exception, e:
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

    def make_cb_oreg( self, dev, logWidget):
        def cb():
            try:
                sts = dev[ 'proxy'].state()
            except Exception, e:
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "make_cb_oreg: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return

            value = dev[ 'proxy'].Value
            if value == 0:
                dev[ 'proxy'].Value = 1
            else:
                dev[ 'proxy'].Value = 0
        return cb

    def make_cb_dac( self, dev, logWidget):
        def cb():
            try:
                sts = dev[ 'proxy'].state()
            except Exception, e:
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "make_cb_oreg: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return

            oldValue = utils.getDacValue( dev)
            value, ok = QtGui.QInputDialog.getText(self, "Enter a value", "New value for %s:" % dev[ 'name'],
                                                   QtGui.QLineEdit.Normal, "%g" % oldValue)
            if ok:
                utils.setDacValue( dev, float(value))

        return cb

    def make_cb_move( self, dev, logWidget):
        def cb():
            if hasattr( self, "w_moveMotor"):
                self.w_moveMotor.cb_closeMoveMotor()
                del self.w_moveMotor
                
            try:
                sts = dev[ 'proxy'].state()
            except Exception, e:
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "cb_move: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return

            self.w_moveMotor = moveMotor.moveMotor( dev, self.timerName, self.counterName, logWidget, allDevices, self)
            self.w_moveMotor.show()
        return cb

    def make_cb_attributes( self, dev, logWidget):
        def cb():
            try:
                sts = dev[ 'proxy'].state()
            except Exception, e:
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "cb_attributes: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return 
                
            # 
            # remove 'self.' to allow for one widget only
            # 
            self.w_attr = tngAPI.deviceAttributes( dev, logWidget, self)
            self.w_attr.show()
        return cb

    def make_cb_commands( self, dev, logWidget):
        def cb():
            try:
                sts = dev[ 'proxy'].state()
            except Exception, e:
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "cb_commands: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return 
                
            # 
            # remove 'self.' to allow for one widget only
            # 
            self.w_commands = tngAPI.deviceCommands( dev, logWidget, self)
            self.w_commands.show()
        return cb

    def make_cb_properties( self, dev, logWidget):
        def cb():
            #
            # replace self.w_prop with w_prop to allow for one 
            # properties widget only
            #
            self.w_prop = tngAPI.deviceProperties( dev, self.logWidget, self)
            self.w_prop.show()
        return cb

    def make_cb_mb3( self, dev, logWidget):
        def cb():
            lst = HasyUtils.getDeviceProperty( dev['device'], "FlagEncoder", dev[ 'hostname'])
            if len(lst) == 0 or lst[0] != "1":
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "EncoderAttribute widget not available for %s, FlagEncoder != 1" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return

            try:
                sts = dev[ 'proxy'].state()
            except Exception, e:
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "cb_mb3: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return 
                
            self.w_encAttr = motorEncAttributes( dev, logWidget, self)
            self.w_encAttr.show()
        return cb

class MacroServerIfc( QtGui.QMainWindow):
    def __init__( self, logWidget = None, parent = None):
        super( MacroServerIfc, self).__init__( parent)
        self.parent = parent
        self.setWindowTitle( "Selected MacroServer Variables")
        self.logWidget = logWidget
        self.prepareWidgets()
        #
        # Menu Bar
        #
        self.menuBar = QtGui.QMenuBar()
        self.setMenuBar( self.menuBar)
        self.prepareMenuBar()
        self.prepareStatusBar()

        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect( self.cb_refreshMacroServerIfc)
        self.updateTimer.start( definitions.TIMEOUT_REFRESH)

    def prepareMenuBar( self):
        self.fileMenu = self.menuBar.addMenu('&File')
        self.exitAction = QtGui.QAction('E&xit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(QtGui.QApplication.quit)
        self.fileMenu.addAction( self.exitAction)

        #
        # the activity menubar: help and activity
        #
        self.menuBarActivity = QtGui.QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarActivity, QtCore.Qt.TopRightCorner)

        #
        # Help menu (bottom part)
        #
        self.helpMenu = self.menuBarActivity.addMenu('Help')
        self.widgetAction = self.helpMenu.addAction(self.tr("Widget"))
        self.widgetAction.triggered.connect( self.cb_helpWidget)

        self.activityIndex = 0
        self.activity = self.menuBarActivity.addMenu( "_")

    def cb_helpWidget(self):
        w = helpBox.HelpBox(self, self.tr("HelpWidget"), self.tr(
            "\
<p><b>ScanFile</b><br>\
Use e.g. [\"tst.fio\", \"tst.nxs\"] to specify that two ouput \
files will be created, a NeXus and a .fio file\
\
<p><b>Hooks</b><br>\
Find explanations in the Spock manual, Scans chapter.\
\
<p><b>JsonRecorder</b><br>\
The SardanaMonitor receives json-encoded data. Therefore the JsonRecoder checkbox should be enabled.\
\
<p><b>Logging</b><br>\
LogMacroOnOff: if True, logging is active<br>\
LogMacroPath: directory where the log will be stored<br>\
LogMacroAll: if 0, only the macros called from spock will be written, \
if 1 also the macros called by macros<br>\
LogMacroMode: if False, logging is appended in existing file, if True \
current file is copied to a backup file and a new one is created.\
\
"
                ))
        w.show()

    def prepareStatusBar( self):
        #
        # Status Bar
        #
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar( self.statusBar)

        self.abortMacro = QtGui.QPushButton(self.tr("Abort Macro")) 
        self.statusBar.addWidget( self.abortMacro) 
        self.abortMacro.clicked.connect( self.cb_abortMacro)

        self.apply = QtGui.QPushButton(self.tr("&Apply")) 
        self.statusBar.addPermanentWidget( self.apply) # 'permanent' to shift it right
        self.apply.clicked.connect( self.cb_applyMacroServerIfc)
        self.apply.setShortcut( "Alt+a")

        self.exit = QtGui.QPushButton(self.tr("E&xit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        self.exit.clicked.connect( self.cb_closeMacroServerIfc )
        self.exit.setShortcut( "Alt+x")
        
    def prepareWidgets( self):
        w = QtGui.QWidget()
        self.layout_v = QtGui.QVBoxLayout()
        w.setLayout( self.layout_v)
        self.setCentralWidget( w)
        self.dct = {}
        #
        # the ActiveMntGrp
        #
        if HasyUtils.getMgAliases() is not None:
            hBox = QtGui.QHBoxLayout()
            w = QtGui.QLabel( "ActiveMntGrp")
            w.setMinimumWidth( 120)
            hBox.addWidget( w)
            hBox.addStretch()            
            self.activeMntGrpComboBox = QtGui.QComboBox()
            self.activeMntGrpComboBox.setMinimumWidth( 250)
            count = 0
            activeMntGrp = HasyUtils.getEnv( "ActiveMntGrp")
            for mg in HasyUtils.getMgAliases():
                self.activeMntGrpComboBox.addItem( mg)
                #
                # initialize the comboBox to the current ActiveMntGrp
                #
                if activeMntGrp == mg:
                    self.activeMntGrpComboBox.setCurrentIndex( count)
                count += 1
            #
            # connect the callback AFTER the combox is filled. Otherwise there
            # will be some useless changes
            #
            self.activeMntGrpComboBox.currentIndexChanged.connect( self.cb_activeMntGrpChanged)
            hBox.addWidget( self.activeMntGrpComboBox)
            self.layout_v.addLayout( hBox)
        #
        # horizontal line
        #
        hBox = QtGui.QHBoxLayout()
        w = QtGui.QFrame()
        w.setFrameShape( QtGui.QFrame.HLine)
        w.setFrameShadow(QtGui.QFrame.Sunken)
        hBox.addWidget( w)
        self.layout_v.addLayout( hBox)
        #
        # some Env variables
        #
        self.varsEnv = [ "ScanDir", "ScanFile", "FioAdditions"]
        for var in self.varsEnv:
            hBox = QtGui.QHBoxLayout()
            w = QtGui.QLabel( "%s:" % var)
            w.setMinimumWidth( 120)
            hBox.addWidget( w)
            hsh = {}
            w_value = QtGui.QLabel()
            w_value.setMinimumWidth( 250)
            w_value.setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
            hBox.addWidget( w_value)
            w_line = QtGui.QLineEdit()
            w_line.setAlignment( QtCore.Qt.AlignRight)
            w_line.setMinimumWidth( 250)
            hBox.addWidget( w_line)
            self.dct[ var] = { "w_value": w_value, "w_line": w_line}
            self.layout_v.addLayout( hBox)

        #
        # horizontal line
        #
        hBox = QtGui.QHBoxLayout()
        w = QtGui.QFrame()
        w.setFrameShape( QtGui.QFrame.HLine)
        w.setFrameShadow(QtGui.QFrame.Sunken)
        hBox.addWidget( w)
        self.layout_v.addLayout( hBox)
        #
        # JsonRecorder
        #
        hBox = QtGui.QHBoxLayout()
        self.w_jsonRecorderCheckBox = QtGui.QCheckBox()
        self.w_jsonRecorderCheckBox.setToolTip( "Enables SardanaMonitor")
        a = HasyUtils.getEnv( "JsonRecorder")
        if a is False:
            self.w_jsonRecorderCheckBox.setChecked( False)
        else:
            self.w_jsonRecorderCheckBox.setChecked( True)

        self.w_jsonRecorderCheckBox.stateChanged.connect( self.cb_jsonRecorder)
        hBox.addWidget( self.w_jsonRecorderCheckBox)
        l = QtGui.QLabel( "JsonRecorder")
        l.setMinimumWidth( 120)
        hBox.addWidget( l)
        hBox.addStretch()
        self.layout_v.addLayout( hBox)
        #
        # horizontal line
        #
        hBox = QtGui.QHBoxLayout()
        w = QtGui.QFrame()
        w.setFrameShape( QtGui.QFrame.HLine)
        w.setFrameShadow(QtGui.QFrame.Sunken)
        hBox.addWidget( w)
        self.layout_v.addLayout( hBox)
        #
        # ShowDial, ShowCtrlAxis
        #
        hsh = HasyUtils.getEnv( "_ViewOptions")
        hBox = QtGui.QHBoxLayout()
        self.w_showDialCheckBox = QtGui.QCheckBox()
        self.w_showDialCheckBox.setToolTip( "If True, 'Dial' with motor position (wa, wm)")
        if hsh[ 'ShowDial']:
            self.w_showDialCheckBox.setChecked( True)
        else:
            self.w_showDialCheckBox.setChecked( False)
        self.w_showDialCheckBox.stateChanged.connect( self.cb_showDial)
        hBox.addWidget( self.w_showDialCheckBox)
        l = QtGui.QLabel( "ShowDial")
        l.setMinimumWidth( 120)
        hBox.addWidget( l)

        self.w_showCtrlAxisCheckBox = QtGui.QCheckBox()
        self.w_showCtrlAxisCheckBox.setToolTip( "If True, show controller axis with motor position (wa, wm)")
        if hsh[ 'ShowCtrlAxis']:
            self.w_showCtrlAxisCheckBox.setChecked( True)
        else:
            self.w_showCtrlAxisCheckBox.setChecked( False)
        self.w_showCtrlAxisCheckBox.stateChanged.connect( self.cb_showCtrlAxis)
        hBox.addWidget( self.w_showCtrlAxisCheckBox)
        l = QtGui.QLabel( "ShowCtrlAxis")
        l.setMinimumWidth( 120)
        hBox.addWidget( l)
        hBox.addStretch()
        self.layout_v.addLayout( hBox)
        #
        # horizontal line
        #
        hBox = QtGui.QHBoxLayout()
        w = QtGui.QFrame()
        w.setFrameShape( QtGui.QFrame.HLine)
        w.setFrameShadow(QtGui.QFrame.Sunken)
        hBox.addWidget( w)
        self.layout_v.addLayout( hBox)
        #
        # general hooksm on-condition, on-stop
        #
        hBox = QtGui.QHBoxLayout()
        self.w_generalHooksCheckBox = QtGui.QCheckBox()
        hsh = HasyUtils.getEnv( "GeneralHooks")
        if hsh is None:
            self.w_generalHooksCheckBox.setChecked( False)
        else:
            self.w_generalHooksCheckBox.setChecked( True)

        self.w_generalHooksCheckBox.stateChanged.connect( self.cb_generalHooks)
        hBox.addWidget( self.w_generalHooksCheckBox)
        l = QtGui.QLabel( "General hooks")
        l.setMinimumWidth( 120)
        hBox.addWidget( l)
        #
        self.w_onConditionCheckBox = QtGui.QCheckBox()
        a = HasyUtils.getEnv( "GeneralCondition")
        if a is None:
            self.w_onConditionCheckBox.setChecked( False)
        else:
            self.w_onConditionCheckBox.setChecked( True)

        self.w_onConditionCheckBox.stateChanged.connect( self.cb_onCondition)
        hBox.addWidget( self.w_onConditionCheckBox)
        l = QtGui.QLabel( "On condition")
        l.setMinimumWidth( 120)
        hBox.addWidget( l)
        #
        self.w_generalStopCheckBox = QtGui.QCheckBox()
        a = HasyUtils.getEnv( "GeneralOnStopFunction")
        if a is None:
            self.w_generalStopCheckBox.setChecked( False)
        else:
            self.w_generalStopCheckBox.setChecked( True)

        self.w_generalStopCheckBox.stateChanged.connect( self.cb_generalStop)
        hBox.addWidget( self.w_generalStopCheckBox)
        l = QtGui.QLabel( "General stop")
        hBox.addWidget( l)
        l.setMinimumWidth( 120)
        hBox.addStretch()
        self.layout_v.addLayout( hBox)
        #
        # horizontal line
        #
        hBox = QtGui.QHBoxLayout()
        w = QtGui.QFrame()
        w.setFrameShape( QtGui.QFrame.HLine)
        w.setFrameShadow(QtGui.QFrame.Sunken)
        hBox.addWidget( w)
        self.layout_v.addLayout( hBox)
        #
        # logging
        #
        # LogMacroOnOff, LogMacroAll, LogMacroMode
        # 
        hBox = QtGui.QHBoxLayout()
        self.w_logMacroOnOffCheckBox = QtGui.QCheckBox()
        self.w_logMacroOnOffCheckBox.setToolTip( "If True, logging is active")
        a = HasyUtils.getEnv( "LogMacroOnOff")
        if a is False:
            self.w_logMacroOnOffCheckBox.setChecked( False)
        else:
            self.w_logMacroOnOffCheckBox.setChecked( True)

        self.w_logMacroOnOffCheckBox.stateChanged.connect( self.cb_logMacroOnOff)
        hBox.addWidget( self.w_logMacroOnOffCheckBox)
        l = QtGui.QLabel( "LogMacroOnOff")
        l.setMinimumWidth( 120)
        hBox.addWidget( l)
        #
        self.w_logMacroAllCheckBox = QtGui.QCheckBox()
        self.w_logMacroAllCheckBox.setToolTip( "If 0, only the macros called from spock will be written, if 1 also the macros called be macros")
        a = HasyUtils.getEnv( "LogMacroAll")
        if a is 0:
            self.w_logMacroAllCheckBox.setChecked( False)
        else:
            self.w_logMacroAllCheckBox.setChecked( True)

        self.w_logMacroAllCheckBox.stateChanged.connect( self.cb_logMacroAll)
        hBox.addWidget( self.w_logMacroAllCheckBox)
        l = QtGui.QLabel( "LogMacroAll")
        hBox.addWidget( l)
        l.setMinimumWidth( 120)
        # 
        self.w_logMacroModeCheckBox = QtGui.QCheckBox()
        self.w_logMacroModeCheckBox.setToolTip( "If False logging is appended in existing file, if True current file is copied to a backup file and a new one is created.")
        a = HasyUtils.getEnv( "LogMacroMode")
        if a is False:
            self.w_logMacroModeCheckBox.setChecked( False)
        else:
            self.w_logMacroModeCheckBox.setChecked( True)

        self.w_logMacroModeCheckBox.stateChanged.connect( self.cb_logMacroMode)
        hBox.addWidget( self.w_logMacroModeCheckBox)
        l = QtGui.QLabel( "LogMacroMode")
        hBox.addWidget( l)
        hBox.addStretch()
        self.layout_v.addLayout( hBox)

        self.varsEnv.append( "LogMacroPath")
        var = "LogMacroPath"
        hBox = QtGui.QHBoxLayout()
        w = QtGui.QLabel( "%s:" % var)
        w.setMinimumWidth( 120)
        hBox.addWidget( w)
        hsh = {}
        w_value = QtGui.QLabel()
        w_value.setMinimumWidth( 250)
        w_value.setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
        hBox.addWidget( w_value)
        w_line = QtGui.QLineEdit()
        w_line.setAlignment( QtCore.Qt.AlignRight)
        w_line.setMinimumWidth( 250)
        hBox.addWidget( w_line)
        self.dct[ var] = { "w_value": w_value, "w_line": w_line}
        self.layout_v.addLayout( hBox)

    def cb_refreshMacroServerIfc( self):

        if self.isMinimized(): 
            return

        self.activityIndex += 1
        if self.activityIndex > (len( definitions.ACTIVITY_SYMBOLS) - 1):
            self.activityIndex = 0
        self.activity.setTitle( definitions.ACTIVITY_SYMBOLS[ self.activityIndex])
        #
        # has the ActiveMntGrp been changed from outside?
        #
        if HasyUtils.getMgAliases() is not None:
            activeMntGrp = HasyUtils.getEnv( "ActiveMntGrp")
            temp = str(self.activeMntGrpComboBox.currentText())
            if temp != activeMntGrp:
                max = self.activeMntGrpComboBox.count()
                for count in range( 0, max):
                    temp1 = str( self.activeMntGrpComboBox.itemText( count))
                    if temp1 == activeMntGrp:
                        self.activeMntGrpComboBox.setCurrentIndex( count)
                    break
                else:
                    self.logWidget.append( "New ActiveMntGrp not on the list, restart widget")
        
        for var in self.varsEnv:
            res = HasyUtils.getEnv( var)
            if type( res) is list:
                res = ".".join(res)
            if res is None:
                self.dct[ var][ "w_value"].setText( "None")
            else:
                self.dct[ var][ "w_value"].setText( res)

        hsh = HasyUtils.getEnv( "_ViewOptions")
        if hsh[ 'ShowDial']:
            self.w_showDialCheckBox.setChecked( True)
        else:
            self.w_showDialCheckBox.setChecked( False)
        if hsh[ 'ShowCtrlAxis']:
            self.w_showCtrlAxisCheckBox.setChecked( True)
        else:
            self.w_showCtrlAxisCheckBox.setChecked( False)

        hsh = HasyUtils.getEnv( "GeneralHooks")
        if hsh is None:
            self.w_generalHooksCheckBox.setChecked( False)
        else:
            self.w_generalHooksCheckBox.setChecked( True)

        a = HasyUtils.getEnv( "GeneralCondition")
        if a is None:
            self.w_onConditionCheckBox.setChecked( False)
        else:
            self.w_onConditionCheckBox.setChecked( True)

        a = HasyUtils.getEnv( "GeneralOnStopFunction")
        if a is None:
            self.w_generalStopCheckBox.setChecked( False)
        else:
            self.w_generalStopCheckBox.setChecked( True)

        a = HasyUtils.getEnv( "JsonRecorder")
        if a is True:
            self.w_jsonRecorderCheckBox.setChecked( True)
        else:
            self.w_jsonRecorderCheckBox.setChecked( False)

        a = HasyUtils.getEnv( "LogMacroOnOff")
        if a is True:
            self.w_logMacroOnOffCheckBox.setChecked( True)
        else:
            self.w_logMacroOnOffCheckBox.setChecked( False)

        a = HasyUtils.getEnv( "LogMacroAll")
        if a is 1:
            self.w_logMacroAllCheckBox.setChecked( True)
        else:
            self.w_logMacroAllCheckBox.setChecked( False)

        a = HasyUtils.getEnv( "LogMacroMode")
        if a is True:
            self.w_logMacroModeCheckBox.setChecked( True)
        else:
            self.w_logMacroModeCheckBox.setChecked( False)

    def closeEvent( self, e):
        self.cb_closeMacroServerIfc()

    def cb_closeMacroServerIfc( self): 
        self.updateTimer.stop()
        self.close()
        
    def cb_jsonRecorder( self):
        if self.w_jsonRecorderCheckBox.isChecked():
            HasyUtils.setEnv( "JsonRecorder", True)
            a = HasyUtils.getEnv( "JsonRecorder")
            self.logWidget.append( "JsonRecorder: %s" % repr( a))
        else:
            HasyUtils.setEnv( "JsonRecorder", False)
            a = HasyUtils.getEnv( "JsonRecorder")
            self.logWidget.append( "JsonRecorder: %s" % repr(a))

    def cb_logMacroAll( self):
        if self.w_logMacroAllCheckBox.isChecked():
            HasyUtils.setEnv( "LogMacroAll", "1")
            a = HasyUtils.getEnv( "LogMacroAll")
            self.logWidget.append( "LogMacroAll: %s" % repr( a))
        else:
            HasyUtils.setEnv( "LogMacroAll", "0")
            self.logWidget.append( "LogMacroAll: disabled")

    def cb_logMacroOnOff( self):
        if self.w_logMacroOnOffCheckBox.isChecked():
            HasyUtils.setEnv( "LogMacroOnOff", True)
            a = HasyUtils.getEnv( "LogMacroOnOff")
            self.logWidget.append( "LogMacroOnOff: %s" % repr( a))
        else:
            HasyUtils.setEnv( "LogMacroOnOff", False)
            self.logWidget.append( "LogMacroOnOff: disabled")

    def cb_logMacroMode( self):
        if self.w_logMacroModeCheckBox.isChecked():
            HasyUtils.setEnv( "LogMacroMode", True)
            a = HasyUtils.getEnv( "LogMacroMode")
            self.logWidget.append( "LogMacroMode: %s" % repr( a))
        else:
            HasyUtils.setEnv( "LogMacroMode", False)
            self.logWidget.append( "LogMacroMode: disabled")

    def cb_generalStop( self):
        if self.w_generalStopCheckBox.isChecked():
            HasyUtils.runMacro( "gs_enable")
            a = HasyUtils.getEnv( "GeneralOnStopFunction")
            self.logWidget.append( "General on stop: %s" % repr( a))
        else:
            HasyUtils.runMacro( "gs_disable")
            self.logWidget.append( "General on stop: disabled")

    def cb_onCondition( self):
        if self.w_onConditionCheckBox.isChecked():
            HasyUtils.runMacro( "gc_enable")
            a = HasyUtils.getEnv( "GeneralCondition")
            self.logWidget.append( "General condition: %s" % repr( a))
        else:
            HasyUtils.runMacro( "gc_disable")
            self.logWidget.append( "General condition: disabled")

    def cb_generalHooks( self):

        if self.w_generalHooksCheckBox.isChecked():
            HasyUtils.runMacro( "gh_enable")
            hsh = HasyUtils.getEnv( "GeneralHooks")
            self.logWidget.append( "GeneralHooks: %s" % repr( hsh))
        else:
            HasyUtils.runMacro( "gh_disable")
            self.logWidget.append( "GeneralHooks: disabled")
        
    def cb_showDial( self):
        hsh = HasyUtils.getEnv( "_ViewOptions")
        if self.w_showDialCheckBox.isChecked():
            hsh[ 'ShowDial'] = True
        else:
            hsh[ 'ShowDial'] = False
        HasyUtils.setEnv( "_ViewOptions", hsh)

    def cb_showCtrlAxis( self):
        hsh = HasyUtils.getEnv( "_ViewOptions")
        if self.w_showCtrlAxisCheckBox.isChecked():
            hsh[ 'ShowCtrlAxis'] = True
        else:
            hsh[ 'ShowCtrlAxis'] = False
        HasyUtils.setEnv( "_ViewOptions", hsh)
        
        
    def cb_applyMacroServerIfc( self):

        for var in self.varsEnv:
            hsh = self.dct[ var]
            temp = str(hsh[ "w_line"].text())
            if len( temp) > 0:
                self.logWidget.append( "setting %s to %s" % (var, temp))
                HasyUtils.setEnv( var, temp)
                hsh[ 'w_value'].setText( temp)
                hsh[ "w_line"].clear()

    def cb_abortMacro( self): 
        try:
            door = PyTango.DeviceProxy( HasyUtils.getLocalDoorNames()[0])
        except Exception, e:
            self.logWidget.append( "cb_abortMacro: Failed to create proxy to Door" )
            self.logWidget.append( repr( e))
            return 

        door.abortmacro()
        self.logWidget.append( "Sent abortmacro() to door")
        return 
            
    def cb_activeMntGrpChanged( self):
        activeMntGrp = HasyUtils.getEnv( "ActiveMntGrp")
        temp = str(self.activeMntGrpComboBox.currentText())
        HasyUtils.setEnv( "ActiveMntGrp", temp)
        elements = HasyUtils.getMgElements( temp)
        self.logWidget.append( "ActiveMntGrp to %s: %s" % (temp, elements))
        
def parseCLI():
    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description="TngTool", 
        epilog='''\
Examples:
  TngTool.py 
    select all devices from online.xml
  TngTool.py -p 
        select all devices from online.xml and from pool, 
        e.g. diffractometer motors
  TngTool.py exp_mot01 exp_mot02
    selected motors from online.xml
  TngTool.py -tags expert
    select all devices tagged with expert
  TngTool.py exp_mot01
    launches the move menu for one motor

  The Python regular expression rules apply.
    ''')
    #
    # notice that 'pattern' is a positional argument
    #
    parser.add_argument('namePattern', nargs='*', help='a pattern to match the motor names')
    #parser.add_argument( '-c', dest='counterName', nargs='?', help='signal counter')
    #parser.add_argument( '-t', dest='timerName', nargs='?', help='signal timer')
    parser.add_argument( '-t', dest='tags', nargs='?', help='tags matching online.xml tags')
    #parser.add_argument('-l', dest="list", action="store_true", help='list server and devices')
    args = parser.parse_args()

    # 
    args.counterName = None
    args.timerName = None
    # 

    return args

def findAllMotors( args):
    global allMotors
    global allDevices
    #
    # read /online_dir/online.xml here because it is also elsewhere
    #
    #{'control': 'tango', 
    # 'name': 'd1_mot65', 
    # 'tags': 'user,expert',
    # 'hostname': 'haso107d1:10000', 
    # 'module': 'oms58', 
    # 'device': 'p09/motor/d1.65', 
    # 'type': 'stepping_motor', 
    # 'channel': '65'}
    #
    if not allDevices:
        allDevices = HasyUtils.getOnlineXML( cliTags = args.tags)
        
    #
    # find the motors and match the tags
    #
    allMotors = []
    if allDevices:
        for dev in allDevices:
            if dev.has_key( 'sardananame'):
                dev[ 'name'] = dev[ 'sardananame']

            if (dev['module'].lower() == 'motor_tango' or 
                dev['type'].lower() == 'stepping_motor' or
                dev['type'].lower() == 'dac'):
                #
                # try to create a proxy. If this is not possible, ignore the motor
                #
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    #print "findAllMotors: No proxy to %s, ignoring this device" % dev[ 'name']
                    continue
                dev[ 'flagPseudoMotor'] = False
                dev[ 'flagPoolMotor'] = False
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                allMotors.append( dev)
        
    #
    # there are PseudoMotors that do not appear in online.xml, 
    # e.g. the diffractometer motors. they should also be included
    #
    localPools = HasyUtils.getLocalPoolNames()
    if len( localPools) == 0:
        allMotors = sorted( allMotors, key=lambda k: k['name'])
        return 
        
    pool = PyTango.DeviceProxy( localPools[0])
    poolMotors = []
    for mot in pool.MotorList:
        poolDct = json.loads( mot)
        name = poolDct['name']
        #
        # devices that are in online.xml are not included via the pool
        #
        for dev in allDevices:
            if name == dev[ 'name']:
                break
        else:
            #print "name NOT in motorDict", name, "\n", repr( poolDct)
            #
            # source: haso107d1:10000/pm/e6cctrl/1/Position
            #
            dev = {}
            dev[ 'name'] = name
            dev[ 'type'] = 'type_tango'
            dev[ 'module'] = 'motor_pool'
            dev[ 'control'] = 'tango'
            #
            # source: haso107d1:10000/pm/e6cctrl/1/Position
            #         tango://haspe212oh.desy.de:10000/motor/dummy_mot_ctrl/1
            #
            src = poolDct[ 'source']
            if src.find( "tango://") == 0:
                src = src[ 8:]
            lst = src.split( '/')
            dev[ 'hostname'] = lst[0]
            
            dev[ 'device'] = "/".join( lst[1:-1])
            dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
            dev[ 'flagPoolMotor'] = True
            dev[ 'flagOffline'] = False # devices not responding are flagged offline
            if poolDct[ 'type'] == 'PseudoMotor':
                dev[ 'flagPseudoMotor'] = True
            else:
                dev[ 'flagPseudoMotor'] = False   # exp_dmy01, mu, chi

            dev[ 'proxy'] = createProxy( dev)
            if dev[ 'proxy'] is None:
                #print "findAllMotors: No proxy do %s, ignoring this device (2)" % dev[ 'name']
                continue
            poolMotors.append( dev)

    for dev in poolMotors: 
        allMotors.append( dev)

    allMotors = sorted( allMotors, key=lambda k: k['name'])

def findAllCounters( args):
    global allCounters, allTangoAttrCtrls, allTangoCounters
    global allDevices
    #
    # read /online_dir/online.xml here because it is also elsewhere
    #
    # <device>
    # <name>d1_c01</name>
    # <type>counter</type>
    # <module>sis3820</module>
    # <device>p09/counter/d1.01</device>
    # <control>tango</control>
    # <hostname>haso107d1:10000</hostname>
    # <channel>1</channel>
    # </device>
    #
    if not allDevices:
        allDevices = HasyUtils.getOnlineXML( cliTags = args.tags)
        
    allCounters = []
    if allDevices:
        for dev in allDevices:
            if dev.has_key( 'sardananame'):
                dev[ 'name'] = dev[ 'sardananame']
                
            if (dev['module'].lower() == 'tangoattributectctrl'):
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                allTangoAttrCtrls.append( dev)
            elif (dev['module'].lower() == 'tango_counter'):
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                allTangoCounters.append( dev)
            elif dev['module'].lower() in modulesRoiCounters:
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                allTangoCounters.append( dev)
            elif (dev['type'].lower() == 'counter'):
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                allCounters.append( dev)

    allCounters = sorted( allCounters, key=lambda k: k['name'])
    allTangoAttrCtrls = sorted( allTangoAttrCtrls, key=lambda k: k['name'])
    allTangoCounters = sorted( allTangoCounters, key=lambda k: k['name'])

def findAllTimers( args):
    global allTimers
    global allDevices
    #
    # read /online_dir/online.xml here because it is also elsewhere
    #
    # <device>
    # <name>d1_t01</name>
    # <type>timer</type>
    # <module>dgg2</module>
    # <device>p09/dgg2/d1.01</device>
    # <control>tango</control>
    # <hostname>haso107d1:10000</hostname>
    # <channel>1</channel>
    # </device>
    #
    if not allDevices:
        allDevices = HasyUtils.getOnlineXML( cliTags = args.tags)
        
    #
    # find the motors and match the tags
    #
    allTimers = []
    if allDevices:
        for dev in allDevices:
            if dev.has_key( 'sardananame'):
                dev[ 'name'] = dev[ 'sardananame']

            if (dev['type'].lower() == 'timer'):
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    print "findAllTimers: No proxy do %s, ignoring this device" % dev[ 'name']
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                allTimers.append( dev)
        
    allTimers = sorted( allTimers, key=lambda k: k['name'])

def findAllIORegs( args):
    global allIRegs, allORegs
    global allDevices
    #
    # read /online_dir/online.xml here because it is also elsewhere
    #
    #{'control': 'tango', 
    # 'name': 'd1_mot65', 
    # 'hostname': 'haso107d1:10000', 
    # 'module': 'oms58', 
    # 'device': 'p09/motor/d1.65', 
    # 'type': 'stepping_motor', 
    # 'channel': '65'}
    #
    if not allDevices:
        allDevices = HasyUtils.getOnlineXML( cliTags = args.tags)
        
    #
    # find the motors and match the tags
    #
    allIRegs = []
    allORegs = []
    if allDevices:
        for dev in allDevices:
            if dev.has_key( 'sardananame'):
                dev[ 'name'] = dev[ 'sardananame']

            if (dev['type'].lower() == 'input_register'):
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    print "findAllIORegs: No proxy do %s, ignoring this device" % dev[ 'name']
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                allIRegs.append( dev)

            if (dev['type'].lower() == 'output_register'):
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    print "findIORegs: No proxy do %s, ignoring this device" % dev[ 'name']
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                allORegs.append( dev)
        
    allIRegs = sorted( allIRegs, key=lambda k: k['name'])
    allORegs = sorted( allORegs, key=lambda k: k['name'])

def findAllAdcDacs( args):
    global allAdcs, allDacs, allVfcAdcs
    global allDevices
    #
    # read /online_dir/online.xml here because it is also elsewhere
    #
    # <device>
    # <name>d1_adc01</name>
    # <type>adc</type>
    # <module>tip850adc</module>
    # <device>p09/tip850adc/d1.01</device>
    # <control>tango</control>
    # <hostname>haso107d1:10000</hostname>
    # <channel>1</channel>
    # </device>
    if not allDevices:
        allDevices = HasyUtils.getOnlineXML( cliTags = args.tags)
    #
    # find the motors and match the tags
    #
    allAdcs = []
    allVfcAdcs = []
    allDacs = []
    if allDevices:
        for dev in allDevices:
            if dev.has_key( 'sardananame'):
                dev[ 'name'] = dev[ 'sardananame']

            if (dev['module'].lower() == 'tip830' or \
                dev['module'].lower() == 'tip850adc'):
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    print "findAllAdcDacs: No proxy do %s, ignoring this device" % dev[ 'name']
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                allAdcs.append( dev)

            if (dev['module'].lower() == 'vfcadc'):
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    print "findAllAdcDacs: No proxy do %s, ignoring this device" % dev[ 'name']
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                allVfcAdcs.append( dev)

            if (dev['module'].lower() == 'tip551' or \
                dev['module'].lower() == 'tip850dac'):
                dev[ 'proxy'] = createProxy( dev)
                if dev[ 'proxy'] is None:
                    print "findAdcDacs: No proxy do %s, ignoring this device" % dev[ 'name']
                    continue
                dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
                dev[ 'flagOffline'] = False # devices not responding are flagged offline
                allDacs.append( dev)
        
    allAdcs = sorted( allAdcs, key=lambda k: k['name'])
    allVfcAdcs = sorted( allVfcAdcs, key=lambda k: k['name'])
    allDacss = sorted( allDacs, key=lambda k: k['name'])

def findAllMCAs( args):
    global allMCAs
    global allDevices
    #
    # read /online_dir/online.xml here because it is also elsewhere
    #
    #
    # <device>
    # <name>d1_mca01</name>
    # <type>mca</type>
    # <module>mca_8701</module>
    # <device>p09/mca/d1.01</device>
    # <control>tango</control>
    # <hostname>haso107d1:10000</hostname>
    # <channel>1</channel>
    # </device>
    #

    if not allDevices:
        allDevices = HasyUtils.getOnlineXML( cliTags = args.tags)

    if not allDevices:
        return
    #
    # find the motors and match the tags
    #
    allMCAs = []
    for dev in allDevices:
        if dev.has_key( 'sardananame'):
            dev[ 'name'] = dev[ 'sardananame']

        if (dev['module'].lower() == 'mca_8701'):
            dev[ 'proxy'] = createProxy( dev)
            if dev[ 'proxy'] is None:
                print "findMCAs: No proxy do %s, ignoring this device" % dev[ 'name']
                continue
            dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
            dev[ 'flagOffline'] = False # devices not responding are flagged offline
            allMCAs.append( dev)
        
    allMCAs = sorted( allMCAs, key=lambda k: k['name'])

def findAllCameras( args):
    global allCameras
    global allDevices
    #
    # read /online_dir/online.xml here because it is also elsewhere
    #
    #
    # <device>
    # <name>lmbd</name>
    # <sardananame>lmbd</sardananame>
    # <type>DETECTOR</type>
    # <module>lambda</module>
    # <device>p23/lambda/01</device>
    # <control>tango</control>
    # <hostname>hasep23oh:10000</hostname>
    # </device>
    #

    if not allDevices:
        allDevices = HasyUtils.getOnlineXML( cliTags = args.tags)

    if not allDevices:
        return
    #
    # find the motors and match the tags
    #
    allCameras = []
    for dev in allDevices:
        if dev.has_key( 'sardananame'):
            dev[ 'name'] = dev[ 'sardananame']

        if dev['module'].lower() in cameraNames: 
            dev[ 'proxy'] = createProxy( dev)
            if dev[ 'proxy'] is None:
                print "findMCAs: No proxy do %s, ignoring this device" % dev[ 'name']
                continue
            dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
            dev[ 'flagOffline'] = False # devices not responding are flagged offline
            allCameras.append( dev)
        
    allCameras = sorted( allCameras, key=lambda k: k['name'])

def findAllPiLCModules( args):
    global allPiLCModules
    global allDevices

    if not allDevices:
        allDevices = HasyUtils.getOnlineXML( cliTags = args.tags)

    if not allDevices:
        return
    #
    # find the motors and match the tags
    #
    allPiLCModules = []
    for dev in allDevices:
        if dev.has_key( 'sardananame'):
            dev[ 'name'] = dev[ 'sardananame']

        if dev['module'].lower() in PiLCModuleNames: 
            dev[ 'proxy'] = createProxy( dev)
            if dev[ 'proxy'] is None:
                print "findMCAs: No proxy do %s, ignoring this device" % dev[ 'name']
                continue
            dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
            dev[ 'flagOffline'] = False # devices not responding are flagged offline
            allPiLCModules.append( dev)
        
    allPiLCModules = sorted( allPiLCModules, key=lambda k: k['name'])

def findAllModuleTangos( args):
    global allModuleTangos
    global allDevices

    if not allDevices:
        allDevices = HasyUtils.getOnlineXML( cliTags = args.tags)

    if not allDevices:
        return
    #
    # find the motors and match the tags
    #
    allModuleTangos = []
    for dev in allDevices:
        if dev.has_key( 'sardananame'):
            dev[ 'name'] = dev[ 'sardananame']

        if dev['module'].lower() == 'module_tango':
            dev[ 'proxy'] = createProxy( dev)
            if dev[ 'proxy'] is None:
                print "findModuleTangos: No proxy do %s, ignoring this device" % dev[ 'name']
                continue
            dev[ 'fullName'] = "%s/%s" % (dev[ 'hostname'], dev[ 'device'])
            dev[ 'flagOffline'] = False # devices not responding are flagged offline
            allModuleTangos.append( dev)
        
    allModuleTangos = sorted( allModuleTangos, key=lambda k: k['name'])

def createProxy( dev):

    try:
        #print "createProxy %s/%s, %s" % (dev[ 'hostname'], dev[ 'device'], dev[ 'name'])
        #
        #  <device>p08/sis3302/exp.01/1</device>
        #
        if (len( dev[ 'device'].split('/')) == 4 or 
            dev[ 'module'].lower() == 'tangoattributectctrl'):
            proxy = PyTango.DeviceProxy(  "%s" % (dev[ 'name']))
        else:
            proxy = PyTango.DeviceProxy(  "%s/%s" % (dev[ 'hostname'], dev[ 'device']))
        #
        # state() generates an exception, to see whether the server is actually running
        #
        startTime = time.time()
        sts = proxy.state() 
    except Exception, e:
        print "createProxy: no proxy to %s, flagging 'offline' " % dev[ 'name']
        dev[ 'flagOffline'] = True
        #for arg in e.args:
        #    if hasattr( arg, 'desc'):
        #        print " desc:   %s" % arg.desc
        #        print " origin: %s" % arg.origin
        #        print " reason: %s" % arg.reason
        #        print ""
        #    else:
        #        print repr( e)
        proxy = None

    return proxy

def main():
    global allDevices
    global selectedMotors
    #
    # open spectra here to avoid x-errors on image exit
    #
    Spectra.gra_command( "cls")

    args = parseCLI()
    sys.argv = []
    #app = TaurusApplication( sys.argv)
    #
    # if .setStyle() is not called, if TngTool is running
    # locally (not via ssh), the function app.style().metaObject().className()
    # returns QGtkStyle. If this string is supplied to .setStyle()
    # a segmentation fault is generated, locally and remotely.
    # so for remote running we use 'Ceanlooks' which is quite OK.
    #
    if os.getenv( "DISPLAY") != ':0':
        QtGui.QApplication.setStyle( 'Cleanlooks')

    app = QtGui.QApplication(sys.argv)
    #
    # the call afterwards, app.setStyle( 'CDE') (e.g.) has no effect at all
    #
    # [u'Windows', u'Motif', u'CDE', u'Plastique', u'GTK+', u'Cleanlooks']
    #print QtGui.QStyleFactory.keys()

    # print "style", app.style().metaObject().className()

    if args.tags and len( args.namePattern) > 0:
        print "TngTool: specify tags or names"
        return 0
        

    findAllMotors( args)
    findAllIORegs( args)
    findAllAdcDacs( args)
    findAllMCAs( args)
    findAllCameras( args)
    findAllPiLCModules( args)
    findAllModuleTangos( args)
    findAllTimers( args)
    findAllCounters( args)

    timerName = None
    counterName = None
    if args.counterName:
        counterName = args.counterName
    if args.timerName:
        timerName = args.timerName
    selectedMotors = []
    if args.namePattern:
        #
        # find selected motors
        #
        for dev in allMotors:
            for mot in args.namePattern:
                if HasyUtils.match( dev['name'], mot):
                    #
                    # remember this selection: m3y m3yaw m3_dmy05 m3_dmy06
                    #  m3y matches m3y AND m3yaw
                    # to make sure there are no doubles
                    #
                    for devTemp in selectedMotors:
                        if dev['name'] == devTemp[ 'name']:
                            break
                    else:
                        selectedMotors.append( dev)
        if len( selectedMotors) == 0:
            print "TngTool: no matching motors"
            return 0
        #
        # one motor specified: launch the moveMotor widget immediately
        #
        if len( selectedMotors) == 1:
            w = moveMotor.moveMotor( selectedMotors[0], timerName, counterName, None, allDevices, None)
            w.show()
        else:
            mainW = motorMenu(timerName, counterName)
            mainW.show()
    else:
        #
        # no pattern: all motors are selected
        #
        selectedMotors = allMotors
        if len( selectedMotors) == 0:
            print "TngTool: no motors found"
            return 0
        mainW = motorMenu(timerName, counterName)
        mainW.show()

    try:
        sys.exit( app.exec_())
    except Exception, e:
        print repr( e)

if __name__ == "__main__":
    main()
    
