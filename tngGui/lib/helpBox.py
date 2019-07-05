#!/usr/bin/env python

from taurus.external.qt import QtGui, QtCore 

class HelpBox( QtGui.QMainWindow):
    #
    # class to display some help text.
    # Avoid QMessageBox() because this cannot be moved
    #
    def __init__( self, parent, title = "Title", text = None):
        super( HelpBox, self).__init__( parent)
        self.setWindowTitle( title)
        w = QtGui.QWidget()
        if len( text) > 1000:
            w.setMinimumWidth( 800)
            w.setMinimumHeight( 800)
        else:
            w.setMinimumWidth( 600)
            w.setMinimumHeight( 400)
        self.setCentralWidget( w)
        self.layout_v = QtGui.QVBoxLayout()
        self.textBox = QtGui.QTextEdit( self)
        #self.textBox = QtGui.QTextBrowser( self)
        #self.textBox.setOpenExternalLinks(True)
        self.textBox.insertHtml( text)
        self.textBox.setReadOnly( True)
        self.layout_v.addWidget( self.textBox)
        w.setLayout( self.layout_v)
        #
        # Status Bar
        #
        self.statusBar = QtGui.QStatusBar()
        self.setStatusBar( self.statusBar)

        self.exit = QtGui.QPushButton(self.tr("&Exit")) 
        self.statusBar.addPermanentWidget( self.exit) # 'permanent' to shift it right
        self.exit.clicked.connect( self.close)
        self.exit.setShortcut( "Alt+x")
