#!/usr/bin/env python
"""
Install the python-pyspectra package on a host

./DoDebianInstall.py <hostName>

"""
import argparse, sys, os
import HasyUtils
import handleVersion

ROOT_DIR = "/home/kracht/Misc/tngGui"
PACKET_NAME = "tnggui"

def main(): 

    parser = argparse.ArgumentParser( 
        formatter_class = argparse.RawDescriptionHelpFormatter,
        usage='%(prog)s [options]', 
        description= "Install %s debian package on some host" % PACKET_NAME)
    
    parser.add_argument( 'hostName', nargs=1, default='None', help='hostname where the package is to be installed')  
    args = parser.parse_args()

    if args.hostName == "None": 
        print( "DoDebianInstall.py: specify hostname")
        sys.exit( 255)

    if len( args.hostName) != 1: 
        print( "DoDebianInstall.py: specify ONE host")
        sys.exit( 255)
        
    host = args.hostName[0]

    print( ">>> DoDebianInstall.py %s" % (host))

    os.chdir( ROOT_DIR)

    if not HasyUtils.checkHostOnline( host): 
        print( "DoDebinaInstall.py: %s is not online " % host)
        sys.exit( 255)

    if not HasyUtils.checkHostRootLogin( host): 
        print( "DoDebinaInstall.py: %s no root login " % host)
        sys.exit( 255)

    #
    # read the version
    #
    handleVers = handleVersion.handleVersion( ROOT_DIR)
    version = handleVers.findVersion()

    argout = os.popen('ssh root@%s "uname -v"' % host).read()
    argout = argout.strip()

    if argout.find( 'Debian') == -1: 
        print( "DoDebinaInstall.py: %s does not run Debian " % host)
        sys.exit( 255)

    debName3 = "python3-%s_%s_all.deb" % (PACKET_NAME, version)
    debName = "python-%s_%s_all.deb" % (PACKET_NAME, version)
    #
    # copy the package to the install host
    #
    if os.system( "scp ./DebianPackages/%s root@%s:/tmp" % (debName, host)):
        print( "trouble copying the package to %s" % host)
        sys.exit( 255)
    if os.system( "scp ./DebianPackages/%s root@%s:/tmp" % (debName3, host)):
        print( "trouble copying the package to %s" % host)
        sys.exit( 255)
    #
    # remove the existing package, may not exist on the host
    #
    if os.system( 'ssh -l root %s "dpkg -r python-%s > /dev/null 2>&1"' % (host, PACKET_NAME)): 
        pass
    if os.system( 'ssh -l root %s "dpkg -r python3-%s > /dev/null 2>&1"' % (host, PACKET_NAME)): 
        pass
    #
    # install the new package
    #
    if os.system( 'ssh -l root %s "dpkg -i /tmp/%s"' % ( host, debName)): 
        print( "trouble installing the package on %s" % host)
        sys.exit( 255)
    if os.system( 'ssh -l root %s "dpkg -i /tmp/%s"' % ( host, debName3)): 
        print( "trouble installing the package on %s" % host)
        sys.exit( 255)
    #
    # delete the deb file
    #
    if os.system( 'ssh -l root %s "/bin/rm /tmp/%s"' % (host, debName)):
        print( "trouble removing deb file on %s" % host)
        sys.exit( 255)
    if os.system( 'ssh -l root %s "/bin/rm /tmp/%s"' % (host, debName3)):
        print( "trouble removing deb file on %s" % host)
        sys.exit( 255)

    print( ">>> DoDebianInstall.py %s DONE" % host)
    return 

if __name__ == "__main__": 
    main()
