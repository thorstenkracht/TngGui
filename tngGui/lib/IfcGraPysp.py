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

def cls():
    if useSpectra:
        Spectra.gra_command( "cls/graphic")
    else:
        pysp.cls()

def close(): 

    if useSpectra:
        pass
    else:
        pysp.close()

def createHardCopy( prnt):
    pass

def deleteScan( scan): 
    
    if useSpectra:
        del scan
    else: 
        pysp.delete( [scan.name])
        pysp.cls()

    return 

def writeFile( fName):
    pass

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
                          at = hsh[ 'at'])

        scan.addText( text = hsh[ 'comment'], x = 0.95, y = 0.95, hAlign = 'right', vAlign = 'top', 
                      color = 'black', fontSize = None)
            
    return scan
    


