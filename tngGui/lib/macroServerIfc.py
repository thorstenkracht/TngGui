#!/usr/bin/env python

from taurus.external.qt import QtGui, QtCore 
import PyTango
import math, os
import definitions, utils, HasyUtils
import json
import tngGui.lib.helpBox as helpBox


class MacroServerIfc( QtGui.QMainWindow):
    def __init__( self, logWidget = None, parent = None):
        super( MacroServerIfc, self).__init__( parent)
        self.parent = parent
        self.setWindowTitle( "Selected MacroServer Features")
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
<p><b>General Hooks</b><br>\
Hooks are explained in the Spock manual, Scans chapter.<br>\
They can be enabled or disabled and the source file can <br>\
be edited and reloaded.<br>\
It is assumed that the hooks and the on-condition Macro are in <br>\
$HOME/sardanaMacros/general_features.py<br>\
\
<p><b>GeneralOnStopFunction</b><br>\
 The on-stop function will be invoked, if a scan is terminated<br>\
by Ctrl-C. It is assumed that the sourcee file is here:<br>\
$HOME/sardanaMacros/generalFunctions/general_functions.py<br>\
\
<p><b>JsonRecorder</b><br>\
The SardanaMonitor receives json-encoded data. Therefore the JsonRecoder checkbox should be enabled.\
\
<p><b>Logging</b><br>\
LogMacro: if True, logging is active<br>\
LogMacroDir: directory where the log will be stored<br>\
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

        self.restartMS = QtGui.QPushButton(self.tr("Restart MS")) 
        self.restartMS.setToolTip( "Restart MacroServer")
        self.statusBar.addWidget( self.restartMS) 
        self.restartMS.clicked.connect( self.cb_restartMS)

        self.restartBoth = QtGui.QPushButton(self.tr("Restart MS and Pool")) 
        self.restartBoth.setToolTip( "Restart MacroServer and Pool")
        self.statusBar.addWidget( self.restartBoth) 
        self.restartBoth.clicked.connect( self.cb_restartBoth)

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
        # general hooks on-condition, on-stop
        #
        hBox = QtGui.QHBoxLayout()
        self.w_generalHooksCheckBox = QtGui.QCheckBox()
        lst = HasyUtils.getEnv( "_GeneralHooks")
        if lst is None:
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

        self.w_editGeneralHooks = QtGui.QPushButton(self.tr("Edit")) 
        self.w_editGeneralHooks.setStatusTip( "Edit file containing hooks and on-condition macros")
        hBox.addWidget( self.w_editGeneralHooks)
        self.w_editGeneralHooks.clicked.connect( self.cb_editGeneralHooks)

        self.w_reloadGeneralHooks = QtGui.QPushButton(self.tr("Reload")) 
        self.w_reloadGeneralHooks.setStatusTip( "Reload hooks and on-condition code")
        hBox.addWidget( self.w_reloadGeneralHooks)
        self.w_reloadGeneralHooks.clicked.connect( self.cb_reloadGeneralHooks)
        #
        self.w_generalStopCheckBox = QtGui.QCheckBox()
        a = HasyUtils.getEnv( "GeneralOnStopFunction")
        if a is None:
            self.w_generalStopCheckBox.setChecked( False)
        else:
            self.w_generalStopCheckBox.setChecked( True)

        self.w_generalStopCheckBox.stateChanged.connect( self.cb_generalStop)
        hBox.addWidget( self.w_generalStopCheckBox)
        l = QtGui.QLabel( "GeneralOnStopFunction")
        hBox.addWidget( l)
        l.setMinimumWidth( 120)

        self.w_editOnStop = QtGui.QPushButton(self.tr("Edit OnStop")) 
        self.w_editOnStop.setToolTip( "After edit, restart MacroServer")
        self.w_editOnStop.setStatusTip( "Edit ~/sardnanaMacros/generalFunctions/general_functions.py")
        hBox.addWidget( self.w_editOnStop)
        self.w_editOnStop.clicked.connect( self.cb_editOnStop)
        
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
        # LogMacro
        # 
        hBox = QtGui.QHBoxLayout()
        self.w_LogMacroCheckBox = QtGui.QCheckBox()
        self.w_LogMacroCheckBox.setToolTip( "If True, logging is active. \nThe file session_<BL>_door_<TANGO_HOST>.<i>.log\nis created in LogMacroDir")
        self.w_LogMacroCheckBox.stateChanged.connect( self.cb_LogMacro)
        hBox.addWidget( self.w_LogMacroCheckBox)
        l = QtGui.QLabel( "LogMacro")
        l.setMinimumWidth( 120)
        l.setToolTip( "If True, logging is active. \nThe file session_<BL>_door_<TANGO_HOST>.<i>.log\nis created in LogMacroDir")
        hBox.addWidget( l)
        hBox.addStretch()
        self.layout_v.addLayout( hBox)
        #
        #
        # LogMacroMode
        # 
        self.varsEnv.append( "LogMacroMode")
        var = "LogMacroMode"
        w = QtGui.QLabel( "%s:" % var)
        w.setToolTip( "If False, only one log file is created (recommended)")
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
        # LogMacroDir
        # 
        self.varsEnv.append( "LogMacroDir")
        var = "LogMacroDir"
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
                self.dct[ var][ "w_value"].setText( str(res))

        hsh = HasyUtils.getEnv( "_ViewOptions")
        if hsh[ 'ShowDial']:
            self.w_showDialCheckBox.setChecked( True)
        else:
            self.w_showDialCheckBox.setChecked( False)
        if hsh[ 'ShowCtrlAxis']:
            self.w_showCtrlAxisCheckBox.setChecked( True)
        else:
            self.w_showCtrlAxisCheckBox.setChecked( False)

        lst = HasyUtils.getEnv( "_GeneralHooks")
        if lst is None:
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

        a = HasyUtils.getEnv( "LogMacro")
        if a is True:
            self.w_LogMacroCheckBox.setChecked( True)
        else:
            self.w_LogMacroCheckBox.setChecked( False)


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

    def cb_LogMacro( self):
        if self.w_LogMacroCheckBox.isChecked():
            HasyUtils.setEnv( "LogMacro", True)
            a = HasyUtils.getEnv( "LogMacro")
            self.logWidget.append( "LogMacro: %s" % repr( a))
        else:
            HasyUtils.setEnv( "LogMacro", False)
            self.logWidget.append( "LogMacro: disabled")

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
            hsh = HasyUtils.getEnv( "_GeneralHooks")
            self.logWidget.append( "GeneralHooks: %s" % repr( hsh))
        else:
            HasyUtils.runMacro( "gh_disable")
            self.logWidget.append( "GeneralHooks: disabled")

    def cb_editGeneralHooks( self):
        lst = HasyUtils.getEnv( "_GeneralHooks")
        if lst is None:
            self.logWidget.append( "GeneralHooks: disabled, enable before edit")
            return
        #
        # need just one hooks macro name to identify the file
        #
        hooksMacroName = lst[0][0]
        hsh = HasyUtils.getMacroInfo( hooksMacroName)
        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        os.system( "%s %s&" % (editor, hsh[ 'file_path']))
        return 

    def cb_reloadGeneralHooks( self):
        lst = HasyUtils.getEnv( "_GeneralHooks")
        if lst is None:
            self.logWidget.append( "GeneralHooks: disabled")
            return
        #
        # use the first hook macro name. relmac pulls-in the whole file
        #
        HasyUtils.runMacro( "relmac %s" % lst[0][0] ) 
        return 

    def cb_editOnStop( self):
        lst = HasyUtils.getEnv( "GeneralOnStopFunction")
        if lst is None:
            self.logWidget.append( "GeneralOnStopFunction: disabled, enable before edit")
            return
        editor = os.getenv( "EDITOR")
        if editor is None:
            editor = "emacs"
        home = os.getenv( "HOME")
        os.system( "%s %s/sardanaMacros/generalFunctions/general_functions.py&" % (editor, home))
        return 
            
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
        except Exception as e:
            self.logWidget.append( "cb_abortMacro: Failed to create proxy to Door" )
            self.logWidget.append( repr( e))
            return 

        door.abortmacro()
        self.logWidget.append( "Sent abortmacro() to door")
        return 

    def cb_restartMS( self): 

        try: 
            MsName = HasyUtils.getLocalMacroServerServers()[0]
        except Exception as e: 
            self.logWidget.append( "cb_restartMS: failed to get MS names")
            self.logWidget.append( "cb_restartMS: %s" % repr( e))
            return 
            
        self.logWidget.append( "cb_restartMS: restarting %s" % MsName)
        self.parent.app.processEvents()

        HasyUtils.restartServer( MsName)
        self.logWidget.append( "cb_restartMS: restarting %s DONE" % MsName)
        return 

    def cb_restartBoth( self): 

        try: 
            MsName = HasyUtils.getLocalMacroServerServers()[0]
        except Exception as e: 
            self.logWidget.append( "cb_restartBoth: failed to get MS names")
            self.logWidget.append( "cb_restartBoth: %s" % repr( e))
            return 

        try: 
            PoolName = HasyUtils.getLocalPoolServers()[0]
        except Exception as e: 
            self.logWidget.append( "cb_restartBoth: failed to get Pool name")
            self.logWidget.append( "cb_restartBoth: %s" % repr( e))
            return 
            
        self.logWidget.append( "cb_restartBoth: restarting %s and %s" % (MsName, PoolName))
        self.parent.app.processEvents()

        self.logWidget.append( "cb_restartBoth: stopping %s" % MsName)
        self.parent.app.processEvents()
        HasyUtils.stopServer( MsName)

        self.logWidget.append( "cb_restartBoth: restarted %s" % PoolName)
        self.parent.app.processEvents()
        HasyUtils.restartServer( PoolName)

        self.logWidget.append( "cb_restartBoth: restarted %s DONE" % PoolName)
        self.parent.app.processEvents()

        HasyUtils.startServer( MsName)
        print( "cb_restartBoth: restarting %s and %s DONE" % (MsName, PoolName))
        return 
            
    def cb_activeMntGrpChanged( self):
        activeMntGrp = HasyUtils.getEnv( "ActiveMntGrp")
        temp = str(self.activeMntGrpComboBox.currentText())
        HasyUtils.setEnv( "ActiveMntGrp", temp)
        elements = HasyUtils.getMgElements( temp)
        self.logWidget.append( "ActiveMntGrp to %s: %s" % (temp, elements))
