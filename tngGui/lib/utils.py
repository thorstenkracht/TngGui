#!/usr/bin/env python

from taurus.external.qt import QtGui, QtCore 

try:
    fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def fromUtf8(s):
        return s

def getPosition( dev):
    try:
        if dev[ 'module'].lower() == 'tip551':
            argout = dev[ 'proxy'].voltage
        else:
            argout = dev[ 'proxy'].position
    except Exception, e: 
        #print "getPosition: %s, reading the position causes an error" % (dev[ 'fullName'])
        #print "%s:" % repr( e)
        argout = 123456789.
    return argout 

def getPositionString( dev):
    try:
        if dev[ 'module'].lower() == 'tip551':
            argout = "%g" % dev[ 'proxy'].voltage
        else:
            argout = "%g" % dev[ 'proxy'].position
    except: 
        argout = "None"
    return argout 

def getPositionEncoderString( dev):
    if dev[ 'module'].lower() == 'oms58':
        try:
            if dev[ 'proxy'].FlagEncoderHomed == 1:
                argout = "%g" % dev[ 'proxy'].positionencoder
            else:
                argout = "not homed"
        except: 
            argout = "exception"
    else:
        argout = "n.a."
    return argout 

#
# the following functions are called from the mainWidget(), moveMotor()
#
def calibrate( dev, newPos, logWidget):
    pOld = getPosition( dev)
    try:
        if dev[ 'module'].lower() == 'oms58':
            dev[ 'proxy'].command_inout( "Calibrate", newPos)
        elif dev[ 'module'].lower() == 'motor_pool':
            dev[ 'proxy'].command_inout( "DefinePosition", newPos)
        else:
            logWidget.append( "calibrate: failed to identify %s (%s)" % (dev[ 'module'], dev[ 'name']))

    except Exception, e:
        logWidget.append( "calibrate: failed for %s" % (dev[ 'fullName']))
        ExceptionToLog( e, logWidget)
        return 

    logWidget.append( "Calibrated %s/%s from %g to %g" % (  dev[ 'hostname'], 
                                                            dev[ 'device'], 
                                                            pOld, newPos))
    return 

def getSlewRate( dev, logWidget):
    argout = None

    if dev[ 'module'].lower() == 'tip551' or \
       dev[ 'module'].lower() == 'motor_tango':
        return None

    try:
        if dev[ 'module'].lower() == 'oms58':
            argout = dev[ 'proxy'].slewRate
        elif dev[ 'module'].lower() == 'motor_pool':
            argout = dev[ 'proxy'].Velocity
        elif dev[ 'module'].lower() == 'spk':
            argout = dev[ 'proxy'].SlewRate
        else:
            logWidget.append( "getSlewRate: failed to identify %s (%s)" % (dev[ 'module'], dev[ 'name']))

    except Exception, e:
        logWidget.append( "getSlewRate: failed to get slewRate/Velocity for %s" % (dev[ 'fullName']))
        ExceptionToLog( e, logWidget)
        return None

    # logWidget.append( "getSlewRate: %s %g" % (dev[ 'name'], argout))
    return argout

def hasSlewRate( dev, logWidget):
    argout = False

    if (dev[ 'module'].lower() == 'oms58' or
        dev[ 'module'].lower() == 'motor_pool' or
        dev[ 'module'].lower() == 'spk'):
        argout = True
    elif (dev[ 'module'].lower() == 'tip551' or
          dev[ 'module'].lower() == 'motor_tango'):
        argout = False
    else:
        logWidget.append( "hasSlewRate: failed to identify %s (%s)" % (dev[ 'module'], dev[ 'name']))

    return argout

