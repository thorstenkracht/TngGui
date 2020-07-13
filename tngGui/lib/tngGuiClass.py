#!/usr/bin/env python

import math, time, os, signal, sys
import HasyUtils
#from taurus.external.qt import QtGui, QtCore 
from PyQt4 import QtCore, QtGui
import numpy as np
 
import tngGui.lib.helpBox as helpBox
import tngGui.lib.defineSignal as defineSignal 
import tngGui.lib.moveMotor as moveMotor
import tngGui.lib.tngAPI as tngAPI
import tngGui.lib.macroServerIfc as macroServerIfc
import tngGui.lib.mcaWidget as mcaWidget
import tngGui.lib.utils as utils
import PySpectra.graPyspIfc as graPyspIfc
import tngGui.lib.definitions as definitions
import tngGui.lib.devices as devices
import PySpectra.pySpectraGuiClass
import PyTango


def matchTags( tags, cliTags): 
    '''
    tags <tags>user</tags> 
    cliTags -t user,expert
    '''
    lstTags = tags.split( ',')
    lstCliTags = cliTags.split( ',')
    
    for tag in lstTags: 
        for cliTag in lstCliTags: 
            if tag.upper() == cliTag.upper():
                #print( "+++matchTags %s %s -> True " % (repr( tags), repr( cliTags)))
                return True
    #print( "+++matchTags %s %s -> False " % (repr( tags), repr( cliTags)))
    return False

def launchMoveMotor( dev, devices, app, logWidget = None, parent = None): 
    '''
    called from 
      - TngGui.main() 
      - pyspMonitorClass
    '''
    w = moveMotor.moveMotor( dev, devices, logWidget, app, parent)
    return w


