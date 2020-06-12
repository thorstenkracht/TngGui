#!/usr/bin python

import os, sys

rootDir = '/home/kracht/Misc'

def findVersion():
    """
    """
    try: 
        inp = open( "%s/hasyutils/versionTarBall.lis" % (rootDir), 'r')
        for line in inp.readlines():
            if line.find( "#") != -1:
                continue
            (major, minor) = line.split( ' ')[1].split( '.')
            break
    except Exception as e:
        print( "findVersion: caught an exception")
        print( repr( e))
        sys.exit( 255)
        
    return "%s.%d" % ( int( major), int( minor))

def incrementVersion():
    """
    """
    version = findVersion()

    (versionMajor, versionMinor) = version.split( '.')

    versionMinor = int( versionMinor) + 1

    try: 
        out = open( "%s/hasyutils/versionTarBall.lis" % (rootDir), 'w')
        out.write( "#\n# do not edit this file\n#\n")
        out.write( "version %d.%d\n" % ( int( versionMajor), int( versionMinor)))
        out.close()
    except Exception as e:
        print( "incrementVersion: caught an exception")
        print( repr( e))
        sys.exit( 255)
    
    return True
