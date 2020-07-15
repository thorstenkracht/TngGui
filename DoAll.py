#!/usr/bin/env python
#
import HasyUtils
import os
import argparse

HOST_LIST = "/afs/desy.de/group/hasylab/Tango/HostLists/TangoHosts.lis"
PACKET_NAME = 'tnggui'

def main():
    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        description="  updates python-%s, python3-~ on all hosts from the repo" % (PACKET_NAME))
    
    parser.add_argument('-x', dest="execute", action="store_true", default = False, 
                        help='update python-%s, python3-~ on all nodes, from repo' % (PACKET_NAME))
 
    parser.add_argument('-r', dest="updateRepo", action="store_true", default = False, help='update repo first')
     
    args = parser.parse_args()

    if not args.execute:
        parser.print_help()
        return 
    
    if args.updateRepo:
        if os.system( "./UpdateDebianRepo.py -x"):
            print "Failed to update the debian repo"
            return 

    nodes = HasyUtils.readHostList( HOST_LIST)

    sz = len( nodes) 
    count = 1
    countFailed = 0
    countOffline = 0
    for host in nodes:
        if not HasyUtils.checkHostRootLogin( host):
            print "-- checkHostRootLogin returned error %s" % host
            countOffline += 1
            continue
        cmd = 'ssh -l root %s "apt-get update && apt -y install python-%s && apt install -y python3-%s && dpkg -s python-%s && dpkg -s python3-%s && echo "" > /dev/null 2>&1"' % (host, PACKET_NAME, PACKET_NAME, PACKET_NAME, PACKET_NAME)
        # print( "%s" % cmd)
        if os.system( cmd): 
            print "Failed to update %s" % host
            countFailed += 1
            continue
        else: 
            print( "Updated %s OK" % host)
        print "\nDoAll: %d/%d (offline %d, failed %d) %s \n" % (count, sz, countOffline, countFailed, host)
        count += 1
    return

if __name__ == "__main__":
    main()
