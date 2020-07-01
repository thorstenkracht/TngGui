#!/usr/bin/env python

from distutils.core import setup
import handleVersion

ROOT_DIR = "/home/kracht/Misc/tngGui"
#
handleVers = handleVersion.handleVersion( ROOT_DIR)
version = handleVers.findVersion()

setup( name="python-tnggui", 
       version=version,
       author = "Thorsten Kracht",
       author_email = "thorsten.kracht@desy.de",
       url = "https://github.com/thorstenkracht/TngGui",    
       scripts = [ 'tngGui/bin/TngGui.py'],
       packages = ['tngGui',
                   'tngGui/lib'], 
   )