class mainMenu( QtGui.QMainWindow):
    '''
    the main class of the TngTool application
    '''
    def __init__( self, args = None, app = None, devs = None, parent = None):
        super( mainMenu, self).__init__( parent)
        

        self.setWindowTitle( "TngGui")


        if PySpectra.InfoBlock.monitorGui is None:
            PySpectra.InfoBlock.setMonitorGui( self)

        self.args = args        
        if devs is None: 
            self.devices = devices.Devices( args = args, xmlFile = None, parent = self)
        else: 
            self.devices = devs

        if self.args.tags and len( self.args.namePattern) > 0:
            print( "TngGui: specify tags or names")
            sys.exit( 255)

        self.app = app

        self.w_attr = None
        self.w_commands = None
        self.w_encAttr = None
        self.w_moveMotor = None
        self.w_prop = None
        self.w_timer = None
        self.pyspGui = None
        self.move( 700, 20)

        if not os.access( "/etc/tangorc", os.R_OK): 
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "/etc/tangorc does not exist", QtGui.QMessageBox.Ok)
            raise ValueError( "tngGuiClass no /etc/tangorc")

        ret = os.popen( "grep TANGO_USER /etc/tangorc").read()
        ret = ret.strip()
        self.tangoUser = ret.split( '=')[1]

        ret = os.popen( "hostname").read()
        self.hostName = ret.strip()

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
        if len( self.devices.allMotors) < 5:
            self.scrollArea.setMinimumHeight( 200)
        elif len( self.devices.allMotors) < 9:
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
        self.toolsMenu.addAction( self.nxselectorAction)
        #
        self.motorMonitorAction = QtGui.QAction('SardanaMotorMonitor', self)        
        self.motorMonitorAction.triggered.connect( self.cb_launchMotorMonitor)
        self.toolsMenu.addAction( self.motorMonitorAction)

        #self.sardanaMonitorAction = QtGui.QAction('SardanaMonitor', self)        
        #self.sardanaMonitorAction.triggered.connect( self.cb_launchSardanaMonitor)
        #self.toolsMenu.addAction( self.sardanaMonitorAction)

        self.spockAction = QtGui.QAction('Spock', self)        
        self.spockAction.triggered.connect( self.cb_launchSpock)
        self.toolsMenu.addAction( self.spockAction)

        if not graPyspIfc.getSpectra(): 

            self.pyspMonitorAction = QtGui.QAction('pyspMonitor', self)        
            self.pyspMonitorAction.triggered.connect( self.cb_launchPyspMonitor)
            self.toolsMenu.addAction( self.pyspMonitorAction)

            self.pyspGuiAction = QtGui.QAction('pyspViewer', self)        
            self.pyspGuiAction.triggered.connect( self.cb_launchPyspGui)
            self.toolsMenu.addAction( self.pyspGuiAction)

            self.evinceAction = QtGui.QAction('evince pyspOutput.pdf', self)        
            self.evinceAction.triggered.connect( self.cb_launchEvince)
            self.toolsMenu.addAction( self.evinceAction)

        self.macroguiAction = QtGui.QAction('Macrogui', self)        
        self.macroguiAction.triggered.connect( self.cb_launchMacrogui)
        self.toolsMenu.addAction( self.macroguiAction)

        self.mcaAction = QtGui.QAction('MCA', self)        
        self.mcaAction.triggered.connect( self.cb_launchMCA)
        self.toolsMenu.addAction( self.mcaAction)


        #self.toolsMenu.addAction( self.spectraAction)

        #
        # Files
        #
        self.filesMenu = self.menuBar.addMenu('Files')
        self.editOnlineXmlAction = QtGui.QAction('online.xml', self)        
        self.editOnlineXmlAction.setStatusTip('Edit /online_dir/online.xml')
        self.editOnlineXmlAction.triggered.connect( self.cb_editOnlineXml)
        self.filesMenu.addAction( self.editOnlineXmlAction)

        self.editTangoDumpLisAction = QtGui.QAction('TangoDump.lis', self)        
        self.editTangoDumpLisAction.setStatusTip('Edit /online_dir/TangoDump.lis')
        self.editTangoDumpLisAction.triggered.connect( self.cb_editTangoDumpLis)
        self.filesMenu.addAction( self.editTangoDumpLisAction)

        self.editMotorLogLisAction = QtGui.QAction('motorLog.lis', self)        
        self.editMotorLogLisAction.setStatusTip('Edit /online_dir/MotorLogs/motorLog.lis')
        self.editMotorLogLisAction.triggered.connect( self.cb_editMotorLogLis)
        self.filesMenu.addAction( self.editMotorLogLisAction)

        self.editIpythonLogAction = QtGui.QAction('/online_dir/ipython_log.py', self)        
        self.editIpythonLogAction.triggered.connect( self.cb_editIpythonLog)
        self.filesMenu.addAction( self.editIpythonLogAction)

        self.editSardanaConfigAction = self.filesMenu.addAction(self.tr("SardanaConfig.py"))   
        self.editSardanaConfigAction.setStatusTip('Edit /online_dir/SardanaConfig.py (executed at the end of SardanaAIO.py)')
        self.editSardanaConfigAction.triggered.connect( self.cb_editSardanaConfig)

        self.edit00StartAction = QtGui.QAction('00-start.py', self)  
        self.edit00StartAction.setStatusTip('Edit the Spock startup file')
        self.edit00StartAction.triggered.connect( self.cb_edit00Start)
        self.filesMenu.addAction( self.edit00StartAction)

        self.editMacroServerPropertiesAction = QtGui.QAction('MacroServer-Properties', self)  
        self.editMacroServerPropertiesAction.setStatusTip('Copies /online_dir/MacroServer/macroserver.properties into a temporary file and launches an editor')
        self.editMacroServerPropertiesAction.triggered.connect( self.cb_editMacroServerProperties)
        self.filesMenu.addAction( self.editMacroServerPropertiesAction)

        self.editMacroServerEnvironmentAction = QtGui.QAction('MacroServer Environment', self)  
        self.editMacroServerEnvironmentAction.setStatusTip('Stores the MacroServer environment in a temporary file and launches an editor')
        self.editMacroServerEnvironmentAction.triggered.connect( self.cb_editMacroServerEnvironment)
        self.filesMenu.addAction( self.editMacroServerEnvironmentAction)

        #
        # LogFiles
        #
        self.logFilesMenu = self.menuBar.addMenu('LogFiles')
        self.fillLogFilesMenu()

        #
        # Misc
        #
        self.miscMenu = self.menuBar.addMenu('Misc')

        self.restartTimerAction = QtGui.QAction('Restart refresh timer', self)        
        self.restartTimerAction.setStatusTip('Restart the timer that refreshes this widget')
        self.restartTimerAction.triggered.connect( self.cb_restartTimer)
        self.miscMenu.addAction( self.restartTimerAction)

        self.stopTimerAction = QtGui.QAction('Stop refresh timer', self)        
        self.stopTimerAction.setStatusTip('Stop the timer that refreshes this widget')
        self.stopTimerAction.triggered.connect( self.cb_stopTimer)
        self.miscMenu.addAction( self.stopTimerAction)

        self.logToTempFileAction = QtGui.QAction('Write log widget to file and edit it.', self)
        self.logToTempFileAction.triggered.connect( self.cb_logToTempFile)
        self.miscMenu.addAction( self.logToTempFileAction)

        #
        # selected MacroServer variables
        #
        self.macroServerAction = QtGui.QAction('MacroServer (Selected Features)', self)        
        self.macroServerAction.setStatusTip('Selected MacroServer features')
        self.macroServerAction.triggered.connect( self.cb_msIfc)
        self.miscMenu.addAction( self.macroServerAction)
        #
        # Table
        #
        self.tableMenu = self.menuBar.addMenu('Table')

        self.motorTableAction = QtGui.QAction('Motors', self)        
        self.motorTableAction.triggered.connect( self.cb_motorTable)
        self.tableMenu.addAction( self.motorTableAction)

        if len( self.devices.allAdcs) > 0 or len( self.devices.allDacs) > 0:
            self.adcDacTableAction = QtGui.QAction('ADC/DACs', self)        
            self.adcDacTableAction.triggered.connect( self.cb_adcDacTable)
            self.tableMenu.addAction( self.adcDacTableAction)

        if len( self.devices.allCameras) > 0:
            self.cameraTableAction = QtGui.QAction('Cameras', self)        
            self.cameraTableAction.triggered.connect( self.cb_cameraTable)
            self.tableMenu.addAction( self.cameraTableAction)

        if len( self.devices.allCounters) or \
           len( self.devices.allTangoAttrCtrls) > 0 or \
           len( self.devices.allTangoCounters) > 0:
            self.counterTableAction = QtGui.QAction('Counters', self)        
            self.counterTableAction.triggered.connect( self.cb_counterTable)
            self.tableMenu.addAction( self.counterTableAction)

        if len( self.devices.allIRegs) > 0 or len(self.devices.allORegs) > 0:
            self.ioregTableAction = QtGui.QAction('IORegs', self)        
            self.ioregTableAction.triggered.connect( self.cb_ioregTable)
            self.tableMenu.addAction( self.ioregTableAction)

        if len( self.devices.allMCAs) > 0:
            self.mcaTableAction = QtGui.QAction('MCAs', self)        
            self.mcaTableAction.triggered.connect( self.cb_mcaTable)
            self.tableMenu.addAction( self.mcaTableAction)

        if len( self.devices.allModuleTangos) > 0:
            self.moduleTangoTableAction = QtGui.QAction('ModuleTango', self)        
            self.moduleTangoTableAction.triggered.connect( self.cb_moduleTangoTable)
            self.tableMenu.addAction( self.moduleTangoTableAction)

        if len( self.devices.allPiLCModules) > 0:
            self.PiLCModulesTableAction = QtGui.QAction('PiLCModules', self)        
            self.PiLCModulesTableAction.triggered.connect( self.cb_PiLCModulesTable)
            self.tableMenu.addAction( self.PiLCModulesTableAction)

        if len( self.devices.allTimers) > 0:
            self.timerTableAction = QtGui.QAction('Timers (extra widget)', self)        
            self.timerTableAction.triggered.connect( self.cb_launchTimer)
            self.tableMenu.addAction( self.timerTableAction)

        if len( self.devices.allVfcAdcs) > 0:
            self.vfcadcTableAction = QtGui.QAction('VFCADCs', self)        
            self.vfcadcTableAction.triggered.connect( self.cb_vfcadcTable)
            self.tableMenu.addAction( self.vfcadcTableAction)

        if len( self.devices.allMGs) > 0:
            self.mgTableAction = QtGui.QAction('MGs', self)        
            self.mgTableAction.triggered.connect( self.cb_mgTable)
            self.tableMenu.addAction( self.mgTableAction)

        if len( self.devices.allDoors) > 0:
            self.doorTableAction = QtGui.QAction('Doors', self)        
            self.doorTableAction.triggered.connect( self.cb_doorTable)
            self.tableMenu.addAction( self.doorTableAction)

        if len( self.devices.allMSs) > 0:
            self.msTableAction = QtGui.QAction('Macroserver', self)        
            self.msTableAction.triggered.connect( self.cb_msTable)
            self.tableMenu.addAction( self.msTableAction)

        if len( self.devices.allPools) > 0:
            self.poolTableAction = QtGui.QAction('Pools', self)        
            self.poolTableAction.triggered.connect( self.cb_poolTable)
            self.tableMenu.addAction( self.poolTableAction)

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
        self.pythonVersionAction = self.helpMenu.addAction(self.tr("PythonVersion"))
        self.pythonVersionAction.triggered.connect( self.cb_pythonVersion)
        self.colorCodeAction = self.helpMenu.addAction(self.tr("Color code"))
        self.colorCodeAction.triggered.connect( self.cb_colorCode)

        self.activityIndex = 0
        self.activity = self.menuBarActivity.addMenu( "_")

    def fillLogFilesMenu( self): 
        import glob
        #
        # "/tmp/tango-%s/MacroServer/%s/log.txt" %  (tangoUser, hostName)
        #
        self.editMacroServerLogTxtAction = QtGui.QAction( "/tmp/tango-%s/MacroServer/%s/log.txt" %  
                                                          (self.tangoUser, self.hostName), self)  
        self.editMacroServerLogTxtAction.triggered.connect( self.cb_editMacroServerLogTxt)
        self.logFilesMenu.addAction( self.editMacroServerLogTxtAction)

        #
        # "/var/tmp/ds.log/MacroServer_%s.log" %  (hostName)
        #
        self.editMacroServerLogAction = QtGui.QAction( "/var/tmp/ds.log/MacroServer_%s.log" % (self.hostName), self)  
        self.editMacroServerLogAction.triggered.connect( self.cb_editMacroServerLogLog)
        self.logFilesMenu.addAction( self.editMacroServerLogAction)

        #
        # "/tmp/tango-%s/Pool/%s/log.txt" %  (tangoUser, hostName)
        #
        self.editPoolLogTxtAction = QtGui.QAction( "/tmp/tango-%s/Pool/%s/log.txt" %  ( self.tangoUser, self.hostName), self)  
        self.editPoolLogTxtAction.triggered.connect( self.cb_editPoolLogTxt)
        self.logFilesMenu.addAction( self.editPoolLogTxtAction)
        #
        # "/var/tmp/ds.log/Pool_%s.log" %  (hostName)
        #
        self.editPoolLogLogAction = QtGui.QAction( "/var/tmp/ds.log/Pool_%s.log" %  ( self.hostName), self)  
        self.editPoolLogLogAction.triggered.connect( self.cb_editPoolLogLog)
        self.logFilesMenu.addAction( self.editPoolLogLogAction)

        self.logFilesMenu.addSeparator()

        #
        # all server logs
        #
        logFiles = glob.glob( "/var/tmp/ds.log/*.log")
        
        logFiles.sort()

        for fl in logFiles:
            if fl.find( '[') > 0 and fl.find( ']') > 0: 
                continue
            if fl.find( 'MacroServer') != -1: 
                continue
            if fl.find( 'Pool') != -1: 
                continue
            logFileAction = QtGui.QAction( fl, self)  
            logFileAction.triggered.connect( self.make_logFileCb( fl))
            self.logFilesMenu.addAction( logFileAction)
            
    def make_logFileCb( self, fileName): 
        def cb():
            editor = os.getenv( "EDITOR")
            if editor is None:
                editor = "emacs"
            os.system( "%s %s&" % (editor, fileName))
            return 
        return cb
            
    def cb_launchTimer( self): 
        self.w_timer = tngAPI.timerWidget( self.logWidget, self.devices.allTimers, self)
        self.w_timer.show()
        return self.w_timer

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
        
    def cb_mgTable( self):
        self.fillMGs()
        
    def cb_doorTable( self):
        self.fillDoors()
        
    def cb_msTable( self):
        self.fillMSs()
        
    def cb_poolTable( self):
        self.fillPools()
    #
    # the closeEvent is called when the window is closed by 
    # clicking the X at the right-upper corner of the frame
    #
    def closeEvent( self, e):
        self.cb_closeMainMenu()
        #e.ignore()
    
    def cb_closeMainMenu( self):

        self.cb_stopMove()

        if self.w_attr is not None: 
            self.w_attr.close()
            self.w_attr = None

        if self.w_commands is not None: 
            self.w_commands.close()
            self.w_commands = None

        if self.w_encAttr is not None: 
            self.w_encAttr.close()
            self.w_encAttr = None

        if self.w_moveMotor is not None: 
            self.w_moveMotor.close()
            self.w_moveMotor = None

        if self.w_prop is not None: 
            self.w_prop.close()
            self.w_prop = None

        if self.w_timer is not None:
            self.w_timer.close()
            self.w_timer = None

        if self.pyspGui: 
            self.pyspGui.close()
            self.pyspGui = None
        #
        # eventually 
        #
        graPyspIfc.close()

        return 

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

    def cb_editMacroServerLogTxt( self):
            
        fName =  "/tmp/tango-%s/MacroServer/%s/log.txt" %  ( self.tangoUser, self.hostName)
        if not os.access( fName, os.R_OK):
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "%s does not exist" % fName,
                                       QtGui.QMessageBox.Ok)
            return
        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s %s&" % (editor, fName))

    def cb_editMacroServerLogLog( self):
            
        fName =  "/var/tmp/ds.log/MacroServer_%s.log" %  ( self.hostName)
        if not os.access( fName, os.R_OK):
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "%s does not exist" % fName,
                                       QtGui.QMessageBox.Ok)
            return
        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s %s&" % (editor, fName))

    def cb_editPoolLogTxt( self):

        fName =  "/tmp/tango-%s/Pool/%s/log.txt" %  ( self.tangoUser, self.hostName)
        if not os.access( fName, os.R_OK):
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "%s does not exist" % fName,
                                       QtGui.QMessageBox.Ok)
            return
        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s %s&" % (editor, fName))

    def cb_editPoolLogLog( self):

        fName =  "/var/tmp/ds.log/Pool_%s.log" %  ( self.hostName)
        if not os.access( fName, os.R_OK):
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "%s does not exist" % fName,
                                       QtGui.QMessageBox.Ok)
            return
        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s %s&" % (editor, fName))

    def cb_editMacroServerProperties( self):
        '''
        creates a temporary file containing the /online_dir/Macroserver/macroserver.properties
        calls an EDITOR to open it
        '''
        import tempfile
        import shelve
        if sys.version.split( '.')[0] == '2': 
            hsh = shelve.open('/online_dir/MacroServer/macroserver.properties')
            ret = HasyUtils.dct_print2str( hsh)
        else: 
            self.logWidget.append( "editMacroServerProperties: not possible in Python3")
            return 

        new_file, filename = tempfile.mkstemp()
        if sys.version.split( '.')[0] == '2': 
            os.write(new_file, "#\n%s" % ret)
        else: 
            os.write(new_file, bytes( "#\n%s" % ret, 'utf-8'))
        os.close(new_file)

        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s %s&" % (editor, filename))
        return 

    def cb_editMacroServerEnvironment( self):
        '''
        creates a temporary file containing the active MacroSerqver environment
        calls an EDITOR to open it
        
        '''
        import tempfile

        d = HasyUtils.getEnvDct()
        ret = HasyUtils.dct_print2str( d)

        new_file, filename = tempfile.mkstemp()
        if sys.version.split( '.')[0] == '2': 
            os.write(new_file, "#\n%s" % ret)
        else: 
            os.write(new_file, bytes( "#\n%s" % ret, 'utf-8'))
        os.close(new_file)

        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s %s&" % (editor, filename))
        return 
        
    def cb_restartTimer( self):
        self.updateTimer.stop()
        self.updateTimer.start( definitions.TIMEOUT_REFRESH)
        
    def cb_stopTimer( self):
        self.updateTimer.stop()

    def cb_logToTempFile( self):
        fName = HasyUtils.createScanName( "smm") + ".lis"
        try:
            out = open( fName, "w")
        except Exception as e:
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
        self.stopMove.setToolTip( "Stop moving motors")
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
        for dev in self.devices.allMotors:
            if dev[ 'proxy'].state() == PyTango.DevState.MOVING:
                utils.execStopMove( dev)

    def cb_msIfc( self):
        self.ms = macroServerIfc.MacroServerIfc( self.logWidget, self)
        self.ms.show()

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
            if os.path.exists( "/usr/bin/terminator"):
                sts = os.system( "terminator -e /usr/bin/spock &")
            else: 
                sts = os.system( "xterm -bg white -fg black -e /usr/bin/spock &")
        return 

    def cb_launchPyspGui( self):
        #
        # one pyspViewer GUI is enough
        #
        if self.pyspGui is None: 
            self.pyspGui = PySpectra.pySpectraGuiClass.pySpectraGui()
            self.pyspGui.show()
        else: 
            self.pyspGui.raise_()
            self.pyspGui.activateWindow()
        return 

    def cb_launchMCA( self): 
        self.mcaWidget = mcaWidget.mcaWidget( devices = self.devices, 
                                              logWidget = self.logWidget, 
                                              app = None, parent = self)
        self.mcaWidget.show()
        
    def cb_launchPyspMonitor( self):
        os.system( "/usr/bin/pyspMonitor.py &")

    def cb_launchEvince( self):
        sts = os.system( "evince pyspOutput.pdf &")

    def __del__( self):
        pass

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

    def cb_pythonVersion(self):
        w = helpBox.HelpBox( self, self.tr("HelpWidget"), self.tr(
            "Python %d.%d" % (sys.version_info.major, sys.version_info.minor)))
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

        for dev in self.devices.allMotors:
            #print( "connecting to %s" % dev[ 'name'])
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
                    
            except utils.TMO as e:
                print( "fillMotorList: failed to connect to %s" % dev[ 'name'])
                del dev
            signal.alarm(0)
        signal.signal( signal.SIGALRM, hndlr)
        self.base.setLayout( layout_grid)
        self.scrollArea.setWidget( self.base)
        self.refreshFunc = self.refreshMotors

    def fillIORegs( self):

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
        for dev in self.devices.allIRegs:
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

        for dev in self.devices.allORegs:
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
        for dev in self.devices.allAdcs:
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

        for dev in self.devices.allDacs:
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
        for dev in self.devices.allCameras:
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
        for dev in self.devices.allPiLCModules:
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
        for dev in self.devices.allModuleTangos:
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
        for dev in self.devices.allMCAs:
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

        for dev in self.devices.allVfcAdcs:
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

        for dev in self.devices.allCounters + \
            self.devices.allTangoAttrCtrls + \
            self.devices.allTangoCounters:

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

    def fillMGs( self):

        if self.base is not None:
            self.base.destroy( True, True)

        self.base = QtGui.QWidget()
        layout_grid = QtGui.QGridLayout()

        layout_grid.addWidget( QtGui.QLabel( "Alias"), 0, 0)
        count = 1
        for dev in self.devices.allMGs:
            aliasName = utils.QPushButtonTK( dev['name'])
            aliasName.setToolTip( "MB-1: Attributes\nMB-2: Commands\nMB-3: Properties")
            aliasName.mb1.connect( self.make_cb_attributes( dev, self.logWidget))
            aliasName.mb2.connect( self.make_cb_commands( dev, self.logWidget))
            aliasName.mb3.connect( self.make_cb_properties( dev, self.logWidget)) 
            layout_grid.addWidget( aliasName, count, 0)
            
            count += 1

        self.base.setLayout( layout_grid)
        self.scrollArea.setWidget( self.base)
        self.refreshFunc = self.refreshMGs
        

    def fillDoors( self):

        if self.base is not None:
            self.base.destroy( True, True)

        self.base = QtGui.QWidget()
        layout_grid = QtGui.QGridLayout()

        layout_grid.addWidget( QtGui.QLabel( "Name"), 0, 0)
        count = 1
        for dev in self.devices.allDoors:
            aliasName = utils.QPushButtonTK( dev['name'])
            aliasName.setToolTip( "MB-1: Attributes\nMB-2: Commands\nMB-3: Properties")
            aliasName.mb1.connect( self.make_cb_attributes( dev, self.logWidget))
            aliasName.mb2.connect( self.make_cb_commands( dev, self.logWidget))
            aliasName.mb3.connect( self.make_cb_properties( dev, self.logWidget)) 
            layout_grid.addWidget( aliasName, count, 0)
            
            count += 1

        self.base.setLayout( layout_grid)
        self.scrollArea.setWidget( self.base)
        self.refreshFunc = self.refreshDoors

    def fillMSs( self):

        if self.base is not None:
            self.base.destroy( True, True)

        self.base = QtGui.QWidget()
        layout_grid = QtGui.QGridLayout()

        layout_grid.addWidget( QtGui.QLabel( "Name"), 0, 0)
        count = 1
        for dev in self.devices.allMSs:
            aliasName = utils.QPushButtonTK( dev['name'])
            aliasName.setToolTip( "MB-1: Attributes\nMB-2: Commands\nMB-3: Properties")
            aliasName.mb1.connect( self.make_cb_attributes( dev, self.logWidget))
            aliasName.mb2.connect( self.make_cb_commands( dev, self.logWidget))
            aliasName.mb3.connect( self.make_cb_properties( dev, self.logWidget)) 
            layout_grid.addWidget( aliasName, count, 0)
            
            count += 1

        self.base.setLayout( layout_grid)
        self.scrollArea.setWidget( self.base)
        self.refreshFunc = self.refreshMSs

    def fillPools( self):

        if self.base is not None:
            self.base.destroy( True, True)

        self.base = QtGui.QWidget()
        layout_grid = QtGui.QGridLayout()

        layout_grid.addWidget( QtGui.QLabel( "Name"), 0, 0)
        count = 1
        for dev in self.devices.allPools:
            aliasName = utils.QPushButtonTK( dev['name'])
            aliasName.setToolTip( "MB-1: Attributes\nMB-2: Commands\nMB-3: Properties")
            aliasName.mb1.connect( self.make_cb_attributes( dev, self.logWidget))
            aliasName.mb2.connect( self.make_cb_commands( dev, self.logWidget))
            aliasName.mb3.connect( self.make_cb_properties( dev, self.logWidget)) 
            layout_grid.addWidget( aliasName, count, 0)
            
            count += 1

        self.base.setLayout( layout_grid)
        self.scrollArea.setWidget( self.base)
        self.refreshFunc = self.refreshPools
        

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
            for dev in self.devices.allMotors:
                if dev[ 'flagOffline']:
                    continue
                if dev[ 'w_pos'].visibleRegion().isEmpty():
                    continue
                #
                # see, if state() responds. If not ignore the motor
                #
                try:
                    sts = dev[ 'proxy'].state()
                except Exception as e:
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
        except utils.TMO as e:
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
            for dev in self.devices.allIRegs + self.devices.allORegs:
                if dev[ 'flagOffline']:
                    continue
                if dev[ 'w_value'].visibleRegion().isEmpty():
                    continue
                #
                # see, if state() responds. If not ignore the motor
                #
                try:
                    sts = dev[ 'proxy'].state()
                except Exception as e:
                    dev[ 'w_value'].setText( "None")
                    continue
                
                # handle the position
                #
                dev[ 'w_value'].setText( "%d" % dev ['proxy'].Value)

        except utils.TMO as e:
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
            for dev in self.devices.allVfcAdcs:
                if dev[ 'flagOffline']:
                    continue
                if dev[ 'w_counts'].visibleRegion().isEmpty():
                    continue
                #
                # see, if state() responds. If not ignore the motor
                #
                try:
                    sts = dev[ 'proxy'].state()
                except Exception as e:
                    dev[ 'w_counts'].setText( "None")
                    continue
                try:
                    dev[ 'w_counts'].setText( utils.getCounterValueStr( dev))
                except Exception as e:
                    dev[ 'w_counts'].setText( "None")
                    print( "refreshTimerCounters: trouble reading Value of %s" % dev[ 'name'])
                    

        except utils.TMO as e:
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
            for dev in self.devices.allCounters + \
                self.devices.allTangoAttrCtrls + \
                self.devices.allTangoCounters:
                if dev[ 'flagOffline']:
                    continue
                if dev[ 'w_counts'].visibleRegion().isEmpty():
                    continue
                #
                # see, if state() responds. If not ignore the motor
                #
                try:
                    sts = dev[ 'proxy'].state()
                except Exception as e:
                    dev[ 'w_counts'].setText( "None")
                    continue
                try:
                    dev[ 'w_counts'].setText( utils.getCounterValueStr( dev))
                except Exception as e:
                    dev[ 'w_counts'].setText( "None")
                    print( "refreshTimerCounters: trouble reading Value of %s" % dev[ 'name'])
                    

        except utils.TMO as e:
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
            for dev in self.devices.allAdcs + self.devices.allDacs:
                if dev[ 'flagOffline']:
                    continue
                if dev[ 'w_value'].visibleRegion().isEmpty():
                    continue
                #
                # see, if state() responds. If not ignore the motor
                #
                try:
                    sts = dev[ 'proxy'].state()
                except Exception as e:
                    dev[ 'w_value'].setText( "None")
                    continue
                #
                # handle the value
                #
                dev[ 'w_value'].setText( "%g" % utils.getDacValue( dev))

        except utils.TMO as e:
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

    def refreshMGs( self):
        pass

    def refreshDoors( self):
        pass

    def refreshMSs( self):
        pass

    def refreshPools( self):
        pass

    def handlerALRM( signum, frame, arg3):
        #print( "handlerALRM: called with signal %d" % signum)
        raise utils.TMO( "tmo-excepttion")

    def make_cb_resetCounter( self, dev, logWidget):
        def cb():
            try:
                sts = dev[ 'proxy'].state()
            except Exception as e:
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "make_cb_oreg: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return

            try:
                dev[ 'proxy'].reset()
                self.logWidget.append( "tngGuiClass.cb_resetCounter: reset %s" % dev[ 'name'])
            except Exception as e:
                print( "Trouble to reset %s" % dev[ 'name'])
                print( repr( e))

        return cb

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

    def make_cb_oreg( self, dev, logWidget):
        def cb():
            try:
                sts = dev[ 'proxy'].state()
            except Exception as e:
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
            except Exception as e:
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

            if dev[ 'name'].upper() in [ 'EXP_DMY01', 'EXP_DMY02', 'EXP_DMY03']: 
                if logWidget is not None: 
                    logWidget.append( "tngGuiClass: MoveMotor not for dummy motors")
                else:
                    raise ValueError( "tngGuiClass: MoveMotor not for dummy motors")

            if self.w_moveMotor is not None:
                self.w_moveMotor.close()
                del self.w_moveMotor
                
            try:
                sts = dev[ 'proxy'].state()
            except Exception as e:
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "cb_move: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return

            self.w_moveMotor = moveMotor.moveMotor( dev, self.devices, logWidget, None, self)
            self.w_moveMotor.show()
            return self.w_moveMotor
        return cb

    def make_cb_attributes( self, dev, logWidget):
        def cb():
            import tngGui.lib.deviceAttributes as deviceAttributes
            try:
                sts = dev[ 'proxy'].state()
            except Exception as e:
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "cb_attributes: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return 
                
            # 
            # remove 'self.' to allow for one widget only
            # 
            self.w_attr = deviceAttributes.deviceAttributes( dev, logWidget, self)
            self.w_attr.show()
            return self.w_attr
        return cb

    def make_cb_commands( self, dev, logWidget):
        def cb():
            import tngGui.lib.deviceCommands as deviceCommands
            try:
                sts = dev[ 'proxy'].state()
            except Exception as e:
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "cb_commands: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return 
                
            # 
            # remove 'self.' to allow for one widget only
            # 
            self.w_commands = deviceCommands.deviceCommands( dev, logWidget, self)
            self.w_commands.show()
            return self.w_commands
        return cb

    def make_cb_properties( self, dev, logWidget):
        def cb():
            import tngGui.lib.deviceProperties as deviceProperties
            #
            # replace self.w_prop with w_prop to allow for one 
            # properties widget only
            #
            self.w_prop = deviceProperties.deviceProperties( dev, self.logWidget, self)
            self.w_prop.show()
            return self.w_prop

        return cb

    def make_cb_mb3( self, dev, logWidget):
        def cb():
            import tngGui.lib.deviceAttributes as deviceAttributes
            lst = HasyUtils.getDeviceProperty( dev['device'], "FlagEncoder", dev[ 'hostname'])
            if len(lst) == 0 or lst[0] != "1":
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "EncoderAttribute widget not available for %s, FlagEncoder != 1" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return

            try:
                sts = dev[ 'proxy'].state()
            except Exception as e:
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "cb_mb3: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return 
                
            self.w_encAttr = deviceAttributes.motorEncAttributes( dev, logWidget, self)
            self.w_encAttr.show()
            return self.w_encAttr
        return cb

    def make_cb_readMCA( self, dev, logWidget):
        def cb():
            proxy = dev[ 'proxy']
            try:
                sts = proxy.state()
            except Exception as e:
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "cb_readMCA: %s, device is offline" % dev[ 'name'], 
                                           QtGui.QMessageBox.Ok)
                return 
            PySpectra.cls()
            PySpectra.delete()
            try: 
                proxy.read()
            except Exception as e: 
                self.logWidget.append( "cb_readMCA: read() threw an exception")
                utils.ExceptionToLog( e, self.logWidget)
                for arg in e.args: 
                    if arg.desc.find( 'busy') != -1:
                        self.logWidget.append( "consider to execute stop() on the MCA first")
                        break
                return 
            PySpectra.Scan( name =  dev[ 'name'], 
                            y = proxy.data)
            PySpectra.display()
            self.cb_launchPyspGui()
            return 
        return cb



