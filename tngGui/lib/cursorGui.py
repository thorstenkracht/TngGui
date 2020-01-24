#!/usr/bin/env python

from taurus.external.qt import QtGui, QtCore 
import PyTango
import math, sys, os
import HasyUtils, Spectra
import utils, definitions

class CursorGUI( QtGui.QMainWindow):
    def __init__( self, nameGQE, dev, logWidget = None, parent = None):
        super( CursorGUI, self).__init__( parent)
        self.setWindowTitle( "Cursor")
        self.dev = dev
        self.move( 10, 510)
        self.nameGQE = nameGQE
        self.parent = parent
        self.scan = Spectra.SCAN( name = self.nameGQE, NoDelete = True)
        #
        # if not enough points: self.close() cannot be called directly
        # because it is executed by the event-loop. use the single
        # timer instead
        #
        if self.scan.getCurrent() < 2:
            QtGui.QMessageBox.about(self, self.tr("Message"), self.tr("Cursor: too few points"))
            QtGui.QTimer.singleShot( 100, self.cb_closeCursorGUI)
            return
        Spectra.gra_command( "set/nolog inter off")
        Spectra.gra_command( "display/single %s" % self.nameGQE)
            
        self.centralWidget = QtGui.QWidget()
        self.setCentralWidget( self.centralWidget)

        self.layout_v = QtGui.QVBoxLayout()
        self.centralWidget.setLayout( self.layout_v)
        #
        # Name, NP, Lin/Log
        # 
        layout_h = QtGui.QHBoxLayout()
        self.w_nameGQE = QtGui.QLabel( nameGQE)
        self.w_np = QtGui.QLabel( "123")
        self.w_linlog = QtGui.QPushButton( "Lin/Log")
        QtCore.QObject.connect( self.w_linlog, QtCore.SIGNAL( utils.fromUtf8("clicked()")), self.cb_linlog)
        layout_h.addWidget( self.w_nameGQE)
        layout_h.addWidget( self.w_np)
        layout_h.addStretch()            
        layout_h.addWidget( self.w_linlog)
        self.layout_v.addLayout( layout_h)
        #
        # linear regression
        # 
        self.w_linear = QtGui.QLabel( "Linear:")
        self.layout_v.addWidget( self.w_linear)
        #
        # motor frame 
        #
        layout_h = QtGui.QHBoxLayout()
        self.layout_v.addLayout( layout_h)
        layout_h.addWidget( QtGui.QLabel( "%s" % self.dev[ 'name']))
        self.w_position = QtGui.QLabel()
        self.w_position.setFixedWidth( definitions.POSITION_WIDTH)
        self.w_position.setFrameStyle( QtGui.QFrame.Panel | QtGui.QFrame.Sunken)

        layout_h.addWidget( self.w_position)
        layout_h.addStretch()            
        self.w_moveToCursor = QtGui.QPushButton( "Move2Cursor")
        self.w_moveToCursor.setToolTip( "Move %s to the cursor position" % self.dev[ 'name'])
        
        layout_h.addWidget( self.w_moveToCursor)
        self.w_moveToCursor.clicked.connect( self.cb_moveToCursor)
        self.w_stopMove = QtGui.QPushButton( "StopMove")
        self.w_stopMove.setToolTip( "Stop %s" % self.dev[ 'name'])
        layout_h.addWidget( self.w_stopMove)
        self.w_stopMove.clicked.connect( self.cb_stopMove)
            
        #
        # Cursor frame
        #
        frame = QtGui.QFrame()
        frame.setFrameShape( QtGui.QFrame.Box)
        self.layout_v.addWidget( frame)
        self.layout_frame_v = QtGui.QVBoxLayout()
        frame.setLayout( self.layout_frame_v)
        layout_h = QtGui.QHBoxLayout()
        self.layout_frame_v.addLayout( layout_h)
        layout_v = QtGui.QVBoxLayout()
        layout_h.addLayout( layout_v)
        layout_v.addWidget( QtGui.QLabel( "Index"))
        self.w_index = QtGui.QLabel( "123")
        layout_v.addWidget( self.w_index)
        # x
        layout_v = QtGui.QVBoxLayout()
        layout_h.addLayout( layout_v)
        layout_v.addWidget( QtGui.QLabel( "x"))
        self.w_x = QtGui.QLabel( "0.")
        layout_v.addWidget( self.w_x)
        # y
        layout_v = QtGui.QVBoxLayout()
        layout_h.addLayout( layout_v)
        layout_v.addWidget( QtGui.QLabel( "y"))
        self.w_y = QtGui.QLabel( "100.")
        layout_v.addWidget( self.w_y)
        # x - x0
        layout_v = QtGui.QVBoxLayout()
        layout_h.addLayout( layout_v)
        layout_v.addWidget( QtGui.QLabel( "x-x0"))
        self.w_xx0 = QtGui.QLabel( "1.")
        layout_v.addWidget( self.w_xx0)
        
        # set X0
        self.setx0 = QtGui.QPushButton( "Set X0")
        self.setx0.setToolTip( "Set x0 to display x - x0")
        layout_h.addWidget( self.setx0)
        QtCore.QObject.connect( self.setx0, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_setx0)
        #
        # the slider
        #
        self.w_slider = QtGui.QSlider( 1)
        self.w_slider.installEventFilter( self)
        self.w_slider.setToolTip( "Key_Right/Key_Left are active, if the slider has the focus (is highlighted).\nUse Alt-o to set the focus to the slider.")
        self.layout_frame_v.addWidget( self.w_slider)
        QtCore.QObject.connect( self.w_slider, QtCore.SIGNAL(utils.fromUtf8("valueChanged(int)")), self.cb_slider)
        #
        # setXMin, left, right, setXMax
        #
        layout_h = QtGui.QHBoxLayout()
        self.layout_frame_v.addLayout( layout_h)
        self.setxmin = QtGui.QPushButton( "Set XMin")
        self.setxmin.setToolTip( "Zoom, set lower window limit")
        layout_h.addWidget( self.setxmin)
        QtCore.QObject.connect( self.setxmin, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_setxmin)
        layout_h.addStretch()            
        self.left = QtGui.QPushButton( "Left")
        self.left.setToolTip( "Move cursor left")
        layout_h.addWidget( self.left)
        QtCore.QObject.connect( self.left, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_cursorLeft)
        self.right = QtGui.QPushButton( "Right")
        self.right.setToolTip( "Move cursor right")
        layout_h.addWidget( self.right)
        QtCore.QObject.connect( self.right, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_cursorRight)
        layout_h.addStretch()            
        self.setxmax = QtGui.QPushButton( "Set XMax")
        self.setxmax.setToolTip( "Zoom, set upper window limit")
        layout_h.addWidget( self.setxmax)
        QtCore.QObject.connect( self.setxmax, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_setxmax)
        #
        # autoscale, ssa, display, displayAll, Back, Next
        #
        layout_h = QtGui.QHBoxLayout()
        self.layout_v.addLayout( layout_h)
        
        self.autoscale = QtGui.QPushButton( "Autoscale")
        self.autoscale.setToolTip( "Autoscale the plot, resetting window limits")
        layout_h.addWidget( self.autoscale)
        QtCore.QObject.connect( self.autoscale, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_autoscale)
        
        self.ssa = QtGui.QPushButton( "SSA")
        layout_h.addWidget( self.ssa)
        self.ssa.setToolTip( "Perform a simple-scan-analysis")
        QtCore.QObject.connect( self.ssa, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_ssa)
        
        self.w_displaySingle = QtGui.QPushButton( "Display")
        self.w_displaySingle.setToolTip( "Display single GQE")
        layout_h.addWidget( self.w_displaySingle)
        QtCore.QObject.connect( self.w_displaySingle, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_displaySingle)
        
        self.displayAll = QtGui.QPushButton( "DisplayAll")
        self.displayAll.setToolTip( "Display all GQEs")
        layout_h.addWidget( self.displayAll)
        QtCore.QObject.connect( self.displayAll, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_displayAll)
        
        layout_h.addStretch()            
        self.back = QtGui.QPushButton( "Back")
        self.back.setToolTip( "Step through GQEs, backwards")
        layout_h.addWidget( self.back)
        QtCore.QObject.connect( self.back, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_back)
        
        self.next = QtGui.QPushButton( "Next")
        self.next.setToolTip( "Step through GQEs, forwards")
        layout_h.addWidget( self.next)
        QtCore.QObject.connect( self.next, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_next)
        #
        # log widget
        #
        self.logWidget = logWidget
        if self.logWidget is None:
            self.logWidget = QtGui.QTextEdit()
            self.logWidget.setFixedHeight( 100)
            self.logWidget.setReadOnly( 1)
            self.layout_v.addWidget( self.logWidget)
        #
        self.setupNewScan()
        #
        # Menu Bar
        #
        self.menuBar = QtGui.QMenuBar()
        self.setMenuBar( self.menuBar)
        self.fillMenuBar()
        #
        # Status Bar
        #
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar( self.statusBar)
        
        self.clear = QtGui.QPushButton(self.tr("&Clear")) 
        self.clear.setToolTip( "Clear log widget")
        self.statusBar.addPermanentWidget( self.clear) # 'permanent' to shift it right
        QtCore.QObject.connect( self.clear, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_clear)
        self.clear.setShortcut( "Alt+c")
        
        self.exit = QtGui.QPushButton(self.tr("E&xit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        QtCore.QObject.connect( self.exit, QtCore.SIGNAL(utils.fromUtf8("clicked()")), self.cb_closeCursor)
        self.exit.setShortcut( "Alt+x")
        self.w_slider.setFocus()

        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect( self.cb_refreshCursor)

        self.updateTimer.start( definitions.TIMEOUT_REFRESH)

    def cb_refreshCursor( self):

        if self.isMinimized(): 
            return
        
        x = utils.getPosition( self.dev) 

        self.activityIndex += 1
        if self.activityIndex > (len( definitions.ACTIVITY_SYMBOLS) - 1):
            self.activityIndex = 0
        self.activity.setTitle( definitions.ACTIVITY_SYMBOLS[ self.activityIndex])
        
        self.w_position.setText( "%g" % x)
        if self.dev[ 'proxy'].state() == PyTango.DevState.MOVING:
            self.w_position.setStyleSheet( "background-color:%s;" % definitions.BLUE_MOVING)
        elif self.dev[ 'proxy'].state() == PyTango.DevState.ON:
            self.w_position.setStyleSheet( "background-color:%s;" % definitions.GREEN_OK)
        else:
            self.w_position.setStyleSheet( "background-color:%s;" % definitions.RED_ALARM)
        
    def eventFilter(self, obj, event):
        #
        # Only watch for specific slider keys.
        # Everything else is pass-thru
        #
        if obj is self.w_slider and event.type() == event.KeyPress:
            key = event.key()
            if key == QtCore.Qt.Key_Up:
                return True
            elif key == QtCore.Qt.Key_Down:
                return True
            elif key == QtCore.Qt.Key_Right:
                self.cb_cursorRight()
                return True
            elif key == QtCore.Qt.Key_Left:
                self.cb_cursorLeft()
                return True
            return False
        return False
        
    #
    # the closeEvent is called when the window is closed by 
    # clicking the X at the right-upper corner of the frame
    #
    def closeEvent( self, e):
        self.cb_closeCursor()

    def cb_closeCursor( self):
        self.updateTimer.stop()
        self.parent.cursorIsActive = False
        self.parent.enableInputWidgets( True)
        self.close()
         
    def fillMenuBar( self):
        #
        # --- file
        #
        self.fileMenu = self.menuBar.addMenu('&File')
        #
        # postscript
        #
        self.postscriptAction = QtGui.QAction('Postscript', self)        
        self.postscriptAction.setStatusTip('Create postscript')
        self.postscriptAction.triggered.connect( self.cb_postscript)
        self.fileMenu.addAction( self.postscriptAction)

        self.postscriptActionA6 = QtGui.QAction('Postscript A6', self)        
        self.postscriptActionA6.setStatusTip('Create postscript, A6')
        self.postscriptActionA6.triggered.connect( self.cb_postscriptA6)
        self.fileMenu.addAction( self.postscriptActionA6)
        #
        # spectra
        #
        self.spectraAction = QtGui.QAction('Spectra', self)        
        self.spectraAction.setStatusTip('Enter Spectra')
        self.spectraAction.triggered.connect( self.cb_launchSpectra)
        self.fileMenu.addAction( self.spectraAction)
        #
        # exit
        #
        self.exitAction = QtGui.QAction('E&xit', self)        
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(QtGui.QApplication.quit)
        self.fileMenu.addAction( self.exitAction)
        #
        # --- tools
        #
        self.toolMenu = self.menuBar.addMenu('&Tools')
        #
        # derivative
        #
        self.derivativeAction = QtGui.QAction('Derivative', self)        
        self.derivativeAction.setStatusTip('Calculate the derivative')
        self.derivativeAction.triggered.connect( self.cb_derivative)
        self.toolMenu.addAction( self.derivativeAction)
        #
        # antiDerivative
        #
        self.antiDerivativeAction = QtGui.QAction('AntiDerivative', self)        
        self.antiDerivativeAction.setStatusTip('Calculate the antiDerivative')
        self.antiDerivativeAction.triggered.connect( self.cb_antiDerivative)
        self.toolMenu.addAction( self.antiDerivativeAction)
        #
        # invert
        #
        self.invertAction = QtGui.QAction('Invert: y -> -y', self)        
        self.invertAction.setStatusTip('y -> -y')
        self.invertAction.triggered.connect( self.cb_invert)
        self.toolMenu.addAction( self.invertAction)
        #
        # smooth
        #
        self.smoothAction = QtGui.QAction('Smooth', self)        
        self.smoothAction.setStatusTip('Smooth')
        self.smoothAction.triggered.connect( self.cb_smooth)
        self.toolMenu.addAction( self.smoothAction)

        self.miscMenu = self.menuBar.addMenu('Misc')

        self.focusSliderAction = QtGui.QAction('F&ocus Slider', self)       
        self.focusSliderAction.triggered.connect( self.w_slider.setFocus)
        self.miscMenu.addAction( self.focusSliderAction)
        self.focusSliderAction.setShortcut( "Alt+o")
    
        self.menuBarActivity = QtGui.QMenuBar( self.menuBar)
        self.menuBar.setCornerWidget( self.menuBarActivity, QtCore.Qt.TopRightCorner)
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

    def cb_postscript(self):
        prnt = os.getenv( "PRINTER")
        if prnt is None: 
            QtGui.QMessageBox.about(self, 'Info Box', "No shell environment variable PRINTER.") 
            return

        Spectra.gra_command(" postscript/nolog/nocon/print/lp=%s" % prnt)
        self.logWidget.append( HasyUtils.getDateTime())
        self.logWidget.append(" Sent postscript file to %s" % prnt)
    
    def cb_postscriptA6(self):
        prnt = os.getenv( "PRINTER")
        if prnt is None: 
            QtGui.QMessageBox.about(self, 'Info Box', "No shell environment variable PRINTER.") 
            return

        Spectra.gra_command(" set 0.1/border=1")
        Spectra.gra_command(" postscript/dina6/nolog/nocon/print/lp=%s" % prnt)
        Spectra.gra_command(" set 0.1/border=0")
        self.logWidget.append( HasyUtils.getDateTime())
        self.logWidget.append(" Sent postscript file to %s" % prnt)
        
    def cb_derivative(self):
        #
        # make a sort because the piezo position may not be ordered
        #
        status = Spectra.gra_command(" sort %s" % (self.scan.name))
        status = Spectra.gra_command(" calc %s_D = ableit( %s)" % (self.scan.name, self.scan.name))
        if status == 0:
            self.logWidget.append("cb_derivative: 'calc %s_D = ableit( %s)' failed" % (self.scan.name, self.scan.name))
            return
            
        self.logWidget.append(" Created %s_D (ableit()), status %d" % (self.scan.name, status))
        self.scan = Spectra.SCAN( name = "%s_D" % self.scan.name, NoDelete = True)
        self.setupNewScan()

    def cb_antiDerivative(self):
        #
        # make a sort because the piezo position may not be ordered
        #
        status = Spectra.gra_command(" sort %s" % (self.scan.name))
        Spectra.gra_command(" calc %s_I = stamm( %s)" % (self.scan.name, self.scan.name))
        self.logWidget.append(" Created %s_I (stamm())" % self.scan.name)
        self.scan = Spectra.SCAN( name = "%s_I" % self.scan.name, NoDelete = True)
        self.setupNewScan()

    def cb_invert(self):
        #
        # make a sort because the piezo position may not be ordered
        #
        status = Spectra.gra_command(" sort %s" % (self.scan.name))
        Spectra.gra_command(" calc %s_M = -%s" % (self.scan.name, self.scan.name))
        self.logWidget.append(" Created %s_M (Y -> -Y)" % self.scan.name)
        self.scan = Spectra.SCAN( name = "%s_M" % self.scan.name, NoDelete = True)
        self.setupNewScan()

    def cb_smooth(self):
        #
        # make a sort because the piezo position may not be ordered
        #
        status = Spectra.gra_command(" sort %s" % (self.scan.name))
        Spectra.gra_command(" smooth/s=1 %s" % (self.scan.name))
        self.logWidget.append(" Created %s_S (smooth)" % self.scan.name)
        self.scan = Spectra.SCAN( name = "%s_S" % self.scan.name, NoDelete = True)
        self.setupNewScan()

    def setupNewScan( self):
        self.scan.x_max = self.scan.getX( self.scan.np - 1)
        self.scan.x_min = self.scan.getX( 0)
        #
        # consider this scan command: ascan exp_dmy01 1. 1.000001 10 0.1
        #
        if self.scan.x_max != 0.:
            try:
                self.precision = math.ceil( math.log10(math.fabs(self.scan.x_max/(self.scan.x_max - self.scan.x_min))))
            except Exception as e:
                self.precision = 3
        else:
            self.precision = 3
        self.scan.np_max = self.scan.np - 1
        self.scan.np_min =  0
        self.setHeader()
        self.tag = Spectra.TAG( name = self.scan.name, 
                                string = "nil",
                                frame = 1,
                                tag_type = 14,
                                distance = 0,
                                x = self.scan.getX( self.scan.index),
                                y = self.scan.getY( self.scan.index))
        if self.scan.linLog == 0:
            self.w_linlog.setText("Log")
            Spectra.gra_command( "set */y_log=0;autoscale/y")
        else:
            self.w_linlog.setText("Lin")
            Spectra.gra_command( "set */y_log=1;autoscale/y")

        self.setSliderScale()

        self.setCursorAndSlider()
        Spectra.gra_command( "cls/graphic" )
        self.cb_displaySingle()


    def setHeader( self):
        self.w_nameGQE.setText( "%s %s" % ( self.scan.slot, self.scan.name))
        self.w_np.setText( "np: %d" % self.scan.np)
        
        (sts, a) = Spectra.gra_decode_text( "linear( %s, a)" % self.scan.name)
        (sts, b) = Spectra.gra_decode_text( "linear( %s, b)" % self.scan.name)
        self.w_linear.setText( "f = a + bx,   a: %s, b %s" % (a, b))

    def setSliderScale( self):
        self.w_slider.setMinimum( self.scan.np_min)
        self.w_slider.setMaximum( self.scan.np_max)
        self.w_slider.setValue( self.scan.index)
        
    def setCursorAndSlider( self): 
        #print( "Cursor.setCursorAndSlider: x %s, y %s " %( self.scan.getX( self.scan.index), self.scan.getY( self.scan.index)))
        self.tag.configure( x = self.scan.getX( self.scan.index),
                            y = self.scan.getY( self.scan.index))
        self.w_slider.setValue( self.scan.index)
        self.w_index.setText( "%d" % self.scan.index)
        if self.precision > 5:
            self.w_x.setText( "%s" % repr(self.scan.getX( self.scan.index)))
        else:
            self.w_x.setText( "%g" % self.scan.getX( self.scan.index))
        self.w_y.setText( "%g" % self.scan.getY( self.scan.index))
        self.w_xx0.setText( "%g" % (self.scan.getX( self.scan.index) - self.scan.x0))
        self.cb_displaySingle()

    def cb_moveToCursor( self):
        posReq = self.scan.getX( self.scan.index)
        if posReq > utils.getUnitLimitMax( self.dev, self.logWidget) or posReq < utils.getUnitLimitMin( self.dev, self.logWidget):
            self.logWidget.append( "%s, requested move %g" % (self.dev[ 'name'], posReq))
            self.logWidget.append( " is outside limits %g, %g" % 
                                   (utils.getUnitLimitMin( self.dev, self.logWidget), utils.getUnitLimitMax( self.dev, self.logWidget)))
            return
        
        msg = "Move %s from %g to %g" % ( self.dev[ 'name'], 
                                          utils.getPosition( self.dev),
                                          posReq)
        reply = QtGui.QMessageBox.question(self, 'YesNo', msg, 
                                           QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if not reply == QtGui.QMessageBox.Yes:
            self.logWidget.append( "Cursor: move not confirmed")
        self.parent.moveTarget( posReq)

    def cb_stopMove( self):
        execStopMove( self.dev)
        self.logWidget.append( "Cursor: stopping %s" % self.dev[ 'name'])

    def cb_setx0( self): 
        self.scan.x0 = self.scan.getX( self.scan.index)
        self.logWidget.append( "set x0 to %g" % self.scan.x0)
        self.setCursorAndSlider()

    def cb_cursorLeft(self):
        if self.scan.index > 0:
            self.scan.index -= 1
            self.setCursorAndSlider()
    def cb_cursorRight(self):
        if self.scan.index < (self.scan.np - 1):
            self.scan.index += 1
            self.setCursorAndSlider()

    def cb_setxmax( self): 
        self.scan.x_max = self.scan.getX( self.scan.index)
        self.scan.np_max =  self.scan.index
        self.setSliderScale()
        Spectra.gra_command( "set %s/x_max=%g;autoscale/window;display/single %s" % 
                             (self.scan.name, self.scan.x_max, self.scan.name))

    def cb_setxmin( self): 
        self.scan.x_min = self.scan.getX( self.scan.index)
        self.scan.np_min =  self.scan.index
        self.setSliderScale()
        Spectra.gra_command( "set %s/x_min=%g;autoscale/window;display/single %s" % 
                             (self.scan.name, self.scan.x_min, self.scan.name))

    def cb_autoscale(self):
        Spectra.gra_command( "autoscale")
        self.scan.x_max = self.scan.getX( self.scan.np - 1)
        self.scan.x_min = self.scan.getX( 0)
        self.scan.np_max = self.scan.np - 1
        self.scan.np_min =  0
        self.setSliderScale()
        Spectra.gra_command( "display/single %s" % self.scan.name)

    def cb_ssa( self):
        reasons = ['ok', 'np < 6', 'signal2BG', 'no y > 0', 'midpoint calc', 'midpoint calc.', 'max outside x-range']
        #SSA_REASON  0: ok, 1: np < 6, 2: stbr, 3: no y(i) > 0., 
        #            4, 5: midpoint calc, 6: max outside x-range
                    
        Spectra.gra_command( "delete/nowarn temp_fit_ssa.*")
        cmd = "create/ssa=%s/x_min=%g/x_max=%g/notext temp_fit_ssa" % (self.scan.name, 
                                                                     self.scan.x_min, 
                                                                     self.scan.x_max)
        self.logWidget.append( HasyUtils.getDateTime())
        self.logWidget.append( cmd)
        Spectra.gra_command( cmd)
        ( sts, ret) = Spectra.gra_decode_int( "SSA_STATUS")
        if ret == 0:
            ( sts, reason) = Spectra.gra_decode_int( "SSA_REASON")
            if reason < len( reasons):
                self.logWidget.append( "SSA failed, reason: %s" % reasons[reason])
            else:
                self.logWidget.append( "SSA failed, reason %d (unknown)" % reason)
        else:
            Spectra.gra_command( "deactivate %s.2" % self.scan.name)
            Spectra.gra_command( "cls/graphic" )
            Spectra.gra_command( "set/v0 %s" % self.scan.name)
            Spectra.gra_command( "set/v0 temp_fit_ssa")
            Spectra.gra_command( "display")

    def cb_displaySingle( self):
        Spectra.gra_command( "cls/graphic;display/single %s" % self.scan.name)
    def cb_displayAll( self):
        Spectra.gra_command( "cls/graphic;display/vp")
        
    def cb_back(self):
        self.scan = self.scan.back()
        self.setupNewScan()

    def cb_next(self):
        self.scan = self.scan.next()
        self.setupNewScan()

    def cb_slider( self, value): 
        #buttons = QtGui.qApp.mouseButtons()
        #if buttons == QtCore.Qt.LeftButton: print( "left")

        self.scan.index = value
        self.setCursorAndSlider()

    def cb_linlog(self):
        if self.scan.linLog == 0:
            self.scan.linLog = 1
            self.w_linlog.setText("Lin")
            Spectra.gra_command( "set */y_log=1;autoscale/y")
        else:
            self.scan.linLog = 0
            self.w_linlog.setText("Log")
            Spectra.gra_command( "set */y_log=0;autoscale/y")
        Spectra.gra_command( "cls/graphic")
        Spectra.gra_command( "cls/graphic;display")

    def cb_clear( self):
        self.logWidget.clear()
