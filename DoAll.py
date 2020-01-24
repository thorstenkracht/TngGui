#!/usr/bin/env python
#
import HasyUtils
import os

HOST_LIST = "/afs/desy.de/group/hasylab/Tango/HostLists/TangoHosts.lis"

def main():

    nodes = HasyUtils.readHostList( HOST_LIST)

    sz = len( nodes) 
    count = 1
    countFailed = 0
    for host in nodes:
        if not HasyUtils.checkHostRootLogin( host):
            print "-- checkHostRootLogin returned error %s" % host
            countFailed += 1
            continue
        #
        # avoid the string 'failed' because it is printed in red
        #
        if os.system( "./DoDebianInstall.pl %s" % host):
            print "Missed to update %s" % host
            countFailed += 1
            continue
        print "DoAll: %d/%d (missed %d) %s " % (count, sz, countFailed, host)
        count += 1
    if os.system( "./Update_Debian_Repo.pl"):
        print "Failed to update the debian repo"
    return

if __name__ == "__main__":
    main()
