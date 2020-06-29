#!/usr/bin/env python
"""
this scripts creates the debian package for Python2 and Python3
"""
import os, sys
import handleVersion
import argparse

ROOT_DIR = "/home/kracht/Misc/tngGui"
PACKET_NAME = "tnggui"

def main(): 

    os.chdir( "%s" % (ROOT_DIR))
    
    print( ">>> DoDebianBuild.py \n")

    if not os.path.exists( "/tmp/DebianPackages"): 
        if os.mkdir( "/tmp/DebianPackages"):
            printf( "Failed  to create /tmp/DebianPackages")
            sys.exit( 255)

    if not os.path.exists( "%s/DebianPackages" % (ROOT_DIR)): 
        if os.mkdir( "%s/DebianPackages" % (ROOT_DIR)):
            printf( "Failed  to create %s/DebianPackages" % ROOT_DIR)
            sys.exit( 255)

    #
    # cleanup
    #
    print( ">>> cleanup")
    if os.system( "/bin/rm -rf /tmp/DebianPackages/python*-%s*" % PACKET_NAME):
        print( "trouble cleaning up")
        sys.exit( 255)
    #
    # increment the version 
    #
    handleVersion.incrementVersion()
    version = handleVersion.findVersion()

    #
    # create the source distribution
    #
    print( ">>> Create the source distribution")
    if os.system( "cd %s && python setup.py sdist" % (ROOT_DIR)):
        print( "trouble running setup sdist")
        sys.exit( 255)
    #
    # cp the tarball
    #
    print( ">>> copy the tarBall to ../DebianPackages") 
    if os.system( "cp %s/dist/python-%s-%s.tar.gz /tmp/DebianPackages" % 
                  (ROOT_DIR, PACKET_NAME, version)):
        print( "failed to copy tar file")
        sys.exit( 255)
    #
    # unpack the tarball
    #
    print( ">>> unpack the tarBall") 
    if os.system( "cd /tmp/DebianPackages && tar xvzf python-%s-%s.tar.gz" % (PACKET_NAME, version)):
        print( "failed to unpack the tar file")
        sys.exit( 255)
    #
    # rename the tarball (is this necessary?)
    #
    print( ">>> rename the tarBall") 
    if os.system( "cd /tmp/DebianPackages && mv python-%s-%s.tar.gz python-%s_%s.orig.tar.gz" % 
                  (PACKET_NAME, version, PACKET_NAME, version)):
        print( "failed to rename the tar file")
        sys.exit( 255)
    #
    # dh_make, prepare debian packaging, creates the debian folder
    #
    # -n, --native
    #
    # Create a native Debian packages, i.e. do not generate a .orig archive, since 
    # it will be generated when building with dpkg-buildpackage. The version number 
    # will not have a Debian revision number (e.g. -1) appended to it.
    #
    # -s, --single
    #
    # Automatically set the package class to Single binary, skipping the question.
    #
    # -y 
    #
    # automatic confirmation to the question
    #
    print( ">>> dh_make") 
    if os.system( "cd /tmp/DebianPackages/python-%s-%s && dh_make --native -s -y" % (PACKET_NAME, version)):
        print( "failed to dh_make")
        sys.exit( 255)
    #
    # copy README.source, control, copyright, rules 
    #
    for name in [ 'control', 'copyright', 'rules', 'README.source']: 
        if os.system( "cp -v %s/debian/%s /tmp/DebianPackages/python-%s-%s/debian/%s" %
                      (ROOT_DIR, name, PACKET_NAME, version, name)):
            print( "failed to copy %s" % name)
            sys.exit( 255)
    #
    # build debian package
    #
    print( ">>> build package") 
    if os.system( "cd /tmp/DebianPackages/python-%s-%s && debuild -us -uc" % (PACKET_NAME, version)):
        print( "failed to debuild")
        sys.exit( 255)
    
    #
    # check the deb packages and copy them to ./pyspectra/DebianPackages
    #
    debNameP2 = "/tmp/DebianPackages/python-%s_%s_all.deb" % (PACKET_NAME, version)
    if os.path.exists( debNameP2):
        print( "%s has been created" % (debNameP2))
        if os.system( "cp -v %s %s/DebianPackages" % 
                      (debNameP2, ROOT_DIR)):
            print( "failed to copy deb package to ./DebianPackages")
            sys.exit( 255)
    debNameP3 = "/tmp/DebianPackages/python3-%s_%s_all.deb" % (PACKET_NAME, version)
    if os.path.exists( debNameP3):
        print( "%s has been created" % (debNameP3))
        if os.system( "cp -v %s %s/DebianPackages" % 
                      (debNameP3, ROOT_DIR)):
            print( "failed to copy deb package to ./DebianPackages")
            sys.exit( 255)

    return 

if __name__ == "__main__":
    main()
    
