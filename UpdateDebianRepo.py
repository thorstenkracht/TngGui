#!/usr/bin/env python
"""

./UpdateDebianRepo.py

  this file is identical in hasyutils, pySpectra, tngGui 

# root> apt-get update
# root> apt-cache policy python-pyspectra
# root> apt-get install python-pyspectra

"""
import argparse, sys, os
import HasyUtils
import handleVersion
from optparse import OptionParser

def main():

    DIR_NAME = os.getenv( "PWD").split( "/")[-1]
    if DIR_NAME == 'hasyutils': 
        PACKET_NAME = "hasyutils"
    elif DIR_NAME == 'pySpectra': 
        PACKET_NAME = "pyspectra"
    elif DIR_NAME == 'tngGui': 
        PACKET_NAME = "tnggui"
    else: 
        print( "CheckVersion.py: failed to identify %s" % DIR_NAME)
        sys.exit( 255)
    ROOT_DIR = "/home/kracht/Misc/%s" % DIR_NAME
    
    usage = "%prog -x \n" + \
            "  copies the %s python, python3 packages to the debian repos (stretch, buster)" % PACKET_NAME

    parser = OptionParser(usage=usage)
    parser.add_option( "-x", action="store_true", dest="execute", 
                       default = False, help="update %s debian package in repo" % PACKET_NAME)
    
    (options, args) = parser.parse_args()


    flagExecute = False
    if options.execute is True:
        flagExecute = True

    os.chdir( ROOT_DIR)

    #
    handleVers = handleVersion.handleVersion( ROOT_DIR)
    version = handleVers.findVersion()
    print ( "UpdateDebianPackage: version %s %s" % (version, os.getenv( "PWD")))

    for versOS in [ 'stretch', 'buster']: 

        cmd = "export GNUPGHOME=~/.gnupg-repo && reprepro -V remove %s python-%s" % (versOS, PACKET_NAME)
        print( cmd)
        if flagExecute and os.system( cmd):
            pass

        cmd = "export GNUPGHOME=~/.gnupg-repo && reprepro -V remove %s python3-%s" % (versOS, PACKET_NAME)
        print( cmd) 
        if flagExecute and os.system( cmd): 
            pass

        cmd = "export GNUPGHOME=~/.gnupg-repo && reprepro -V includedeb %s /home/kracht/Misc/%s/DebianPackages/python-%s_%s_all.deb" % \
                      (versOS, DIR_NAME, PACKET_NAME, version)
        print( cmd) 
        if flagExecute and os.system( cmd):
            print( "UpdateDebianRepo: reprepro includedeb %s failed" % versOS)
            sys.exit( 255)

        cmd = "export GNUPGHOME=~/.gnupg-repo && reprepro -V includedeb %s /home/kracht/Misc/%s/DebianPackages/python3-%s_%s_all.deb" % \
                      (versOS, DIR_NAME, PACKET_NAME, version)
        print( cmd) 
        if flagExecute and os.system( cmd):
            print( "UpdateDebianRepo: reprepro includedeb %s failed (P3)" % versOS)
            sys.exit( 255)

        cmd = "wget -q --output-document=- 'http://nims.desy.de/cgi-bin/hasylabDEBSync.cgi'"
        print( cmd) 
        if flagExecute and os.system( cmd):
            print( "UpdateDebianRepo: wget nims failed")
            sys.exit( 255)

        cmd = "cp -v /home/kracht/Misc/%s/DebianPackages/python-%s_%s_all.deb /nfs/fs/fsec/DebianPackages/%s/p" % \
                      ( DIR_NAME, PACKET_NAME, version, versOS)
        print( cmd) 
        if flagExecute and os.system( cmd):
            print( "UpdateDebianRepo: copy to stretch dir failed")
            sys.exit( 255)

        cmd = "cp -v /home/kracht/Misc/%s/DebianPackages/python3-%s_%s_all.deb /nfs/fs/fsec/DebianPackages/%s/p" % \
                      ( DIR_NAME, PACKET_NAME, version, versOS)
        print( cmd) 
        if flagExecute and os.system( cmd):
            print( "UpdateDebianRepo: copy to stretch dir failed")
            sys.exit( 255)

    print( ">>> UpdateDebianRepo.py DONE")

    if not flagExecute: 
        print( "\n")
        print( "this was just a test run, use '-x' to execute\n")
        print( "\n")

    return 

if __name__ == "__main__": 
    main()
