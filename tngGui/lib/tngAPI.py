#!/usr/bin/env python

from taurus.external.qt import QtGui, QtCore 
import PyTango
import math
import definitions, utils, HasyUtils

class deviceAttributes( QtGui.QMainWindow):
    def __init__( self, dev, logWidget, parent = None):
        super( deviceAttributes, self).__init__( parent)
        self.parent = parent
        self.dev = dev
        self.setWindowTitle( "Attributes of %s" % self.dev[ 'name'])
        self.logWidget = logWidget
        w = QtGui.QWidget()
        self.layout_v = QtGui.QVBoxLayout()
        w.setLayout( self.layout_v)
        self.setCentralWidget( w)
        alias_l = QtGui.QLabel( self.dev[ 'name'])
        name_l = QtGui.QLabel( "%s/%s" % (self.dev[ 'hostname'], self.dev[ 'device']))
        layout_h = QtGui.QHBoxLayout()
        layout_h.addWidget( alias_l)
        layout_h.addWidget( name_l)
        self.layout_v.addLayout( layout_h)
        self.layout_grid = QtGui.QGridLayout()
        self.layout_v.addLayout( self.layout_grid)

        self.fillAttributes()
            
        #
        # Menu Bar
        #
        self.menuBar = QtGui.QMenuBar()
        self.setMenuBar( self.menuBar)
        self.fileMenu = self.menuBar.addMenu('&File')
        self.exitAction = QtGui.QAction('E&xit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect( self.cb_closeMotorAttr)
        self.fileMenu.addAction( self.exitAction)


        if self.dev[ 'module'].lower() == "oms58":
            self.miscMenu = self.menuBar.addMenu('&Misc')
            self.blackBoxAction = QtGui.QAction( 'BlackBox', self)        
            self.blackBoxAction.triggered.connect( self.cb_blackBox)
            self.miscMenu.addAction( self.blackBoxAction)

        #
        # the activity menubar: help and activity
        #
        self.menuBarActivity = QtGui.QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarActivity, QtCore.Qt.TopRightCorner)

        if self.dev[ 'module'].lower() == "oms58":
            self.helpMenu = self.menuBarActivity.addMenu('Help')
            self.helpAttr = self.helpMenu.addAction(self.tr("Attributes"))
            self.helpAttr.triggered.connect( self.cb_helpAttrOms58)
            self.helpBlackBox = self.helpMenu.addAction(self.tr("BlackBox"))
            self.helpBlackBox.triggered.connect( self.cb_helpBlackBox)
            self.helpWriteRead = self.helpMenu.addAction(self.tr("WriteRead"))
            self.helpWriteRead.triggered.connect( self.cb_helpWriteRead)
        if self.dev[ 'module'].lower() == "vfcadc":
            self.helpMenu = self.menuBarActivity.addMenu('Help')
            self.helpAttr = self.helpMenu.addAction(self.tr("Widget"))
            self.helpAttr.triggered.connect( self.cb_helpAttrVfcAdc)
        if self.dev[ 'module'].lower() == "spk":
            self.helpMenu = self.menuBarActivity.addMenu('Help')
            self.helpAttr = self.helpMenu.addAction(self.tr("Widget"))
            self.helpAttr.triggered.connect( self.cb_helpAttrSpk)

        self.activityIndex = 0
        self.activity = self.menuBarActivity.addMenu( "_")

        #
        # Status Bar
        #
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar( self.statusBar)

        if self.dev[ 'module'].lower() == "oms58":
            self.recentWrites = QtGui.QPushButton(self.tr("RecentWrites")) 
            self.recentWrites.setToolTip("RecentWrites to log widget")
            self.statusBar.addPermanentWidget( self.recentWrites) # 'permanent' to shift it right
            self.recentWrites.clicked.connect( self.cb_recentWrites)

        if self.dev[ 'module'].lower() == "vfcadc":
            self.reset = QtGui.QPushButton(self.tr("Reset")) 
            self.reset.setToolTip("Reset counts")
            self.statusBar.addPermanentWidget( self.reset) # 'permanent' to shift it right
            self.reset.clicked.connect( self.cb_resetVfcAdc)

            self.resetAll = QtGui.QPushButton(self.tr("ResetAll")) 
            self.resetAll.setToolTip("Reset all VFCADCs")
            self.statusBar.addPermanentWidget( self.resetAll) # 'permanent' to shift it right
            self.resetAll.clicked.connect( self.cb_resetAllVfcAdc)

            self.initVFCADC = QtGui.QPushButton(self.tr("InitVFCADC")) 
            self.initVFCADC.setToolTip("Execute InitVFCADC")
            self.statusBar.addPermanentWidget( self.initVFCADC) # 'permanent' to shift it right
            self.initVFCADC.clicked.connect( self.cb_initVFCADC)

        if self.dev[ 'module'].lower() == "spk":
            self.clearError = QtGui.QPushButton(self.tr("Clear error")) 
            self.clearError.setToolTip("Clear the error condition")
            self.statusBar.addPermanentWidget( self.clearError) # 'permanent' to shift it right
            self.clearError.clicked.connect( self.cb_clearError)

        self.apply = QtGui.QPushButton(self.tr("&Apply")) 
        self.statusBar.addPermanentWidget( self.apply) # 'permanent' to shift it right
        QtCore.QObject.connect( self.apply, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_applyDeviceAttributes)
        self.apply.setShortcut( "Alt+a")

        self.exit = QtGui.QPushButton(self.tr("E&xit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        QtCore.QObject.connect( self.exit, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_closeMotorAttr)
        self.exit.setShortcut( "Alt+x")

        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect( self.cb_refreshAttr)
        self.updateTimer.start( definitions.TIMEOUT_REFRESH)

    def fillAttributes( self): 
        count = 0
        self.attrInfoList = self.getAttrInfoList()

        self.attrDct = {}
        #
        # if we have many attributes, we have to create 2 'columns'
        #
        columnOffset = 0
        splitNo = len( self.attrInfoList)
        if len( self.attrInfoList) > 10:
            splitNo = math.ceil( len( self.attrInfoList)/2.)

        for attrInfo in self.attrInfoList:
            #if not hasattr( self.dev[ 'proxy'], attrInfo.name.lower()) and attrInfo.name.find( "ROI") != 0: 
            if attrInfo.name.lower() not in dir( self.dev[ 'proxy']) and attrInfo.name.find( "ROI") != 0: 
                self.logWidget.append( "motorAttrs: %s, has no attributes %s" % ( self.dev[ 'name'], attrInfo.name))
                continue
            #
            # the name label
            #
            if attrInfo.name.lower() == 'position':
                name = QtGui.QLabel( "Position (cal.)")
            else:
                name = QtGui.QLabel( attrInfo.name)
            name.setToolTip( "%s, %s" % (attrInfo.description, attrInfo.unit))
            self.layout_grid.addWidget( name, count, 0 + columnOffset)
            
            value = None
            line = None

            #
            # writeRead OmsMaxV
            #
            if attrInfo.name == 'WriteRead':
                line = QtGui.QLineEdit()
                line.setAlignment( QtCore.Qt.AlignRight)
                self.layout_grid.addWidget( line, count, 2 + columnOffset)
            #
            # ROIs
            #
            elif attrInfo.name == 'ROI1' or attrInfo.name == 'ROI2' or attrInfo.name == 'ROI3' or attrInfo.name == 'ROI4':
                value = QtGui.QLabel()
                value.setFixedWidth( definitions.POSITION_WIDTH)
                value.setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
                self.layout_grid.addWidget( value, count, 1 + columnOffset)
                line = QtGui.QLineEdit()
                line.setAlignment( QtCore.Qt.AlignRight)
                self.layout_grid.addWidget( line, count, 2 + columnOffset)
                self.attrDct[ attrInfo.name] = { "w_value": value, "w_line": line}
            #
            # all other attributes
            #
            else:
                #
                # the value field
                #
                value = QtGui.QLabel()
                value.setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
                if attrInfo.writable == PyTango._PyTango.AttrWriteType.READ_WRITE:
                    value.setFixedWidth( definitions.POSITION_WIDTH)
                    self.layout_grid.addWidget( value, count, 1 + columnOffset)
                    #
                    # the lineEdit field
                    #
                    if attrInfo.data_format != PyTango.AttrDataFormat.SPECTRUM and \
                       attrInfo.data_format != PyTango.AttrDataFormat.IMAGE: 
                        line = QtGui.QLineEdit() 
                        line.setAlignment( QtCore.Qt.AlignRight)
                        self.layout_grid.addWidget( line, count, 2 + columnOffset)
                else: 
                    #
                    # strings can be quite long, so give read-only string 2 columns space
                    #
                    if attrInfo.data_type == PyTango.CmdArgType.DevString:
                        self.layout_grid.addWidget( value, count, 1 + columnOffset, 1, 2)
                    else: 
                        self.layout_grid.addWidget( value, count, 1 + columnOffset)

            self.attrDct[ attrInfo.name] = { "w_value": value, "w_line": line}
            count += 1
            if count >= splitNo and columnOffset == 0: 
                columnOffset += 4
                count = 0
        return 

    def getAttrInfoList( self): 
        '''
        return the list of attribute info blocks
        '''
        attrOms = [ 'State', 'Status', 'Position', 'UnitLimitMin', 'UnitLimitMax', 'UnitBacklash', 'UnitCalibration',
                    'StepPositionController', 'StepPositionInternal',
                    'SlewRate', 'SlewRateMin', 'SlewRateMax', 'BaseRate',
                    'Conversion', 'Acceleration', 
                    #'StepBacklash', 'StepLimitMin', 'StepLimitMax', 
                    'SettleTime',
                    'CwLimit', 'CcwLimit', 'FlagProtected', 'FlagCheckZMXActivated', 'WriteRead']
        attrTip551 = [ 'State', 'Status', 'Voltage', 'VoltageMax', 'VoltageMin']
        attrVfcAdc = [ 'State', 'Status', 'Counts', 'Value', 'Gain', 'Offset', 'Polarity']
        attrPilcVfcAdc = [ 'State', 'Status', 'Counts', 'Value', 'Polarity']
        attrMCA_8701 = [ 'State', 'Status', 'DataLength', 'NbRois', 
                         'Counts1', 'Counts1Diff', 'ROI1',
                         'Counts2', 'Counts2Diff', 'ROI2',
                         'Counts3', 'Counts3Diff', 'ROI3',
                         'Counts4', 'Counts4Diff', 'ROI4']
        #attrMotorTango = [ 'State', 'Position', 'UnitLimitMin', 'UnitLimitMax']
        attrSpk =  [ 'State', 'Status', 'Position', 'CcwLimit', 'CwLimit', 'ConversionFactor', 'ErrorCode', 
                     'Position', 'SlewRate', 'UnitBackLash', 'UnitLimitMin', 'UnitLimitMax']
        attrMotorPool = [ 'State', 'Status', 'Position', 'Backlash', 'Acceleration', 'Velocity', 'Step_per_unit']

        attrExtra = ['BraggAngle', 'BraggOffset', 'BraggOffset0', 'BraggOffset1', 'BraggOffset3', 
                     'Crystal', 'ExitOffset', 'ExitOffsetC0', 'ExitOffsetC1', 'UpdateStatusRate', 'PositionSim']

        attrSelected = None

        if self.dev[ 'module'].lower() == 'oms58':
            attrSelected = attrOms
        elif self.dev[ 'module'].lower() == 'tip551':
            attrSelected = attrTip551
        elif self.dev[ 'module'].lower() == 'motor_pool':
            attrSelected = attrMotorPool
        elif self.dev[ 'module'].lower() == 'spk':
            attrSelected = attrSpk
        elif self.dev[ 'module'].lower() == 'vfcadc':
            if hasattr( self.dev[ 'proxy'], 'Gain'):
                attrSelected = attrVfcAdc
            else:
                attrSelected = attrPilcVfcAdc
        elif self.dev[ 'module'].lower() == 'mca_8701':
            attrSelected = attrMCA_8701
        #elif self.dev[ 'module'].lower() == 'motor_tango':
        #    attrSelected = attrMotorTango
        #    for a in attrExtra:
        #        if hasattr( self.motor, a):
        #            attrSelected.append( a)

        attrInfoListAll = self.dev[ 'proxy'].attribute_list_query()
        attrInfoList = []
        for attrInfo in attrInfoListAll: 
            if attrInfo.name == 'State': 
                ste = attrInfo
                continue
            if attrInfo.name == 'Status': 
                sts = attrInfo
                continue
            if attrSelected is not None: 
                if attrInfo.name not in attrSelected: 
                    continue
            attrInfoList.append( attrInfo)

        def cmpr( x, y): 
            return cmp( x.name, y.name)

        attrInfoList.sort( cmpr) 
        attrInfoList.append( ste)
        attrInfoList.append( sts)
        return attrInfoList
        
    def cb_clearError( self):
        '''
        Spk
        '''
        self.dev[ 'proxy'].ClearError()

    def cb_resetVfcAdc( self):
        self.dev[ 'proxy'].reset()

    def cb_resetAllVfcAdc( self):
        '''
        after a reset of a single channel, all readings are 0, but
        the next gate period shows that not all are really reset
        '''
        for dev in allVfcAdcs:
            dev[ 'proxy'].reset()

    def cb_initVFCADC( self):
        self.dev[ 'proxy'].InitVFCADC()

    def cb_refreshAttr( self):
        
        if self.isMinimized(): 
            return

        try: 
            stst = self.dev[ 'proxy'].state()
        except Exception, e:
            self.attrDct[ 'State'][ "w_value"].setText( "Offline")
            self.attrDct[ 'State'][ "w_value"].setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
            return 

        self.activityIndex += 1
        if self.activityIndex > (len( definitions.ACTIVITY_SYMBOLS) - 1):
            self.activityIndex = 0
        self.activity.setTitle( definitions.ACTIVITY_SYMBOLS[ self.activityIndex])

        for attrInfo in self.attrInfoList:
            #if not hasattr( self.dev[ 'proxy'], attrInfo.name) and attrInfo.name.find( 'ROI') != 0: 
            if attrInfo.name.lower() not in dir( self.dev[ 'proxy']) and attrInfo.name.find( "ROI") != 0: 
                continue

            if attrInfo.name.lower() == "writeread":
                continue
                
            w_value = self.attrDct[ attrInfo.name][ "w_value"]
            if w_value is None:
                continue
            #
            # ROIs
            #
            if attrInfo.name == 'ROI1' or attrInfo.name == 'ROI2' or attrInfo.name == 'ROI3' or attrInfo.name == 'ROI4':
                w_value.setText( "%s" % self.getROI( attrInfo.name))
                continue
            if attrInfo.data_format == PyTango.AttrDataFormat.IMAGE:
                w_value.setText( "Image")
                continue
            if attrInfo.data_format == PyTango.AttrDataFormat.SPECTRUM:
                w_value.setText( "Spectrum")
                continue

            try: 
                a = self.dev[ 'proxy'].read_attribute( attrInfo.name)
            except Exception, e:
                w_value.setText( "Failed")
                continue
            #
            # Boolean
            #
            if attrInfo.data_type == PyTango.CmdArgType.DevBoolean:
                w_value.setText( "%s" % str( a.value))
            #
            # Double, Float
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevDouble or \
                 attrInfo.data_type == PyTango.CmdArgType.DevFloat:
                w_value.setText( "%g" % a.value)
            #
            # Long
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevLong or \
                 attrInfo.data_type == PyTango.CmdArgType.DevLong64:
                w_value.setText( "%d" % a.value)
                if attrInfo.name.lower() == "cwlimit":
                    if a.value == 1:
                        w_value.setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
                    else:
                        w_value.setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
                if attrInfo.name.lower() == "ccwlimit":
                    if a.value == 1:
                        w_value.setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
                    else:
                        w_value.setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
            #
            # UChar, Short, UShort, ULong, ULong64
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevShort or \
                 attrInfo.data_type == PyTango.CmdArgType.DevUShort or \
                 attrInfo.data_type == PyTango.CmdArgType.DevUChar or \
                 attrInfo.data_type == PyTango.CmdArgType.DevULong or \
                 attrInfo.data_type == PyTango.CmdArgType.DevULong64:
                w_value.setText( "%d" % a.value)
            #
            # String
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevString:
                w_value.setText( "%s" % a.value)
            #
            # State
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevState:
                w_value.setText( "%s" % a.value)
                if a.value == PyTango.DevState.MOVING:
                    w_value.setStyleSheet( "background-color:%s;" % definitions.BLUE_MOVING)
                elif a.value == PyTango.DevState.ON:
                    w_value.setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
                else:
                    w_value.setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
            else:
                w_value.setText( "unknown")

    def getROI( self, roiName):
        try:
            roiArr2D = self.dev[ 'proxy'].rois
            NbRois = self.dev[ 'proxy'].NbRois
        except Exception, e:
            self.logWidget.append( "getROI: failed for %s" % (dev[ 'fullName']))
            utils.ExceptionToLog( e, logWidget)
            return 
        roiArr = []
        for elm in roiArr2D[0]:
            roiArr.append( elm)
        for elm in roiArr2D[1]:
            roiArr.append( elm)
        #
        # p.rois = [[1000,2000, 2500, 2600],[1015,2018, 2515, 2615]]
        #
        # In [30]: p.rois
        # Out[30]: 
        # array([[1000, 2000, 2500, 2600],
        #        [1015, 2018, 2515, 2615]], dtype=int32)
        #
        if NbRois > 0 and roiName.lower() == 'roi1':
            argout = "%d, %d" % (roiArr[0], roiArr[1])
        elif NbRois > 1 and roiName.lower() == 'roi2':
            argout = "%d, %d" % (roiArr[2], roiArr[3])
        elif NbRois > 2 and roiName.lower() == 'roi3':
            argout = "%d, %d" % (roiArr[4], roiArr[5])
        elif NbRois > 3 and roiName.lower() == 'roi4':
            argout = "%d, %d" % (roiArr[6], roiArr[7])
        else:
            argout = "n.a."
            
        return argout
    #
    # the closeEvent is called when the window is closed by 
    # clicking the X at the right-upper corner of the frame
    #
    def closeEvent( self, e):
        self.cb_closeMotorAttr()
        #e.ignore()

    def cb_closeMotorAttr( self):
        self.updateTimer.stop()
        self.close()


    def cb_helpAttrOms58( self):
        w = helpBox.HelpBox( self, self.tr("Help Attributes"), self.tr(
            "<h3>Attributes</h3>"
            "<ul>"
            "<li> Position (cal.): Calibrates the motor, the motor position is calibrated to the "
            "user supplied value. The user is prompted for confirmation."
            "<li> StepPositionController/Internal: the command setStepRegister is used to set " 
            "the internal and controller register. The position does not change."
            "</ul>"
                ))
        w.show()

    def cb_helpAttrSpk( self):
        w = helpBox.HelpBox( self, self.tr("Help widget"), self.tr(
            "<ul>"
            "<li> use 'online -tki' for more details"
            "<li> Error code"
            "<ul>"
            "<li> 0 no error"
            "<li> 1 emergency off"
            "<li> 2 unexpected limit switch (wrong direction)"
            "<li> 3 at limit when switched on"
            "<li> 4 both limit switches fired"
            "<li> 5 reference move stopped by limit switch"
            "<li> 6 reference move: wrong limit"
            "<li> 7 backlash greater than 1"
            "<li> 8 inconsistent limits"
            "<li> 9 hardware error( Schrittmotorklemme)"
            "<li> 10 encoder error (misaligned?)"
            "<li> 11 error during init"
            "</ul>"
            "</ul>"
                ))
        w.show()
    def cb_helpAttrVfcAdc( self):
        w = helpBox.HelpBox( self, self.tr("Help widget"), self.tr(
            "<ul>"
            "<li> Polarity: 1 or 0"
            "<li> ResetAll: after a reset of a single channel, all readings are 0, but"
            "the next gate period shows that not all are really reset"
            "</ul>"
                ))
        w.show()

    def cb_helpBlackBox( self):
        w = helpBox.HelpBox( self, self.tr("Help BlackBox"), self.tr(
            "<h3>BlackBox</h3>"
            "The Black Box contents is written to the log widget. "
            "This features finds connected clients."
                ))
        w.show()
    def cb_helpWriteRead( self):
        w = helpBox.HelpBox( self, self.tr("Help WriteRead"), self.tr(
            "<h3>WriteRead</h3>"
            "The input string is sent to the motor and the result "
            "is printed in the log widget. The server inserts an axis specification "
            "at the beginning of the string."
            "<hr>"
            "<br>"
            "<b>RP</b> Request position"
            "<br>"
            "<b>RE</b> Request encoder"
            "<br>"
            "<b>LO12345</b> Load motor position"
            "<br>"
            "<b>LP12345</b> Load motor and encoder position"
            "<br>"
            "<b>LPE12345</b> Load encoder position, independent of motor position"
            "<br>"
            "<b>CL?</b> Query closed loop state"
            "<br>"
            "<b>SI</b> Stop"
            "<br>"
            "<b>MA12345;GO;SI</b> Move absolute, set DONE when finished"
            "<br>"
            "<b>VL4321</b> Set slew rate"
            "<br>"
            "<b>VL?</b> Query slew rate"
                ))
        w.show()
        
    def cb_recentWrites( self):
        lst = self.dev[ 'proxy'].recentwrites
        self.logWidget.append('---')
        self.logWidget.append( "%s" % self.dev[ 'name'])
        for line in lst:
            if line.find('Empty') == -1:
                self.logWidget.append( line)
        
    def cb_blackBox( self):
        lst = self.dev[ 'proxy'].black_box( 100)
        self.logWidget.append('---')
        self.logWidget.append( "%s" % self.dev[ 'name'])
        for line in lst:
            if line.find('Empty') == -1:
                self.logWidget.append( line)

    def cb_applyDeviceAttributes( self):
        count = 0
        #
        # check, whether there is some input at all
        #
        for attrInfo in self.attrInfoList:
            line = self.attrDct[ attrInfo.name][ "w_line"]
            if line is None:
                continue
            if len(line.text()) > 0:
                count += 1
                attrFound = attrInfo
        if count == 0:
            self.logWidget.append( "motorAttr.cb_apply: no input")
            return 
        #
        # More than one input: clear the input lines
        #
        if count > 1:
            for attrInfo in self.attrInfoList:
                line = self.attrDct[ attrInfo.name][ "w_line"]
                if line is None:
                    continue
                line.clear()
            self.logWidget.append( "motorAttr.cb_apply: more that one input")
            return

        attrInfo = attrFound
        line = self.attrDct[ attrInfo.name][ "w_line"]
        #
        #
        #
        if attrInfo.name.lower() == 'roi1' or attrInfo.name.lower() == 'roi2' or \
           attrInfo.name.lower() == 'roi3' or attrInfo.name.lower() == 'roi4':
            temp = line.text()
            line.clear()
            self.setROI( attrInfo.name, temp)
            return
        #
        # WriteRead is a command, not an attribute
        #
        if attrInfo.name == "WriteRead":
            temp = line.text()
            try:
                reply = self.dev[ 'proxy'].command_inout( "WriteRead", str(temp))
            except Exception, e:
                self.logWidget.append( "%s: %s causes an error" % (self.dev[ 'name'], str(temp)))
                utils.ExceptionToLog( e, self.logWidget)
                line.clear()
                return 
            self.logWidget.append( "%s:%s -> %s" % (self.dev[ 'name'], temp, reply))
            line.clear()
            return
            self.logWidget.append( "%s:%s -> %s" % (self.dev[ 'name'], temp, reply))
            line.clear()
            return

        if attrInfo.name.lower() == 'position':
            reply = QtGui.QMessageBox.question(self, 
                                               'YesNo', 
                                               "Calibrate %s/%s from %g to %s" % (self.dev[ 'hostname'], 
                                                                                  self.dev[ 'device'], 
                                                                                  getPosition( self.dev), line.text()), 
                                               QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if reply != QtGui.QMessageBox.Yes:
                self.logWidget.append( "Calibration aborted")
                line.clear()
                return 
            definitions.calibrate( self.dev, float( line.text()), self.logWidget)
            line.clear()
            return 

        if attrInfo.name.lower() == 'positionsim':
            self.dev[ 'proxy'].positionsim = float( line.text())
            self.logWidget.append( "ResultSim\n%s" % (  repr(self.dev[ 'proxy'].resultsim)))
            line.clear()
            return 
            
        if attrInfo.name.lower() == "steppositioncontroller" or \
           attrInfo.name.lower() == "steppositioninternal":
            if self.dev[ 'proxy'].FlagClosedLoop:
                if self.dev[ 'proxy'].FlagClosedLoop == 1:
                    QtGui.QMessageBox.critical(self, 'Error', 
                                               "%s/%s, register cannot be changed, if a motor is in ClosedLoop" % (self.dev[ 'hostname'], self.dev[ 'device']),
                                               QtGui.QMessageBox.Ok)
                    line.clear()
                    return
            reply = QtGui.QMessageBox.question(self, 
                                               'YesNo', 
                                               "SetStepRegister (internal and controller) of %s/%s to %s (position does not change)" % (self.dev[ 'hostname'], 
                                                                                   self.dev[ 'device'], 
                                                                                   line.text()),
                                               QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if reply != QtGui.QMessageBox.Yes:
                self.logWidget.append( "SetStepRegister: abortet")
                line.clear()
                return 
            try:
                self.dev[ 'proxy'].command_inout( "SetStepRegister", int( line.text()))
            except Exception, e:
                self.logWidget.append( "%s: failed to SetStepRegister to %d" % 
                                       (self.dev[ 'name'], int( line.text())))
                utils.ExceptionToLog( e, self.logWidget)
                
            line.clear()
            return 
            
        temp = line.text()
        try:
            if attrInfo.data_type == PyTango.CmdArgType.DevBoolean:
                if temp.lower() == "false": 
                    t = False
                elif temp.lower() == "true": 
                    t = True
                self.dev[ 'proxy'].write_attribute( attrInfo.name, t)
            elif attrInfo.data_type == PyTango.CmdArgType.DevDouble or \
                 attrInfo.data_type == PyTango.CmdArgType.DevFloat:
                self.dev[ 'proxy'].write_attribute( attrInfo.name, float(temp))
            elif attrInfo.data_type == PyTango.CmdArgType.DevString:
                self.dev[ 'proxy'].write_attribute( attrInfo.name, temp)
            elif attrInfo.data_type == PyTango.CmdArgType.DevLong or \
                 attrInfo.data_type == PyTango.CmdArgType.DevULong or \
                 attrInfo.data_type == PyTango.CmdArgType.DevULong64 or \
                 attrInfo.data_type == PyTango.CmdArgType.DevUChar or \
                 attrInfo.data_type == PyTango.CmdArgType.DevShort or \
                 attrInfo.data_type == PyTango.CmdArgType.DevUShort:
                self.dev[ 'proxy'].write_attribute( attrInfo.name, int(temp))
            else:
                print "dataType not identified", attrInfo.data_type
        except Exception, e:
            self.logWidget.append( "%s: failed to set attr. %s to %s" % 
                                   (self.dev[ 'name'], attrInfo.name, repr( temp)))
            utils.ExceptionToLog( e, self.logWidget)
        line.clear()

    def setROI( self, roiName, temp):
        try:
            #
            # this is what we receive: 
            # roiArr: array([[101, 102, 201], [202, 301, 302]], dtype=int32)
            #
            roiArr = self.dev[ 'proxy'].rois
            NbRois = self.dev[ 'proxy'].NbRois
        except Exception, e:
            self.logWidget.append( "setROI: failed for %s" % (dev[ 'fullName']))
            utils.ExceptionToLog( e, logWidget)
            return 

        if len( roiArr.shape) != 2:
            self.logWidget.append( "setROI: len(roiArr.shape) != 2, instead %d" % 
                                   (len( roiArr.shape)))
            return

        #
        # this is what we send
        # p.rois = [[101, 102, 201, 202, 301, 302]]
        #
        roiArr = [np.concatenate( (roiArr[0], roiArr[1]))]
            
        #
        # 1000, 1200
        #
        lst = temp.split( ',')
        if len( lst) != 2:
            self.logWidget.append( "setROI: wrong syntax, %s" % (self.dev[ 'name']))
        
        if NbRois > 0 and roiName.lower() == 'roi1':
            roiArr[0][0] = int( lst[0])
            roiArr[0][1] = int( lst[1])
        elif NbRois > 1 and roiName.lower() == 'roi2':
            roiArr[0][2] = int( lst[0])
            roiArr[0][3] = int( lst[1])
        elif NbRois > 2 and roiName.lower() == 'roi3':
            roiArr[0][4] = int( lst[0])
            roiArr[0][5] = int( lst[1])
        elif NbRois > 3 and roiName.lower() == 'roi4':
            roiArr[0][6] = int( lst[0])
            roiArr[0][7] = int( lst[1])
        else:
            self.logWidget.append( "setROI: wrong syntax, %s" % (self.dev[ 'name']))
            return

        self.dev[ 'proxy'].rois = roiArr
        return
            
class deviceCommands( QtGui.QMainWindow):
    def __init__( self, dev, logWidget, parent = None):
        super( deviceCommands, self).__init__( parent)
        self.parent = parent
        self.dev = dev
        self.setWindowTitle( "Commands of %s" % self.dev[ 'name'])
        self.logWidget = logWidget
        w = QtGui.QWidget()
        self.layout_v = QtGui.QVBoxLayout()
        w.setLayout( self.layout_v)
        self.setCentralWidget( w)
        alias_l = QtGui.QLabel( self.dev[ 'name'])
        name_l = QtGui.QLabel( "%s/%s" % (self.dev[ 'hostname'], self.dev[ 'device']))
        layout_h = QtGui.QHBoxLayout()
        layout_h.addWidget( alias_l)
        layout_h.addWidget( name_l)
        self.layout_v.addLayout( layout_h)
        self.layout_grid = QtGui.QGridLayout()
        self.layout_v.addLayout( self.layout_grid)

        self.fillCommands()
            
        #
        # Menu Bar
        #
        self.menuBar = QtGui.QMenuBar()
        self.setMenuBar( self.menuBar)
        self.fileMenu = self.menuBar.addMenu('&File')
        self.exitAction = QtGui.QAction('E&xit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect( self.cb_closeMotorAttr)
        self.fileMenu.addAction( self.exitAction)


        if self.dev[ 'module'].lower() == "oms58":
            self.miscMenu = self.menuBar.addMenu('&Misc')
            self.blackBoxAction = QtGui.QAction( 'BlackBox', self)        
            self.blackBoxAction.triggered.connect( self.cb_blackBox)
            self.miscMenu.addAction( self.blackBoxAction)

        #
        # the activity menubar: help and activity
        #
        self.menuBarActivity = QtGui.QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarActivity, QtCore.Qt.TopRightCorner)

        self.helpMenu = self.menuBarActivity.addMenu('Help')
        self.helpCommand = self.helpMenu.addAction(self.tr("Widget"))
        self.helpCommand.triggered.connect( self.cb_helpCommand)

        self.activityIndex = 0
        self.activity = self.menuBarActivity.addMenu( "_")

        #
        # Status Bar
        #
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar( self.statusBar)

        self.exit = QtGui.QPushButton(self.tr("E&xit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        QtCore.QObject.connect( self.exit, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_closeMotorAttr)
        self.exit.setShortcut( "Alt+x")

        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect( self.cb_refreshCommands)
        self.updateTimer.start( definitions.TIMEOUT_REFRESH)

    def cb_helpCommand( self):
        w = helpBox.HelpBox( self, self.tr("Help Commands"), self.tr(
            "<h3>Commands</h3>"
            "<ul>"
            "<li> Arrays elements are separated by commas"
            "</ul>"
                ))
        w.show()

    def cb_refreshCommands( self):
        pass


    def getCommandInfoList( self): 
        '''
        return the list of commands info blocks
        '''
        commandInfoList = self.dev[ 'proxy'].command_list_query()
        return commandInfoList

    def fillCommands( self): 
        count = 0
        self.commandInfoList = self.getCommandInfoList()

        self.commandDct = {}
        #
        # if we have many attributes, we have to create 2 'columns'
        #
        columnOffset = 0
        splitNo = len( self.commandInfoList)
        if len( self.commandInfoList) > 10:
            splitNo = math.ceil( len( self.commandInfoList)/2.)

        for commandInfo in self.commandInfoList:
            nameBtn = utils.QPushButtonTK( commandInfo.cmd_name)
            nameBtn.setToolTip( "In: %s\nOut:%s" % (commandInfo.in_type_desc, commandInfo.out_type_desc))
            self.layout_grid.addWidget( nameBtn, count, 0 + columnOffset)
            
            line = None
            if commandInfo.in_type != PyTango.CmdArgType.DevVoid:
                line = QtGui.QLineEdit()
                line.setAlignment( QtCore.Qt.AlignRight)
                self.layout_grid.addWidget( line, count, 1 + columnOffset)

            nameBtn.mb1.connect( self.make_cb_command( commandInfo, line))

            count += 1
            #
            # we don't want to reset the count, if there is only one 
            # command column. Otherwise the 'Reply' will be
            # put with count == 0
            #
            if splitNo != len( self.commandInfoList) and \
               count >= splitNo and columnOffset == 0: 
                columnOffset += 4
                count = 0

        self.replyLabel = QtGui.QLabel( "Reply:")
        self.layout_grid.addWidget( self.replyLabel, count, 0, 1, 2)


        return 

    def make_cb_command( self, commandInfo, line):
        def cb():
            try:
                if commandInfo.in_type == PyTango.CmdArgType.DevVoid:
                    reply = self.dev[ 'proxy'].command_inout( commandInfo.cmd_name)
                elif commandInfo.in_type == PyTango.CmdArgType.DevBoolean:
                    if line.text().lower() == "false": 
                        t = False
                    elif line.text().lower() == "true": 
                        t = True
                    reply = self.dev[ 'proxy'].command_inout( commandInfo.cmd_name, t)
                elif commandInfo.in_type == PyTango.CmdArgType.DevDouble or \
                     commandInfo.in_type == PyTango.CmdArgType.DevFloat:
                    reply = self.dev[ 'proxy'].command_inout( commandInfo.cmd_name, float( line.text()))
                elif commandInfo.in_type == PyTango.CmdArgType.DevLong or \
                     commandInfo.in_type == PyTango.CmdArgType.DevULong or \
                     commandInfo.in_type == PyTango.CmdArgType.DevLong64 or \
                     commandInfo.in_type == PyTango.CmdArgType.DevULong64 or \
                     commandInfo.in_type == PyTango.CmdArgType.DevShort or \
                     commandInfo.in_type == PyTango.CmdArgType.DevUShort:
                    reply = self.dev[ 'proxy'].command_inout( commandInfo.cmd_name, int( line.text()))
                elif commandInfo.in_type == PyTango.CmdArgType.DevVarDoubleArray or \
                     commandInfo.in_type == PyTango.CmdArgType.DevVarFloatArray:
                    lst = [ float( n) for n in line.text().split( ',')]
                    reply = self.dev[ 'proxy'].command_inout( commandInfo.cmd_name, lst)
                elif commandInfo.in_type == PyTango.CmdArgType.DevString:
                    reply = self.dev[ 'proxy'].command_inout( commandInfo.cmd_name, str( line.text()))
                elif commandInfo.in_type == PyTango.CmdArgType.DevVarStringArray:
                    lst = line.text().split( ',')
                    reply = self.dev[ 'proxy'].command_inout( commandInfo.cmd_name, lst)
                elif commandInfo.in_type == PyTango.CmdArgType.DevVarLongArray or \
                     commandInfo.in_type == PyTango.CmdArgType.DevVarLong64Array or \
                     commandInfo.in_type == PyTango.CmdArgType.DevVarShortArray or \
                     commandInfo.in_type == PyTango.CmdArgType.DevVarUShortArray or \
                     commandInfo.in_type == PyTango.CmdArgType.DevVarULongArray or \
                     commandInfo.in_type == PyTango.CmdArgType.DevVarULong64Array or \
                     commandInfo.in_type == PyTango.CmdArgType.DevVarCharArray:
                    lst = [int( n) for n in line.text().split( ',')]
                    reply = self.dev[ 'proxy'].command_inout( commandInfo.cmd_name, lst)
                else:
                    print "make_cb_command: need to implement %s" % repr( commandInfo.in_type)
                    return
            except Exception, e:
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "make_cb_command: %s, %s" % (self.dev[ 'name'], repr(e)), 
                                           QtGui.QMessageBox.Ok)
                return

            if line is not None:
                line.clear()

            self.replyLabel.setText( "Reply: %s" % repr( reply))
            return 

        return cb

    def getAttrInfoList( self): 
        '''
        return the list of attribute info blocks
        '''
        attrOms = [ 'State', 'Status', 'Position', 'UnitLimitMin', 'UnitLimitMax', 'UnitBacklash', 'UnitCalibration',
                    'StepPositionController', 'StepPositionInternal',
                    'SlewRate', 'SlewRateMin', 'SlewRateMax', 'BaseRate',
                    'Conversion', 'Acceleration', 
                    #'StepBacklash', 'StepLimitMin', 'StepLimitMax', 
                    'SettleTime',
                    'CwLimit', 'CcwLimit', 'FlagProtected', 'FlagCheckZMXActivated', 'WriteRead']
        attrTip551 = [ 'State', 'Status', 'Voltage', 'VoltageMax', 'VoltageMin']
        attrVfcAdc = [ 'State', 'Status', 'Counts', 'Value', 'Gain', 'Offset', 'Polarity']
        attrPilcVfcAdc = [ 'State', 'Status', 'Counts', 'Value', 'Polarity']
        attrMCA_8701 = [ 'State', 'Status', 'DataLength', 'NbRois', 
                         'Counts1', 'Counts1Diff', 'ROI1',
                         'Counts2', 'Counts2Diff', 'ROI2',
                         'Counts3', 'Counts3Diff', 'ROI3',
                         'Counts4', 'Counts4Diff', 'ROI4']
        #attrMotorTango = [ 'State', 'Position', 'UnitLimitMin', 'UnitLimitMax']
        attrSpk =  [ 'State', 'Status', 'Position', 'CcwLimit', 'CwLimit', 'ConversionFactor', 'ErrorCode', 
                     'Position', 'SlewRate', 'UnitBackLash', 'UnitLimitMin', 'UnitLimitMax']
        attrMotorPool = [ 'State', 'Status', 'Position', 'Backlash', 'Acceleration', 'Velocity', 'Step_per_unit']

        attrExtra = ['BraggAngle', 'BraggOffset', 'BraggOffset0', 'BraggOffset1', 'BraggOffset3', 
                     'Crystal', 'ExitOffset', 'ExitOffsetC0', 'ExitOffsetC1', 'UpdateStatusRate', 'PositionSim']

        attrSelected = None

        if self.dev[ 'module'].lower() == 'oms58':
            attrSelected = attrOms
        elif self.dev[ 'module'].lower() == 'tip551':
            attrSelected = attrTip551
        elif self.dev[ 'module'].lower() == 'motor_pool':
            attrSelected = attrMotorPool
        elif self.dev[ 'module'].lower() == 'spk':
            attrSelected = attrSpk
        elif self.dev[ 'module'].lower() == 'vfcadc':
            if hasattr( self.dev[ 'proxy'], 'Gain'):
                attrSelected = attrVfcAdc
            else:
                attrSelected = attrPilcVfcAdc
        elif self.dev[ 'module'].lower() == 'mca_8701':
            attrSelected = attrMCA_8701
        #elif self.dev[ 'module'].lower() == 'motor_tango':
        #    attrSelected = attrMotorTango
        #    for a in attrExtra:
        #        if hasattr( self.motor, a):
        #            attrSelected.append( a)

        attrInfoListAll = self.dev[ 'proxy'].attribute_list_query()
        attrInfoList = []
        for attrInfo in attrInfoListAll: 
            if attrInfo.name == 'State': 
                ste = attrInfo
                continue
            if attrInfo.name == 'Status': 
                sts = attrInfo
                continue
            if attrSelected is not None: 
                if attrInfo.name not in attrSelected: 
                    continue
            attrInfoList.append( attrInfo)

        def cmpr( x, y): 
            return cmp( x.name, y.name)

        attrInfoList.sort( cmpr) 
        attrInfoList.append( ste)
        attrInfoList.append( sts)
        return attrInfoList
        
    def cb_clearError( self):
        '''
        Spk
        '''
        self.dev[ 'proxy'].ClearError()

    def cb_resetVfcAdc( self):
        self.dev[ 'proxy'].reset()

    def cb_resetAllVfcAdc( self):
        '''
        after a reset of a single channel, all readings are 0, but
        the next gate period shows that not all are really reset
        '''
        for dev in allVfcAdcs:
            dev[ 'proxy'].reset()

    def cb_initVFCADC( self):
        self.dev[ 'proxy'].InitVFCADC()

    def cb_refreshAttr( self):
        
        if self.isMinimized(): 
            return

        try: 
            stst = self.dev[ 'proxy'].state()
        except Exception, e:
            self.attrDct[ 'State'][ "w_value"].setText( "Offline")
            self.attrDct[ 'State'][ "w_value"].setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
            return 

        self.activityIndex += 1
        if self.activityIndex > (len( definitions.ACTIVITY_SYMBOLS) - 1):
            self.activityIndex = 0
        self.activity.setTitle( definitions.ACTIVITY_SYMBOLS[ self.activityIndex])

        for attrInfo in self.attrInfoList:
            #if not hasattr( self.dev[ 'proxy'], attrInfo.name) and attrInfo.name.find( 'ROI') != 0: 
            if attrInfo.name.lower() not in dir( self.dev[ 'proxy']) and attrInfo.name.find( "ROI") != 0: 
                continue

            if attrInfo.name.lower() == "writeread":
                continue
                
            w_value = self.attrDct[ attrInfo.name][ "w_value"]
            if w_value is None:
                continue
            #
            # ROIs
            #
            if attrInfo.name == 'ROI1' or attrInfo.name == 'ROI2' or attrInfo.name == 'ROI3' or attrInfo.name == 'ROI4':
                w_value.setText( "%s" % self.getROI( attrInfo.name))
                continue
            if attrInfo.data_format == PyTango.AttrDataFormat.IMAGE:
                w_value.setText( "Image")
                continue
            if attrInfo.data_format == PyTango.AttrDataFormat.SPECTRUM:
                w_value.setText( "Spectrum")
                continue

            try: 
                a = self.dev[ 'proxy'].read_attribute( attrInfo.name)
            except Exception, e:
                w_value.setText( "Failed")
                continue
            #
            # Boolean
            #
            if attrInfo.data_type == PyTango.CmdArgType.DevBoolean:
                w_value.setText( "%s" % str( a.value))
            #
            # Double
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevDouble:
                w_value.setText( "%g" % a.value)
            #
            # Long
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevLong:
                w_value.setText( "%d" % a.value)
                if attrInfo.name.lower() == "cwlimit":
                    if a.value == 1:
                        w_value.setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
                    else:
                        w_value.setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
                if attrInfo.name.lower() == "ccwlimit":
                    if a.value == 1:
                        w_value.setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
                    else:
                        w_value.setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
            #
            # Short
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevShort:
                w_value.setText( "%d" % a.value)
            #
            # UShort
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevUShort:
                w_value.setText( "%d" % a.value)
            #
            # ULong
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevULong:
                w_value.setText( "%d" % a.value)
            #
            # String
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevString:
                w_value.setText( "%s" % a.value)
            #
            # State
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevState:
                w_value.setText( "%s" % a.value)
                if a.value == PyTango.DevState.MOVING:
                    w_value.setStyleSheet( "background-color:%s;" % definitions.BLUE_MOVING)
                elif a.value == PyTango.DevState.ON:
                    w_value.setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
                else:
                    w.value.setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
            else:
                w_value.setText( "unknown")

    def getROI( self, roiName):
        try:
            roiArr2D = self.dev[ 'proxy'].rois
            NbRois = self.dev[ 'proxy'].NbRois
        except Exception, e:
            self.logWidget.append( "getROI: failed for %s" % (dev[ 'fullName']))
            utils.ExceptionToLog( e, logWidget)
            return 
        roiArr = []
        for elm in roiArr2D[0]:
            roiArr.append( elm)
        for elm in roiArr2D[1]:
            roiArr.append( elm)
        #
        # p.rois = [[1000,2000, 2500, 2600],[1015,2018, 2515, 2615]]
        #
        # In [30]: p.rois
        # Out[30]: 
        # array([[1000, 2000, 2500, 2600],
        #        [1015, 2018, 2515, 2615]], dtype=int32)
        #
        if NbRois > 0 and roiName.lower() == 'roi1':
            argout = "%d, %d" % (roiArr[0], roiArr[1])
        elif NbRois > 1 and roiName.lower() == 'roi2':
            argout = "%d, %d" % (roiArr[2], roiArr[3])
        elif NbRois > 2 and roiName.lower() == 'roi3':
            argout = "%d, %d" % (roiArr[4], roiArr[5])
        elif NbRois > 3 and roiName.lower() == 'roi4':
            argout = "%d, %d" % (roiArr[6], roiArr[7])
        else:
            argout = "n.a."
            
        return argout
    #
    # the closeEvent is called when the window is closed by 
    # clicking the X at the right-upper corner of the frame
    #
    def closeEvent( self, e):
        self.cb_closeMotorAttr()
        #e.ignore()

    def cb_closeMotorAttr( self):
        self.updateTimer.stop()
        self.close()


    def cb_helpAttrOms58( self):
        w = helpBox.HelpBox( self, self.tr("Help Attributes"), self.tr(
            "<h3>Attributes</h3>"
            "<ul>"
            "<li> Position (cal.): Calibrates the motor, the motor position is calibrated to the "
            "user supplied value. The user is prompted for confirmation."
            "<li> StepPositionController/Internal: the command setStepRegister is used to set " 
            "the internal and controller register. The position does not change."
            "</ul>"
                ))
        w.show()

    def cb_helpAttrSpk( self):
        w = helpBox.HelpBox( self, self.tr("Help widget"), self.tr(
            "<ul>"
            "<li> use 'online -tki' for more details"
            "<li> Error code"
            "<ul>"
            "<li> 0 no error"
            "<li> 1 emergency off"
            "<li> 2 unexpected limit switch (wrong direction)"
            "<li> 3 at limit when switched on"
            "<li> 4 both limit switches fired"
            "<li> 5 reference move stopped by limit switch"
            "<li> 6 reference move: wrong limit"
            "<li> 7 backlash greater than 1"
            "<li> 8 inconsistent limits"
            "<li> 9 hardware error( Schrittmotorklemme)"
            "<li> 10 encoder error (misaligned?)"
            "<li> 11 error during init"
            "</ul>"
            "</ul>"
                ))
        w.show()
    def cb_helpAttrVfcAdc( self):
        w = helpBox.HelpBox( self, self.tr("Help widget"), self.tr(
            "<ul>"
            "<li> Polarity: 1 or 0"
            "<li> ResetAll: after a reset of a single channel, all readings are 0, but"
            "the next gate period shows that not all are really reset"
            "</ul>"
                ))
        w.show()

    def cb_helpBlackBox( self):
        w = helpBox.HelpBox( self, self.tr("Help BlackBox"), self.tr(
            "<h3>BlackBox</h3>"
            "The Black Box contents is written to the log widget. "
            "This features finds connected clients."
                ))
        w.show()
    def cb_helpWriteRead( self):
        w = helpBox.HelpBox( self, self.tr("Help WriteRead"), self.tr(
            "<h3>WriteRead</h3>"
            "The input string is sent to the motor and the result "
            "is printed in the log widget. The server inserts an axis specification "
            "at the beginning of the string."
            "<hr>"
            "<br>"
            "<b>RP</b> Request position"
            "<br>"
            "<b>RE</b> Request encoder"
            "<br>"
            "<b>LO12345</b> Load motor position"
            "<br>"
            "<b>LP12345</b> Load motor and encoder position"
            "<br>"
            "<b>LPE12345</b> Load encoder position, independent of motor position"
            "<br>"
            "<b>CL?</b> Query closed loop state"
            "<br>"
            "<b>SI</b> Stop"
            "<br>"
            "<b>MA12345;GO;SI</b> Move absolute, set DONE when finished"
            "<br>"
            "<b>VL4321</b> Set slew rate"
            "<br>"
            "<b>VL?</b> Query slew rate"
                ))
        w.show()
        
    def cb_recentWrites( self):
        lst = self.dev[ 'proxy'].recentwrites
        self.logWidget.append('---')
        self.logWidget.append( "%s" % self.dev[ 'name'])
        for line in lst:
            if line.find('Empty') == -1:
                self.logWidget.append( line)
        
    def cb_blackBox( self):
        lst = self.dev[ 'proxy'].black_box( 100)
        self.logWidget.append('---')
        self.logWidget.append( "%s" % self.dev[ 'name'])
        for line in lst:
            if line.find('Empty') == -1:
                self.logWidget.append( line)

    def cb_applyDeviceAttributes( self):
        count = 0
        #
        # check, whether there is some input at all
        #
        for attrInfo in self.attrInfoList:
            line = self.attrDct[ attrInfo.name][ "w_line"]
            if line is None:
                continue
            if len(line.text()) > 0:
                count += 1
                attrFound = attrInfo
        if count == 0:
            self.logWidget.append( "motorAttr.cb_apply: no input")
            return 
        #
        # More than one input: clear the input lines
        #
        if count > 1:
            for attrInfo in self.attrInfoList:
                line = self.attrDct[ attrInfo.name][ "w_line"]
                if line is None:
                    continue
                line.clear()
            self.logWidget.append( "motorAttr.cb_apply: more that one input")
            return

        attrInfo = attrFound
        line = self.attrDct[ attrInfo.name][ "w_line"]
        #
        #
        #
        if attrInfo.name.lower() == 'roi1' or attrInfo.name.lower() == 'roi2' or \
           attrInfo.name.lower() == 'roi3' or attrInfo.name.lower() == 'roi4':
            temp = line.text()
            line.clear()
            self.setROI( attrInfo.name, temp)
            return
        #
        # WriteRead is a command, not an attribute
        #
        if attrInfo.name == "WriteRead":
            temp = line.text()
            try:
                reply = self.dev[ 'proxy'].command_inout( "WriteRead", str(temp))
            except Exception, e:
                self.logWidget.append( "%s: %s causes an error" % (self.dev[ 'name'], str(temp)))
                utils.ExceptionToLog( e, self.logWidget)
                line.clear()
                return 
            self.logWidget.append( "%s:%s -> %s" % (self.dev[ 'name'], temp, reply))
            line.clear()
            return
            self.logWidget.append( "%s:%s -> %s" % (self.dev[ 'name'], temp, reply))
            line.clear()
            return

        if attrInfo.name.lower() == 'position':
            reply = QtGui.QMessageBox.question(self, 
                                               'YesNo', 
                                               "Calibrate %s/%s from %g to %s" % (self.dev[ 'hostname'], 
                                                                                  self.dev[ 'device'], 
                                                                                  getPosition( self.dev), line.text()), 
                                               QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if reply != QtGui.QMessageBox.Yes:
                self.logWidget.append( "Calibration aborted")
                line.clear()
                return 
            definitions.calibrate( self.dev, float( line.text()), self.logWidget)
            line.clear()
            return 

        if attrInfo.name.lower() == 'positionsim':
            self.dev[ 'proxy'].positionsim = float( line.text())
            self.logWidget.append( "ResultSim\n%s" % (  repr(self.dev[ 'proxy'].resultsim)))
            line.clear()
            return 
            
        if attrInfo.name.lower() == "steppositioncontroller" or \
           attrInfo.name.lower() == "steppositioninternal":
            if self.dev[ 'proxy'].FlagClosedLoop:
                if self.dev[ 'proxy'].FlagClosedLoop == 1:
                    QtGui.QMessageBox.critical(self, 'Error', 
                                               "%s/%s, register cannot be changed, if a motor is in ClosedLoop" % (self.dev[ 'hostname'], self.dev[ 'device']),
                                               QtGui.QMessageBox.Ok)
                    line.clear()
                    return
            reply = QtGui.QMessageBox.question(self, 
                                               'YesNo', 
                                               "SetStepRegister (internal and controller) of %s/%s to %s (position does not change)" % (self.dev[ 'hostname'], 
                                                                                   self.dev[ 'device'], 
                                                                                   line.text()),
                                               QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if reply != QtGui.QMessageBox.Yes:
                self.logWidget.append( "SetStepRegister: abortet")
                line.clear()
                return 
            try:
                self.dev[ 'proxy'].command_inout( "SetStepRegister", int( line.text()))
            except Exception, e:
                self.logWidget.append( "%s: failed to SetStepRegister to %d" % 
                                       (self.dev[ 'name'], int( line.text())))
                utils.ExceptionToLog( e, self.logWidget)
                
            line.clear()
            return 
            
        temp = line.text()
        try:
            if attrInfo.data_type == PyTango.CmdArgType.DevBoolean:
                if temp.lower() == "false": 
                    t = False
                elif temp.lower() == "true": 
                    t = True
                self.dev[ 'proxy'].write_attribute( attrInfo.name, t)
            elif attrInfo.data_type == PyTango.CmdArgType.DevLong:
                self.dev[ 'proxy'].write_attribute( attrInfo.name, int(temp))
            elif attrInfo.data_type == PyTango.CmdArgType.DevDouble:
                self.dev[ 'proxy'].write_attribute( attrInfo.name, float(temp))
            elif attrInfo.data_type == PyTango.CmdArgType.DevFloat:
                self.dev[ 'proxy'].write_attribute( attrInfo.name, float(temp))
            elif attrInfo.data_type == PyTango.CmdArgType.DevString:
                self.dev[ 'proxy'].write_attribute( attrInfo.name, temp)
            elif attrInfo.data_type == PyTango.CmdArgType.DevULong:
                self.dev[ 'proxy'].write_attribute( attrInfo.name, int(temp))
            elif attrInfo.data_type == PyTango.CmdArgType.DevShort:
                self.dev[ 'proxy'].write_attribute( attrInfo.name, int(temp))
            elif attrInfo.data_type == PyTango.CmdArgType.DevUShort:
                self.dev[ 'proxy'].write_attribute( attrInfo.name, int(temp))
            else:
                print "dataType not identified", attrInfo.data_type
        except Exception, e:
            self.logWidget.append( "%s: failed to set attr. %s to %s" % 
                                   (self.dev[ 'name'], attrInfo.name, repr( temp)))
            utils.ExceptionToLog( e, self.logWidget)
            
        line.clear()

    def setROI( self, roiName, temp):
        try:
            #
            # this is what we receive: 
            # roiArr: array([[101, 102, 201], [202, 301, 302]], dtype=int32)
            #
            roiArr = self.dev[ 'proxy'].rois
            NbRois = self.dev[ 'proxy'].NbRois
        except Exception, e:
            self.logWidget.append( "setROI: failed for %s" % (dev[ 'fullName']))
            utils.ExceptionToLog( e, logWidget)
            return 

        if len( roiArr.shape) != 2:
            self.logWidget.append( "setROI: len(roiArr.shape) != 2, instead %d" % 
                                   (len( roiArr.shape)))
            return

        #
        # this is what we send
        # p.rois = [[101, 102, 201, 202, 301, 302]]
        #
        roiArr = [np.concatenate( (roiArr[0], roiArr[1]))]
            
        #
        # 1000, 1200
        #
        lst = temp.split( ',')
        if len( lst) != 2:
            self.logWidget.append( "setROI: wrong syntax, %s" % (self.dev[ 'name']))
        
        if NbRois > 0 and roiName.lower() == 'roi1':
            roiArr[0][0] = int( lst[0])
            roiArr[0][1] = int( lst[1])
        elif NbRois > 1 and roiName.lower() == 'roi2':
            roiArr[0][2] = int( lst[0])
            roiArr[0][3] = int( lst[1])
        elif NbRois > 2 and roiName.lower() == 'roi3':
            roiArr[0][4] = int( lst[0])
            roiArr[0][5] = int( lst[1])
        elif NbRois > 3 and roiName.lower() == 'roi4':
            roiArr[0][6] = int( lst[0])
            roiArr[0][7] = int( lst[1])
        else:
            self.logWidget.append( "setROI: wrong syntax, %s" % (self.dev[ 'name']))
            return

        self.dev[ 'proxy'].rois = roiArr
        return
            
        
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

class motorEncAttributes( QtGui.QMainWindow):
    def __init__( self, dev, logWidget, parent = None):
        super( motorEncAttributes, self).__init__( parent)
        self.dev = dev
        self.parent = parent
        self.setWindowTitle( "%s/%s" % (dev[ 'hostname'], dev[ 'device']))
        self.logWidget = logWidget
        w = QtGui.QWidget()
        self.layout_v = QtGui.QVBoxLayout()
        w.setLayout( self.layout_v)
        self.setCentralWidget( w)
        alias_l = QtGui.QLabel( self.dev[ 'name'])
        name_l = QtGui.QLabel( "%s/%s" % (self.dev[ 'hostname'], self.dev[ 'device']))
        layout_h = QtGui.QHBoxLayout()
        layout_h.addWidget( alias_l)
        layout_h.addWidget( name_l)
        self.layout_v.addLayout( layout_h)
        self.layout_grid = QtGui.QGridLayout()
        self.layout_v.addLayout( self.layout_grid)
        count = 0
        self.attrs = ['State',
                      'Position',
                      'PositionEncoder',
                      'PositionEncoderRaw',
                      'StepPositionController',
                      'HomePosition',
                      'FlagEncoderHomed',
                      'FlagClosedLoop',
                      'FlagUseEncoderPosition',
                      'ConversionEncoder',
                      'EncoderRatio',
                      'FlagInvertEncoderDirection',
                      'CorrectionGain',
                      'StepDeadBand',
                      'SlewRateCorrection',
                      'SlipTolerance']

        self.attrDct = {}
        for attr in self.attrs:
            name = QtGui.QLabel( attr)
            self.layout_grid.addWidget( name, count, 0)

            value = QtGui.QLabel()
            value.setFixedWidth( definitions.POSITION_WIDTH)
            self.layout_grid.addWidget( value, count, 1)

            extra = None
            if attr.lower() == 'positionencoderraw':
                extra = QtGui.QLabel()
                extra.setFixedWidth( 190)
                self.layout_grid.addWidget( extra, count, 2)
                
            #
            # for the encoder attributes widget the position is ro
            #
            line = None
            if attr.lower() != 'position' and \
               attr.lower() != 'steppositioncontroller':
                try:
                    attrInfo = self.dev[ 'proxy'].get_attribute_config( attr.lower())
                except Exception, e:
                    logWidget.append( "motorEncAttributes: failed to access %s" % (dev[ 'fullName']))
                    utils.ExceptionToLog( e, logWidget)
                    self.cb_closeMotorEncAttr
                    return 
                if attrInfo.writable == PyTango._PyTango.AttrWriteType.READ_WRITE:
                    line = QtGui.QLineEdit()
                    line.setAlignment( QtCore.Qt.AlignRight)
                    self.layout_grid.addWidget( line, count, 2)
            self.attrDct[ attr] = { "w_value": value, "w_line": line, "w_extra": extra}
            count += 1

        hBox = QtGui.QHBoxLayout()

        self.home = QtGui.QPushButton(self.tr("Home")) 
        self.home.setToolTip( "Start the homing procedure. See Help-Homing for explanations.")
        hBox.addWidget( self.home)
        QtCore.QObject.connect( self.home, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_home)

        self.setFlagHomed = QtGui.QPushButton(self.tr("Set FlagEncoderHomed")) 
        self.setFlagHomed.setToolTip( "Sets the home flag. Makes sense only, if the VME stayed powered since the last homing.")
        hBox.addWidget( self.setFlagHomed)
        QtCore.QObject.connect( self.setFlagHomed, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_setFlagHomed)

        self.caliEnc = QtGui.QPushButton(self.tr("Cali Enc.")) 
        self.caliEnc.setToolTip( "Loads the encoder (LPE) with a value that is calculated using the unit position,\nthe home position and the encoder conversion. Used, if homing is not an option. \n\nWarning: Make sure that the motor position is well-defined (backlash-correct). This is\ngenerally the case after nomally completed moves, but not, if the last movement\nhas been interrupted. In this case things can be settled by executing a move ")
        hBox.addWidget( self.caliEnc)
        QtCore.QObject.connect( self.caliEnc, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_caliEnc)

        self.alignRegAndEnc = QtGui.QPushButton(self.tr("AlignRegAndEncs")) 
        self.alignRegAndEnc.setToolTip( "Sets the step registers, internal and controller, \nto be consistent with the encoder reading. \nMay change UnitCalibration. \nThe position does not change.\nUsed to prepare closed-loop without homing, \nsee Help-Closing the Loop")
        hBox.addWidget( self.alignRegAndEnc)
        QtCore.QObject.connect( self.alignRegAndEnc, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_alignRegAndEnc)

        self.layout_v.addLayout( hBox)


        #
        # Menu Bar
        #
        self.menuBar = QtGui.QMenuBar()
        self.setMenuBar( self.menuBar)
        self.fileMenu = self.menuBar.addMenu('&File')
        self.exitAction = QtGui.QAction('E&xit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect( self.cb_closeMotorEncAttr)
        self.fileMenu.addAction( self.exitAction)

        #
        # the activity menubar: help and activity
        #
        self.menuBarActivity = QtGui.QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarActivity, QtCore.Qt.TopRightCorner)

        self.helpMenu = self.menuBarActivity.addMenu('Help')
        self.helpActionEncoderAttributes = self.helpMenu.addAction(self.tr("Encoder Attributes"))
        self.helpActionEncoderAttributes.triggered.connect( self.cb_helpEncoderAttributes)
        self.helpActionHoming = self.helpMenu.addAction(self.tr("Homing"))
        self.helpActionHoming.triggered.connect( self.cb_helpHoming)
        self.helpActionClosedLoop = self.helpMenu.addAction(self.tr("Closing the Loop"))
        self.helpActionClosedLoop.triggered.connect( self.cb_helpEncoderClosedLoop)
        self.helpActionErrors = self.helpMenu.addAction(self.tr("Errors"))
        self.helpActionErrors.triggered.connect( self.cb_helpEncoderErrors)

        self.activityIndex = 0
        self.activity = self.menuBarActivity.addMenu( "_")

        #
        # Status Bar
        #
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar( self.statusBar)

        self.apply = QtGui.QPushButton(self.tr("Apply")) 
        self.apply.setToolTip("Reads the entry widgets and executes the corresponding update.")
        self.statusBar.addPermanentWidget( self.apply) # 'permanent' to shift it right
        QtCore.QObject.connect( self.apply, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_applyMotorEncAttr)
        self.apply.setShortcut( "Alt+a")
        self.apply.setText( "&Apply")

        self.exit = QtGui.QPushButton(self.tr("Exit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        QtCore.QObject.connect( self.exit, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_closeMotorEncAttr)
        self.exit.setShortcut( "Alt+x")
        self.exit.setText( "E&xit")

        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect( self.cb_refreshEncAttr)
        self.updateTimer.start( definitions.TIMEOUT_REFRESH)
        
        
    def cb_refreshEncAttr( self): 

        if self.isMinimized(): 
            return

        try: 
            stst = self.dev[ 'proxy'].state()
        except Exception, e:
            self.attrDct[ 'State'][ "w_value"].setText( "Offline")
            self.attrDct[ 'State'][ "w_value"].setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
            return 

        self.activityIndex += 1
        if self.activityIndex > (len( definitions.ACTIVITY_SYMBOLS) - 1):
            self.activityIndex = 0
        self.activity.setTitle( definitions.ACTIVITY_SYMBOLS[ self.activityIndex])

        for attr in self.attrs:
            #
            # [line, attr, attrInfo, value]
            #
            attrInfo = self.dev[ 'proxy'].get_attribute_config( attr.lower())
            if self.attrDct[ attr][ "w_value"] is None:
                continue
            if attrInfo is None:
                continue    
            if attr == "PositionEncoder":
                if self.dev[ 'proxy'].FlagEncoderHomed == 0:
                    self.attrDct[ attr][ "w_value"].setText( "Not homed")
                    continue
            try:
                a = self.dev[ 'proxy'].read_attribute( attr)
            except Exception, e:
                self.logWidget.append( "%s: failed to read attr. %s" % 
                                       (self.dev[ 'name'], attr))
                utils.ExceptionToLog( e, self.logWidget)

            #
            # Double
            #
            if attrInfo.data_type == PyTango.CmdArgType.DevDouble:
                self.attrDct[ attr][ "w_value"].setText( "%g" % a.value)
            #
            # Long
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevLong:
                self.attrDct[ attr][ "w_value"].setText( "%d" % a.value)
            #
            # State
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevState:
                self.attrDct[ attr][ "w_value"].setText( "%s" % a.value)
                if a.value == PyTango.DevState.MOVING:
                    self.attrDct[ attr][ "w_value"].setStyleSheet( "background-color:%s;" % definitions.BLUE_MOVING)
                elif a.value == PyTango.DevState.ON:
                    self.attrDct[ attr][ "w_value"].setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
                else:
                    self.attrDct[ attr][ "w_value"].setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
            else:
                self.attrDct[ attr][ "w_value"].setText( "unknown")
            
            if attr.lower() == 'positionencoderraw':
                temp = float( self.dev[ 'proxy'].positionencoderraw)*self.dev[ 'proxy'].conversion/self.dev[ 'proxy'].conversionencoder
                
                self.attrDct[ attr][ "w_extra"].setText( "Enc*ER: %d" % int( temp))
                

    #
    # the closeEvent is called when the window is closed by 
    # clicking the X at the right-upper corner of the frame
    #
    def closeEvent( self, e):
        self.cb_closeMotorEncAttr()

    def cb_closeMotorEncAttr( self): 
        self.updateTimer.stop()
        self.close()
        

    def cb_helpEncoderErrors(self):
        w = helpBox.HelpBox( self, self.tr("Help encoder errors"), self.tr(
            "\
The error Message<br>\
MotName, encoderRatio != 1 (XXX) and NOT closedLoop, changed ER to 1. \
occurs mostly because the motor slipped.<br>\
Consider to increase the SlipTolerance. \
"
                ))
        w.show()
           
    def cb_helpEncoderAttributes(self):
        w = helpBox.HelpBox( self, self.tr("Help Encoder Attributes"), self.tr(
            "\
<p>\
The attributes mentioned here come into effect when the loop is closed, \
except FlagInvertEncoderDirection.\
<p>\
<b>Correction Gain</b>(aka HG - hold gain): [1,32000], e.g. 100<br>\
OmsMaxV manual (HG - stepper hold gain): 'The parameter should be set experimentally \
by increasing it until the system is unstable then reducing it slightly below the \
threshold of stability. Factory default: 1<br>\
'Stability' can be sensed by listening to the motor or by watching the motor position. \
If the position keeps jumping forth and back, although the target position has been \
reached, the motor is unstable. If the value is too low, the motor needs a long time \
to reach the target position.\
<p>\
<b>StepDeadBand</b>: e.g. 2. <br>\
OmsMaxV manual on HD (stepper hold deadband): 'If the encoder count is within this \
distance of target, it is considered in position and no further correction will be made.'\
<p>\
<b>SlewRateCorrection</b>: must be non-zero, the maximum is the motor slew rate.<br> \
The maximum velocity to be used during position correction.<br>\
SlewCorr = CorrGain*PositionError, but less than SlewRateCorrection.\
<p>\
<b>SlipTolerance</b>: typically 100 or 1000.<br>\
Closed loop movements have to terminate, if the axis \
slips. Otherwise the motor moves into the limit switch, if it looses the encoder \
signal. In case SlitTolarance is too low, every movement is interrupted by the slip \
condition. If it is much too low, esp. below the DeadBand, the slip condition is \
detected also when the motor stands still.\
<p>\
<b>FlagInvertEncoderDirection</b>: if set, the encoder direction is changed. \
This fixes the bug that the encoderRatio must not be negative. After the \
flag is set, the sign of the encoderConversion has to be changed.\
<p>\
            <b>EncoderRatio (ER)</b>: conversion/conversionEncoder, a read-only parameter, valid in closed loop operation (otherwise ER == 1.), \
must not be negative, see FlagInvertEncoderDirection.\
"
                ))
        w.show()
        
    def cb_helpEncoderClosedLoop(self):
#<a href='http://hasyweb.desy.de/services/computing/hardware/node56.html'>Closed Loop Operation</a>\
        w = helpBox.HelpBox( self, self.tr("Help Closing the Loop"), self.tr(
            "\
<h3>Closing the Loop</h3><p>\
<b>Warning:</b> Exit the closed loop mode \
before disconnecting the encoder cables.<p>\
During closed loop operation the motor controller card minimizes \
the difference between encoder reading and step position.\
<ol>\
<li> The encs and the steps have to have identical offsets, in other words: \
the Home position and the UnitCalibration have to be the same.\
<li> EncoderRatio=Conversion/ConversionEncoder takes into account the different magnitudes of the conversion factors. \
<li> FlagInvertEncoderDirection: the Oms closed loop algorithm does not like negative \
EncoderRatios. To avoid this, you may have to set this flag to 1 \
and change the sign of the encoder conversion factor.\
<li> The loop can be closed, if the position and positionEncoder are close to each other \
and the registers are consistent, meaning that Enc*ER has to be close to the \
StepPositionController.\
</ol>\
The procedure for closing the loop:\
<ul>\
\
<li> Set CorrectionGain, StepDeadband, SlewRateCorrection, SlipTolerance as \
described in a separate Help text.\
<li> <b>If the homing procedure can be executed</b>: if possible, execute the homing procedure as \
described in Help-Homing.<br>\
Note: The home flag is cleared when the Tango server is re-started.\
\
<li> <b>If the homing procedure cannot be executed</b>: \
<ul>\
<li>Press the 'Set FlagEncoderHomed'. This is possible without loosing accuracy, \
as long as the VME stayed powered after the last homing procedure.\
<li>Press 'Cali Enc.' to calibrate the encoder position to the motor position.\
<li>Press 'AlignRegAndEncs' to make the step position consistent with the encoder \
            reading. Generally this will change the UnitCalibration, but not the position.\
</ul>\
<li> The widget displays a quantity Enc*ER=. The value should be close to the step \
register. 'Close' means within DeadBand*EncoderRatio.<br>\
Warning: a calibration (which can only be done in open-loop mode) changes the UnitCalibration of \
the motor creating a difference to the home position of the encoder. In this case the user has to \
CaliEnc and AlignWithEnc again. The same applies to reset-motor-step-position commands.\
\
<li> Move the motor to ensure that the encoder position and the motor postion are more or \
less identical and that the step register and the encoder raw position are \
consistent. Enc*ER has to be close to the StepPositionController. \
\
<li> If the encoder counts and the steps have the same direction, you may close the loop now. \
Whether or not the steps and the encoder counts have the same direction can be checked \
by moving the motor. Compare StepPositionController and PositionEncoder.\
\
<li> If steps and encoder counts have the opposite direction:\
<ul>\
<li> Set the FlagInvertEncoderDirection to 1\
<li> Change the sign of the encoder conversion.\
<li> Move the motor to ensure that the position and the encoder position are \
more or less identical.\
</ul>\
<li> Close the loop by setting FlagClosedLoop to 1, \
The closed loop is active after the next move.\
<li> Closed loop operation needs to be enabled after the server was re-started\
</ul>"
        ))
        w.show()

    def cb_helpHoming(self):
        w = helpBox.HelpBox(self, self.tr("Homing"), self.tr(
            "<h3>Homing</h3><p>"
            "<b>Warning</b>: The homing of a motor involves the risk that the motor moves all "
            "the way to the limit switches. Software limits are ignored during the homing procedure. "
            "Make sure that the limit switches are correctly cabled.<p>"
            "The homing procedure, step by step:"
            "<ul>"
            "<li> make sure that the FlagEncoder property (Tango server) is set and that "
            "it has the value 1. If you have to create this property or change its value, "
            "the Tango server has to be restarted."
            "<li> move the motor a little bit forth and back to check that PositionEncoderRaw changes."
            "<li> set the correct encoder conversion factor. This is a possible procedure:"
            "<ul>"
            "<li> move the motor to position 0."
            "<li> set the home position to 0."
            "<li> set the internal and controller step register to 0."
            "<li> clear the encoder position by clicking on Cali Enc."
            "<li> set the encoder conversion factor to 1"
            "<li> move the motor to 1 units."
            "<li> the encoder raw position gives the encoder conversion factor. "
            "There may be tiny deviations between the actual value and the true value due to hardware "
            "imperfections, e.g. if the encoder raw position is 19988 the true conversion factor is most likely 20000."
            "<li> set the encoder conversion factor."
            "<li> If the encoder conversion factor and the conversion factor have different signs, "
            "set the FlagInvertEncoderDir to 1 and change the sign of the encoder conversion factor. "
            "This fixes the bug that the encoderRatio must not be negative."
            "</ul>"
            "<li> move back to 0. Check whether the encoder position is 0 and the encoder raw position is 0."
            "<li> suppose the backlash is greater than 0: move the motor to a position below the home position. "
            "If you have no idea where the home position is, search it while standing in front of the axis. "
            "The encoder LED changes its colour when moving over the home position. If you have no clear "
            "indication where the home position is, ask an expert."
            "<li> make sure that the backlash is sufficiently large. It is a frequent error that the backlash is too small."
            "<li> start the motor homing sequence by clicking the Home button. While the motor is homed, software "
            "limits are ignored. The motor moves until it senses home (reference mark) or hits a limit switch. "
            "If a limit switch is hit, the direction of the motion is reversed to search for home. If the second "
            "limit switch is hit, the sequence is terminated."
            "<li> if the homing procedure was not successfull but the motor stopped near the home position, "
            "this is most likely because the backlash was too small."
            "<li> the motor is homed now but the encoder position is meaningless, since the correct "
            "home position has not been set yet. You have to determine the current motor position somehow "
            "and set the home position accordingly."
            "<li> set the correct motor unit limits. In general the homing procedure changes them. "
            "That is because the step register is cleared when the motor moves over the reference position. "
            "However, the limit re-adjustment needs to be done only once after the first homing procedure of a motor."
            "</ul>"

        ))
        w.show()

    def cb_home( self):
        reply = QtGui.QMessageBox.question(self, 'YesNo', "Really home %s/%s" % ( self.dev[ 'hostname'], self.dev[ 'device']), 
                                           QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply != QtGui.QMessageBox.Yes:
            self.logWidget.append( "Homing aborted")
        else:
            if self.dev[ 'proxy'].unitBacklash == 0.:
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "%s/%s UnitBacklash == 0" % (self.dev[ 'hostname'], self.dev[ 'device']), 
                                           QtGui.QMessageBox.Ok)
                return
                
            try:
                self.dev[ 'proxy'].movehome()
            except Exception, e:
                self.logWidget.append( "")
                self.logWidget.append( "%s: homing failed" % (self.dev[ 'name']))
                utils.ExceptionToLog( e, self.logWidget)
                QtGui.QMessageBox.critical(self, 'Error', 
                                           "%s/%s Homing failed, see log widget" % (self.dev[ 'hostname'], self.dev[ 'device']), 
                                           QtGui.QMessageBox.Ok)
           
    def cb_setFlagHomed( self):
        self.dev[ 'proxy'].flagencoderhomed = 1
           
    def cb_caliEnc( self):
        self.dev[ 'proxy'].calibrateencoder()
           
    def cb_alignRegAndEnc( self):
        if self.dev[ 'proxy'].FlagClosedLoop == 1:
            QtGui.QMessageBox.critical(self, 'Error', 
                                       "%s/%s, register cannot be changed, if a motor is in ClosedLoop" % (self.dev[ 'hostname'], self.dev[ 'device']),
                                       QtGui.QMessageBox.Ok)
            return
            
        homePos = self.dev[ 'proxy'].homePosition
        unitPos = self.dev[ 'proxy'].position
        conv = self.dev[ 'proxy'].conversion
        steps = (unitPos - homePos)*conv
        try:
            self.dev[ 'proxy'].command_inout( "SetStepRegister", steps)
        except Exception, e:
            self.logWidget.append( "%s: failed to SetStepRegister to %d" % 
                                   (self.dev[ 'name'], steps))
            utils.ExceptionToLog( e, self.logWidget)

    def cb_applyMotorEncAttr( self):
        count = 0
        #
        # how many input lines are filled?
        #
        for attr in self.attrs:
            line = self.attrDct[ attr][ "w_line"]
            if line is None:
                continue
            if len(line.text()) > 0:
                count += 1
                attrFound = attr
        if count == 0:
            return 
        if count > 1:
            for attr in self.attrs:
                line = self.attrDct[ attr][ "w_line"]
                if line is None:
                    continue
                line.clear()
            return

        attr = attrFound
        line = self.attrDct[ attr][ "w_line"]
        attrInfo = self.dev[ 'proxy'].get_attribute_config( attr.lower())
        temp = line.text()
        try:
            if attrInfo.data_type == PyTango.CmdArgType.DevLong:
                self.dev[ 'proxy'].write_attribute( attr, int(temp))
            elif attrInfo.data_type == PyTango.CmdArgType.DevDouble:
                self.dev[ 'proxy'].write_attribute( attr, float(temp))
            elif attrInfo.data_type == PyTango.CmdArgType.DevFloat:
                self.dev[ 'proxy'].write_attribute( attr, float(temp))
            elif attrInfo.data_type == PyTango.CmdArgType.DevString:
                self.dev[ 'proxy'].write_attribute( attr, temp)
            else:
                print "dataType not identified", attrInfo.data_type
        except Exception, e:
            self.logWidget.append( "%s: failed to set attr. %s to %s" % 
                                   (self.dev[ 'name'], attr, repr( temp)))
            utils.ExceptionToLog( e, self.logWidget)
            
        line.clear()

class motorZmxAttributes( QtGui.QMainWindow):
    def __init__( self, dev, logWidget, parent = None):
        super( motorZmxAttributes, self).__init__( parent)
        self.dev = dev
        self.parent = parent
        self.setWindowTitle( dev[ 'zmxdevice'])
        self.logWidget = logWidget
        w = QtGui.QWidget()
        self.layout_v = QtGui.QVBoxLayout()
        w.setLayout( self.layout_v)
        self.setCentralWidget( w)
        nameZMX = self.dev[ 'zmxdevice']
        if not nameZMX.find( "10000:"):
            nameZMX = "%s/%s" % (self.dev[ 'hostname'], self.dev[ 'zmxdevice'])
        
        try:
            self.zmx = PyTango.DeviceProxy( "%s" % nameZMX)
            self.zmx.state()
        except Exception, e:
            self.logWidget.append( "%s, failed to create proxy" % nameZMX)
            utils.ExceptionToLog( e, self.logWidget)

            QtGui.QMessageBox.critical(self, 'Error', 
                                       "%s failed to create proxy" % (nameZMX), 
                                       QtGui.QMessageBox.Ok)
            
            self.close()
            return
        name_l = QtGui.QLabel( nameZMX)
        layout_h = QtGui.QHBoxLayout()
        layout_h.addWidget( name_l)
        layout_h.addStretch()            
        self.layout_v.addLayout( layout_h)
        self.layout_grid = QtGui.QGridLayout()
        self.layout_v.addLayout( self.layout_grid)

        count = 0
        #
        # need this array because we want the attrs to be ordered
        #
        self.attrs = [ 'State',
                       'AxisName',
                       'RunCurrent',
                       'StopCurrent',
                       'StepWidth',
                  #'DelayTime',
                       'StepWidthStr',
                       'PreferentialDirection',
                       'Deactivation', 
                       'Temperature',
                  #'PowerStageStatus',
                  #'Error',  
                  #'IntermediateVoltage',
                  #'Channel_rd', 
                  #'InputLogicLevel',
                  #'Overdrive', 
                  #'OperationMode',
                  #'DeactivationStr',
                  #'PreferentialDirectionStr',
                  #'InputLogicLevelStr',
                  #'OverdriveStr',
                  #'OperationModeStr',
                  #'VersionPS',
                  #'VersionFPGA',
                  #'PathOutputFiles',
                  #'FlagNotErrorZMXConnection',
                  #'ErrorZMXConnection',
                  #'IntermediateVoltageInfo',
                  #'DelayTimeInfo',
                  #'FlagThreadRunning',
                  #'PowerStageStatusInt',
              ]
        toolTipDct = { 'State': "The device state",
                  'AxisName': "string", 
                  'RunCurrent': "0.1 - 5 A, if SB is active", 
                  'StopCurrent': "50% of RunCurrent, if SB is not active", 
                  'StepWidth': "Set and write value from 0 to 13. In StepWidthStr one can read the real step width value:\n0 = 1/1, 1 = 1/2, 2 = 1/2.5, 3 = 1/4, 4 = 1/5, 5 = 1/8, 6 = 1/10, 7 = 1/16, 8 = 1/20, 9 = 1/32, 10 = 1/64, 11 = 1/128, 12 = 1/256, 13 = 1/512 ", 
                  #'DelayTime': "Set value from 0 to 15. Read value in ms:\n0=1, 1=2,2=4,3=6,4=8,5=10,6=12,7=14,8=16,9=20,10=40,\n11=60,12=100, 13=200, 14=500, 15=1000\n ", 
                  'StepWidthStr': "string", 
                  'PreferentialDirection': "0 or 1", 
                       'Deactivation': "0: is active, 1: not active", 
                  'Temperature': "float", 
                  #'PowerStageStatus': "string", 
                  #'Error': "string", 
                  #'IntermediateVoltage': "loat", 
                  #'Channel_rd': "Read the Power Stage channel from the Channel property ", 
                  #'InputLogicLevel': "long", 
                  #'Deactivation': "long", 
                  #'Overdrive': "long", 
                  #'OperationMode': "long", 
                  #'DeactivationStr': "string", 
                  #'PreferentialDirectionStr': "string", 
                  #'InputLogicLevelStr': "string", 
                  #'OverdriveStr': "string", 
                  #'OperationModeStr': "string", 
                  #'VersionPS': "Software version of the power stage ", 
                  #'VersionFPGA': "Software version of the FPGA", 
                  #'PathOutputFiles': "string", 
                  #'FlagNotErrorZMXConnection': "bool", 
                  #'ErrorZMXConnection': "string", 
                  #'IntermediateVoltageInfo': "string", 
                  #'DelayTimeInfo': "string", 
                  #'FlagThreadRunning': "long", 
                  #'PowerStageStatusInt': "long", 
              }
        self.attrDct = {}
        for attr in self.attrs:
            name = QtGui.QLabel( attr)
            name.setToolTip( toolTipDct[ attr])
            self.layout_grid.addWidget( name, count, 0)

            value = QtGui.QLabel()
            value.setFixedWidth( definitions.POSITION_WIDTH)
            self.layout_grid.addWidget( value, count, 1)

            attrInfo = self.zmx.get_attribute_config( attr.lower())
            line = None
            if attrInfo.writable == PyTango._PyTango.AttrWriteType.READ_WRITE:
                line = QtGui.QLineEdit()
                line.setAlignment( QtCore.Qt.AlignRight)
                self.layout_grid.addWidget( line, count, 2)
            self.attrDct[ attr] = { "w_value": value, "w_line": line}
            count += 1
        #
        # Menu Bar
        #
        self.menuBar = QtGui.QMenuBar()
        self.setMenuBar( self.menuBar)
        self.fileMenu = self.menuBar.addMenu('&File')
        self.exitAction = QtGui.QAction('E&xit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect( self.cb_closeMotorZMXAttr)
        self.fileMenu.addAction( self.exitAction)

        #
        # the activity menubar: help and activity
        #
        self.menuBarActivity = QtGui.QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarActivity, QtCore.Qt.TopRightCorner)

        self.helpMenu = self.menuBarActivity.addMenu('Help')
        self.helpActionStopCurrent = self.helpMenu.addAction(self.tr("Widget"))
        self.helpActionStopCurrent.triggered.connect( self.cb_helpStopCurrent)

        self.activityIndex = 0
        self.activity = self.menuBarActivity.addMenu( "|")

        #
        # Status Bar
        #
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar( self.statusBar)

        self.apply = QtGui.QPushButton(self.tr("Apply")) 
        self.apply.setToolTip("Reads the entry widgets and executes the corresponding update.")
        self.statusBar.addPermanentWidget( self.apply) # 'permanent' to shift it right
        QtCore.QObject.connect( self.apply, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_applyMotorZmxAttr)
        self.apply.setShortcut( "Alt+a")
        self.apply.setText( "&Apply")

        self.exit = QtGui.QPushButton(self.tr("Exit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        QtCore.QObject.connect( self.exit, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_closeMotorZMXAttr)
        self.exit.setShortcut( "Alt+x")
        self.exit.setText( "E&xit")

        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect( self.cb_refreshZMXAttr)
        self.updateTimer.start( definitions.TIMEOUT_REFRESH)

    def cb_refreshZMXAttr( self):

        if self.isMinimized(): 
            return

        try: 
            stst = self.zmx.state()
        except Exception, e:
            self.attrDct[ 'State'][ "w_value"].setText( "Offline")
            self.attrDct[ 'State'][ "w_value"].setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
            return 

        self.activityIndex += 1
        if self.activityIndex > (len( definitions.ACTIVITY_SYMBOLS) - 1):
            self.activityIndex = 0
        self.activity.setTitle( definitions.ACTIVITY_SYMBOLS[ self.activityIndex])


        for attr in self.attrs:
            #
            # [line, attr, attrInfo, value]
            #
            attrInfo = self.zmx.get_attribute_config( attr.lower())
            w_value = self.attrDct[ attr][ "w_value"]
            if w_value is None:
                continue
            if attrInfo is None:
                continue    

            a = self.zmx.read_attribute( attr)
            #
            # Double
            #
            if attrInfo.data_type == PyTango.CmdArgType.DevDouble:
                w_value.setText( "%g" % a.value)
            #
            # Float
            #
            if attrInfo.data_type == PyTango.CmdArgType.DevFloat:
                w_value.setText( "%g" % a.value)
            #
            # Long
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevLong:
                w_value.setText( "%d" % a.value)
            #
            # String
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevString:
                w_value.setText( "%s" % a.value)
            #
            # State
            #
            elif attrInfo.data_type == PyTango.CmdArgType.DevState:
                w_value.setText( "%s" % a.value)
                if a.value == PyTango.DevState.MOVING:
                    w_value.setStyleSheet( "background-color:%s;" % definitions.BLUE_MOVING)
                elif a.value == PyTango.DevState.ON:
                    w_value.setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
                else:
                    w.value.setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
            else:
                w_value.setText( "unknown")

    #
    # the closeEvent is called when the window is closed by 
    # clicking the X at the right-upper corner of the frame
    #
    def closeEvent( self, e):
        self.cb_closeMotorZMXAttr()

    def cb_closeMotorZMXAttr( self): 
        self.updateTimer.stop()
        self.close()

    def cb_helpStopCurrent(self):
        w = helpBox.HelpBox( self, title = "Help ZMX", text = self.tr( 
            "<h3> ZMX Parameters</h3>"
            "<ul>"
            "<li> RunCurrent: 0.1 - 5 A </li>"
            "<li> StopCurrent: at 50% if the service bus is inactive </li>"
            "<li> StepWidth"
              "<ul>"
              "<li> 0: 1/1"
              "<li> 1: 1/2"
              "<li> 2: 1/2.5"
              "<li> 3: 1/4"
              "<li> 4: 1/5"
              "<li> 5: 1/8"
              "<li> 6: 1/10"
              "<li> 7: 1/16"
              "<li> 8: 1/20"
              "<li> 9: 1/32"
              "<li> 10: 1/64"
              "<li> 11: 1/128"
              "<li> 12: 1/256"
              "<li> 13: 1/512"
              "</ul>"
            "</li>"
            "</ul>"
        ))
        w.show()
    #
    # zmx apply
    #
    def cb_applyMotorZmxAttr( self):
        count = 0
        #
        # check, whether there is some input at all
        #
        for attr in self.attrs:
            line = self.attrDct[ attr][ "w_line"]
            if line is None:
                continue
            if len(line.text()) > 0:
                count += 1
                attrFound = attr
        if count == 0:
            self.logWidget.append( "motorZmxAttr.cb_apply: no input")
            return 
        if count > 1:
            for attr in self.attrs:
                line = self.attrDct[ attr][ "w_line"]
                if line is None:
                    continue
                line.clear()
            self.logWidget.append( "motorZmxAttr.cb_apply: more that one input")
            return

        line = self.attrDct[ attrFound][ "w_line"]
        attr = attrFound

        attrInfo = self.zmx.get_attribute_config( attr.lower())
        temp = line.text()
        try:
            if attrInfo.data_type == PyTango.CmdArgType.DevLong:
                self.zmx.write_attribute( attr, int(temp))
            elif attrInfo.data_type == PyTango.CmdArgType.DevDouble:
                self.zmx.write_attribute( attr, float(temp))
            elif attrInfo.data_type == PyTango.CmdArgType.DevFloat:
                self.zmx.write_attribute( attr, float(temp))
            elif attrInfo.data_type == PyTango.CmdArgType.DevString:
                self.zmx.write_attribute( attr, temp)
            else:
                print "dataType not identified", attrInfo.data_type

        except Exception, e:
            self.logWidget.append( "%s: failed to set attr. %s to %s" % 
                                   (self.dev[ 'name'], attr, repr( temp)))
            self.logWidget.append( "%s" % repr( e)) 
            
        line.clear()

