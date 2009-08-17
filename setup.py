#!/usr/bin/env python

# Use distutils as setuptools tries to be too smart and confuses
# everying.
from distutils.core import setup
from distutils import sysconfig

import shutil
import sys
import os.path

import sys
print sys.path

print sysconfig.get_config_var('prefix')

# add cwd to installed single player XML file
import fileinput
of = open("daneel_ai.xml", 'w')
for line in fileinput.FileInput("daneel_ai.xml.in"):
    if 'PREFIX' in line:
        line = line.replace('PREFIX', sysconfig.get_config_var('prefix'))
    of.write(line)
of.close()

extra_arguments = {}
if sys.platform == 'win32':
    from setuptools import setup
    import py2exe
 
    if os.path.exists("dist"):
        shutil.rmtree("dist")
 
    if os.path.exists("tp"):
        shutil.rmtree("tp")
 
    shutil.copytree(os.path.join('libtpproto-py', 'tp', 'netlib'), os.path.join('tp', 'netlib'))
    shutil.copytree(os.path.join('libtpclient-py', 'tp', 'client'), os.path.join('tp', 'client'))
    open(os.path.join('tp', "__init__.py"), 'w').close()
 
    extra_arguments = dict(
        options={
                "py2exe": {
                        "dll_excludes": [],
                        "packages": ["tp.netlib", "tp.client"],
                        "includes": ["daneel.*"],
                        "excludes": ["Tkconstants", "Tkinter", "tcl", "pydoc" ],
                        "optimize": 2,
                        "compressed": 0,
                }
        },
    )

setup(
    name = "daneel_ai",
    version = "0.0.3",
    license = "GPL",
    description = "An advanced rule based AI for Thousand Parsec.",
    long_description = "",
    author = "Vincent Verhoeven",
    author_email = "verhoevenv@gmail.com",
    url = "http://www.thousandparsec.net",
    scripts = ["daneel_ai"],
    console = ["daneel_ai"],
    packages = ["daneel"],
    data_files = [("share/daneel_ai", ("LICENSE", "COPYING", "README")),
                  ("share/daneel_ai/rules", ("rules/rfts", "rules/risk")),
                  ("share/tp", ("daneel_ai.xml",))],
    **extra_arguments
)