def setSlewRate( dev, slewNew, logWidget):

    if dev[ 'module'].lower() == 'tip551' or \
       dev[ 'module'].lower() == 'motor_tango':
        return

    # logWidget.append( "setSlewRate: %s %g" % (dev[ 'name'], slewNew))

    try:
        if dev[ 'module'].lower() == 'oms58':
            dev[ 'proxy'].slewRate = slewNew
        elif dev[ 'module'].lower() == 'motor_pool':
            dev[ 'proxy'].Velocity = slewNew
        elif dev[ 'module'].lower() == 'spk':
            dev[ 'proxy'].SlewRate = slewNew
        else:
            logWidget.append( "setSlewRate: failed to identify %s (%s)" % (dev[ 'module'], dev[ 'name']))

    except Exception, e:
        logWidget.append( "setSlewRate: failed to set slewRate/Velocity for %s" % (dev[ 'fullName']))
        ExceptionToLog( e, logWidget)

    return

def getUnitLimitMax( dev, logWidget):
    try:
        if dev[ 'flagPoolMotor']:
            attrConfig = dev[ 'proxy'].get_attribute_config_ex( "Position")
            try:
                argout = float( attrConfig[0].max_value)
            except: 
                argout = 1000.
        else:
            if dev[ 'module'].lower() == 'tip551':
                argout = dev[ 'proxy'].voltagemax
            elif dev[ 'module'].lower() == 'absbox':
                argout = 1000
            else:
                argout = dev[ 'proxy'].unitlimitmax
    except Exception, e:
        logWidget.append( "getUnlitLimitMax: %s, reading the max-limit causes an error" % (dev[ 'fullName']))
        ExceptionToLog( e, logWidget)
        argout = 0.

    return argout 

def getUnitLimitMaxString( dev, logWidget):
    try:
        if dev[ 'flagPoolMotor']:
            attrConfig = str( dev[ 'proxy'].get_attribute_config_ex( "Position"))
            try:
                argout = "%g" % float( attrConfig[0].max_value)
            except: 
                argout = "1000."
        else:
            if dev[ 'module'].lower() == 'tip551':
                argout = "%g" % dev[ 'proxy'].voltagemax
            elif dev[ 'module'].lower() == 'absbox':
                argout = "1000."
            else:
                argout = "%g" % dev[ 'proxy'].unitlimitmax
    except Exception, e:
        logWidget.append( "getUnlitLimitMaxStr: %s, reading the max-limit causes an error" % (dev[ 'fullName']))
        ExceptionToLog( e, logWidget)
        argout = "None"

    return argout 

def getUnitLimitMin( dev, logWidget):
    try:
        if dev[ 'flagPoolMotor']:
            attrConfig = dev[ 'proxy'].get_attribute_config_ex( "Position")
            try:
                argout = float( attrConfig[0].min_value)
            except: 
                argout = -1000.
        else:
            if dev[ 'module'].lower() == 'tip551':
                argout = dev[ 'proxy'].voltagemin
            elif dev[ 'module'].lower() == 'absbox':
                argout = -1000
            else:
                argout = dev[ 'proxy'].unitlimitmin
    except Exception, e:
        logWidget.append( "getUnlitLimitMin: %s, reading the min-limit causes an error" % (dev[ 'fullName']))
        ExceptionToLog( e, logWidget)
        argout = 0.
        
    return argout 

def getUnitLimitMinString( dev, logWidget):
    try:
        if dev[ 'flagPoolMotor']:
            attrConfig = str(dev[ 'proxy'].get_attribute_config_ex( "Position"))
            try:
                argout = attrConfig[0].min_value
            except: 
                argout = "-1000."
        else:
            if dev[ 'module'].lower() == 'tip551':
                argout = "%g" % dev[ 'proxy'].voltagemin
            elif dev[ 'module'].lower() == 'absbox':
                argout = "-1000."
            else:
                argout = "%g" % dev[ 'proxy'].unitlimitmin
    except Exception, e:
        logWidget.append( "getUnlitLimitMinStr: %s, reading the min-limit causes an error" % (dev[ 'fullName']))
        ExceptionToLog( e, logWidget)
        argout = "None"
        
    return argout 

