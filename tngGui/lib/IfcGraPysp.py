#!/usr/bin/env python
'''
this module actracts Spectra, PySpectra
'''
import Spectra
import PySpectra as pysp

lineColorArr = [ 
    'RED', 
    'GREEN',
    'BLUE',
    'YELLOW',
    'CYAN',
    'MAGENTA',
    'BLACK',
    'WHITE', 
    'NONE', 
]

useSpectra = False

def setSpectra( flag):
    global useSpectra
    
    if flag:
        useSpectra = True
    else:
        useSpectra = False
    return 

def getSpectra(): 
    return useSpectra
 
def cls():
    if useSpectra:
        Spectra.gra_command( "cls/graphic")
    else:
        pysp.cls()
    return 

def close(): 

    if useSpectra:
        pass
    else:
        pysp.close()
    return 

def createHardCopy( printer = None, flagPrint = False, format = 'DINA4'):
    '''
    create postscript/pdf file and send it to the printer
    '''
    fName = None
    if useSpectra:
        Spectra.gra_command(" set 0.1/border=1")
        Spectra.gra_command(" postscript/%s/redisplay/nolog/nocon/print/lp=%s" % (format, prnt))
        Spectra.gra_command(" set 0.1/border=0")
        Spectra.gra_command(" postscript/redisplay/nolog/nocon/print/lp=%s" % printer)
    else:
        fName = pysp.createPDF( flagPrint = flagPrint, format = format)
        #
        # necessary to bring pqt and mpl again in-sync, mind lastIndex
        #
        pysp.cls()
        pysp.display()

    return fName

def deleteScan( scan): 
    
    if useSpectra:
        del scan
    else: 
        pysp.delete( [scan.name])
        pysp.cls()

    return 

def writeFile( nameGQE):

    if useSpectra:
        Spectra.gra_command( "write/fio %s" % nameGQE)
    else:
        pysp.write( [nameGQE])

    return 

def Scan( **hsh):

    if useSpectra:
        scan = Spectra.SCAN( name = hsh[ 'name'],
                             start = hsh[ 'start'], 
                             stop = hsh[ 'stop'],
                             np = hsh[ 'np'],
                             xlabel = hsh[ 'xlabel'],
                             ylabel = hsh[ 'ylabel'],
                             comment = hsh[ 'comment'],
                             NoDelete = hsh[ 'NoDelete'],
                             colour = hsh[ 'colour'],
                             at = hsh[ 'at'])
    else:
        scan = pysp.Scan( name = hsh[ 'name'],
                          xMin = hsh[ 'start'], 
                          xMax = hsh[ 'stop'],
                          nPts = hsh[ 'np'],
                          xLabel = hsh[ 'xlabel'],
                          yLabel = hsh[ 'ylabel'],
                          color = lineColorArr[ hsh[ 'colour']], 
                          autoscaleX = True, 
                          autoscaleY = True,
                          motorList = hsh[ 'motorList'], 
                          logWidget = hsh[ 'logWidget'], 
                          at = hsh[ 'at'])

        scan.addText( text = hsh[ 'comment'], x = 0.95, y = 0.95, hAlign = 'right', vAlign = 'top', 
                      color = 'black', fontSize = None)
            
    return scan
    


