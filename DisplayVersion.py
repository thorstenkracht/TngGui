#!/usr/bin/env python
"""
this file identical in hasyutils, pySpectra and tngGui
"""
import HasyUtils
import os, sys

HOST_LIST = "/afs/desy.de/group/hasylab/Tango/HostLists/TangoHosts.lis";

def main():

    DIR_NAME = os.getenv( "PWD").split( "/")[-1]
    if DIR_NAME == 'hasyutils': 
        PACKET_NAME = "hasyutils"
    elif DIR_NAME == 'pySpectra': 
        PACKET_NAME = "pyspectra"
    elif DIR_NAME == 'tngGui': 
        PACKET_NAME = "tnggui"
    else: 
        print( "DisplayVersion.py: failed to identify %s" % DIR_NAME)
        sys.exit( 255)
    ROOT_DIR = "/home/kracht/Misc/%s" % DIR_NAME

    nodes = HasyUtils.readHostList( HOST_LIST)

    sz = len( nodes) 
    count = 1
    for host in nodes:
        if not HasyUtils.checkHostRootLogin( host):
            print "-- checkHostRootLogin returned error %s" % host
            continue
        ret = os.popen( "ssh root@%s \"dpkg -l python-%s 2>/dev/null\"" % (host, PACKET_NAME)).read()
        lst = ret.split( '\n')
        for line in lst:
            if line.find( "python-%s" % PACKET_NAME) > 0:
                lst1 = line.split()
                print "%d/%d: %s, python-%s %s" % (count, sz, host, PACKET_NAME, lst1[2])
        ret = os.popen( "ssh root@%s \"dpkg -l python3-%s 2>/dev/null\"" % (host, PACKET_NAME)).read()
        lst = ret.split( '\n')
        for line in lst:
            if line.find( "python3-%s" % PACKET_NAME) > 0:
                lst1 = line.split()
                print "%d/%d: %s, python3-%s %s" % (count, sz, host, PACKET_NAME, lst1[2])
        count += 1
    return

if __name__ == "__main__":
    main()