def getCounterValueStr( dev):
    if dev[ 'flagOffline']:
        return "Offline"

    try:
        if dev[ 'module'].lower() == 'sis3820' or \
           dev[ 'module'].lower() == 'vfcadc' or \
           dev[ 'module'].lower() == 'counter_tango':
            argout = "%g" % dev[ 'proxy'].counts
        else:
            argout = "%g" % dev[ 'proxy'].Value
    except Exception, e: 
        print "getCounterValueStr: trouble reading %s, flagging 'offline'" % dev['name']
        dev[ 'flagOffline'] = True
        argout = "Offline"
    return argout 

def getDacValue( dev):
    try:
        if dev[ 'module'].lower() == 'tip551':
            argout = dev[ 'proxy'].voltage
        else:
            argout = dev[ 'proxy'].value
    except Exception, e: 
        #print "getPosition: %s, reading the position causes an error" % (dev[ 'fullName'])
        #print "%s:" % repr( e)
        argout = 123456789.
    return argout 

def setDacValue( dev, posReq):
    if dev[ 'module'].lower() == 'tip551':
        dev[ 'proxy'].voltage = posReq
    else:
        dev[ 'proxy'].value = posReq
    return

def getUpperLimit( dev, self):
    try:
        if dev[ 'module'].lower() != 'oms58':
            return False
        if dev[ 'proxy'].conversion > 0:
            if dev[ 'proxy'].cwlimit == 1:
                return True
        else:
            if dev[ 'proxy'].ccwlimit == 1:
                return True
    except Exception, e:
        self.logWidget.append( "getUpperLimit: exception for %s, module %s" % (dev[ 'fullName'], dev[ 'module']))
        self.logWidget.append( "getUpperLimit: %s" % repr( e))
        return False
    return False

def getLowerLimit( dev, self):
    try:
        if dev[ 'module'].lower() != 'oms58':
            return False
        if dev[ 'proxy'].conversion > 0:
            if dev[ 'proxy'].ccwlimit == 1:
                return True
        else:
            if dev[ 'proxy'].cwlimit == 1:
                return True
    except Exception, e:
        self.logWidget.append( "getLowerLimit: exception for %s, module %s " % (dev[ 'fullName'], dev[ 'module']))
        self.logWidget.append( "getLowerLimit: %s" % repr( e))
        return False
    return False

def getControllerRegister( dev):
    if dev[ 'module'].lower() == 'oms58':
        argout = dev[ 'proxy'].steppositioncontroller
    else:
        argout = 0.12345
    return argout 

def setPosition( dev, posReq):
    if dev[ 'module'].lower() == 'tip551':
        dev[ 'proxy'].voltage = posReq
    else:
        dev[ 'proxy'].position = posReq
    return

def execStopMove( dev):
    if dev[ 'flagPoolMotor']:
        dev[ 'proxy'].stop()
    else:
        dev[ 'proxy'].stopMove()

def ExceptionToLog( e, logWidget):
    for arg in e.args:
        if hasattr( arg, 'desc'):
            logWidget.append( " desc:   %s" % arg.desc) 
            logWidget.append( "   origin: %s" % arg.origin)
            logWidget.append( "   reason: %s" % arg.reason)
        else:
            logWidget.append( repr( e))
    logWidget.append( "")
    return

class TMO( Exception):
    def __init__( self, *argin):
        self.value = argin
    def __str__( self): 
        return repr( self.value)

class QPushButtonTK( QtGui.QPushButton):
    mb1 = QtCore.pyqtSignal()
    mb2 = QtCore.pyqtSignal()
    mb3 = QtCore.pyqtSignal()

    def __init__( self, *args, **kwargs):
        QtGui.QWidget.__init__( self, *args, **kwargs)

    def mousePressEvent( self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.mb1.emit()
        elif event.button() == QtCore.Qt.MiddleButton:
            self.mb2.emit()
        elif event.button() == QtCore.Qt.RightButton:
            self.mb3.emit()
