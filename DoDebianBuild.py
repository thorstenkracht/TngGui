#!/usr/bin/env python
"""
this scripts creates the tnggui debian package for Python2 and Python3
  DoDebianBuild.py 

"""
import os, sys
import handleVersion
import argparse

ROOT_DIR = "/home/kracht/Misc"

def checkDebContents( packageName): 
    """
    check whether the deb package contains some important files
    """
    files2Check = [ 'bin/TngGui.py', 
                    'tngGuiClass.py']
    ret = os.popen( "dpkg-deb -c %s" % (packageName)).read()

    for line in ret.split( '\n'): 
        print( line)

    print( "checkDebContents: %s" % packageName)
    isOk = True
    for fl in files2Check: 
        if ret.find( fl) == -1: 
            print( "debian package does not contain %s " % fl)
            isOk = False
        else: 
            print( "  contains %s " % fl)
    if isOk: 
        print( "%s contains the files-to-check" % packageName)
    else: 
        print( "%s does not contain all files-to-check" % packageName)
    return isOk

def main(): 

    print( ">>> DoDebianBuild.py \n")

    if not os.path.exists( "/tmp/DebianPackages"): 
        if os.mkdir( "/tmp/DebianPackages"):
            printf( "Failed  to create /tmp/DebianPackages")
            sys.exit( 255)

    if not os.path.exists( "%s/tngGui/DebianPackages" % ROOT_DIR): 
        if os.mkdir( "%s/tngGui/DebianPackages" % ROOT_DIR):
            printf( "Failed  to create %s/DebianPackages" % ROOT_DIR)
            sys.exit( 255)

    #
    # cleanup
    #
    print( ">>> cleanup")
    if os.system( "/bin/rm -rf /tmp/DebianPackages/python*-tnggui*"):
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
    if os.system( "cd %s/tngGui && python setup.py sdist" % (ROOT_DIR)):
        print( "trouble running setup sdist")
        sys.exit( 255)
    #
    # cp the tarball
    #
    print( ">>> copy the tarBall to ../DebianPackages") 
    if os.system( "cp %s/tngGui/dist/python-tnggui-%s.tar.gz /tmp/DebianPackages" % 
                  (ROOT_DIR, version)):
        print( "failed to copy tar file")
        sys.exit( 255)
    #
    # unpack the tarball
    #
    print( ">>> unpack the tarBall") 
    if os.system( "cd /tmp/DebianPackages && tar xvzf python-tnggui-%s.tar.gz" % (version)):
        print( "failed to unpack the tar file")
        sys.exit( 255)
    #
    # rename the tarball (is this necessary?)
    #
    print( ">>> rename the tarBall") 
    if os.system( "cd /tmp/DebianPackages && mv python-tnggui-%s.tar.gz python-tnggui_%s.orig.tar.gz" % 
                  (version, version)):
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
    if os.system( "cd /tmp/DebianPackages/python-tnggui-%s && dh_make --native -s -y" % (version)):
        print( "failed to dh_make")
        sys.exit( 255)
    #
    # copy README.source, control, copyright, rules 
    #
    for name in [ 'control', 'copyright', 'rules', 'README.source']: 
        if os.system( "cp -v %s/tngGui/debian/%s /tmp/DebianPackages/python-tnggui-%s/debian/%s" %
                      (ROOT_DIR, name, version, name)):
            print( "failed to copy %s" % name)
            sys.exit( 255)
    #
    # build debian package
    #
    print( ">>> build package") 
    if os.system( "cd /tmp/DebianPackages/python-tnggui-%s && debuild -us -uc" % (version)):
        print( "failed to debuild")
        sys.exit( 255)
    
    #
    # check the deb packages and copy them to ./tngGui/DebianPackages
    #
    debNameP2 = "/tmp/DebianPackages/python-tnggui_%s_all.deb" % (version)
    if os.path.exists( debNameP2):
        print( "%s has been created" % (debNameP2))
        ret = os.popen( "dpkg-deb -c %s" % (debNameP2)).read()
        if checkDebContents( debNameP2): 
            if os.system( "cp -v %s %s/tngGui/DebianPackages" % 
                          (debNameP2, ROOT_DIR)):
                print( "failed to copy deb package to ./DebianPackages")
                sys.exit( 255)
    debNameP3 = "/tmp/DebianPackages/python3-tnggui_%s_all.deb" % (version)
    if os.path.exists( debNameP3):
        print( "%s has been created" % (debNameP3))
        ret = os.popen( "dpkg-deb -c %s" % (debNameP3)).read()
        if checkDebContents( debNameP3): 
            if os.system( "cp -v %s %s/tngGui/DebianPackages" % 
                          (debNameP3, ROOT_DIR)):
                print( "failed to copy deb package to ./DebianPackages")
                sys.exit( 255)

    return 

if __name__ == "__main__":
    main()
    
