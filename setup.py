#!/usr/bin/env python
# this scipt is executed with 
#
#   $ cd /home/kracht/Misc/tngGui
#   $ python setup.py sdist
#     to build the source distribution, 
#     creates dist/python-hasyutils-1.0.tar.gz 
#     the tarball is used for remote installation only
#
#   kracht$ python setup.py build
#   root$ python setup.py install
#   root$ python setup.py clean
#
# to make a debian package ( or e.g. 'DoDebianBuild.pl haso107tk' and 'DoDebianInstall.pl hastodt'): 
# 
# scp dist/python-tnggui-1.0.tar.gz haso107tk:/home/kracht/Misc/DebianBuilds
#   we assume that the directory 
#     haso107tk:/home/kracht/Misc/DebianBuilds/python-tnggui-1.0
#   does not exist
#
# ssh haso107tk cd /home/kracht/Misc/DebianBuilds && /bin/rm -rf python-tnggui-1.0
# ssh haso107tk "cd /home/kracht/Misc/DebianBuilds && tar xvzf python-tnggui-1.0.tar.gz"
# ssh haso107tk "cd /home/kracht/Misc/DebianBuilds && mv python-tnggui-1.0.tar.gz python-tnggui_1.0.orig.tar.gz"
#
#   haso107tk$ cd python-tnggui-1.0/
#   haso107tk$ dh_make --native -s -y
#     answer question 'Type of package' with 's' 
#
#    then change debian/control:
#     Source: python-tnggui
#     X-Python-Version: >= 2.7
#     Section: unknown
#     Priority: extra
#     Maintainer: Thorsten Kracht <thorsten.kracht@desy.de>
#     Build-Depends: python-all, debhelper (>= 8.0.0)
#     ... 
#
#   haso107tk$ debuild -us -uc
#
#   haso107tk$ cd ..
#   haso107tk$ scp python-tnggui_1.0_amd64.deb hastodt:/tmp
#
#   root@hastodt# dpkg -r python-tnggui                      # to remove the package
#   root@hastodt# dpkg -i /tmp/python-tnggui_1.0_amd64.deb   # to install the package
#
#   dpkg --list | grep -i python-hasy
#     list installed packages
#
from distutils.core import setup, Extension
import sys, os, commands

version = commands.getoutput( './findVersion.pl')
version = version.strip()


setup( name="python-tnggui", 
       version=version,
       author = "Thorsten Kracht",
       author_email = "thorsten.kracht@desy.de",
       url = "https://github.com/thorstenkracht/TngGui",    
       #
       # beware: MANIFEST somehow memorizes the script names (can be deleted)
       #
       scripts = [ 'tngGui/TngGui.py',
                   ],
       packages = ['tngGui',
                   'tngGui/lib', 
       ], 

   )
