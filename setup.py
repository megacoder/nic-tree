#!/usr/bin/env python
# vim: nonu noet ai sm ts=4 sw=4

from setuptools import setup, find_packages

Name    = 'nic_tree'
Runtime	= 'nic-tree'
Version = '1.0.8'

with open( '{0}/version.py'.format( Name ), 'wt' ) as f:
    print >>f, 'Version = "{0}"'.format( Version )

setup(
    name				= Name,
    version				= Version,
    description			= 'Show network structure from ifcfg-* files',
	long_description	= open( 'README.md' ).read(),
    url					= 'http://www.megacoder.com',
    author				= 'Tommy Reynolds',
    author_email		= 'oldest.software.guy@gmail.com',
    packages			= [ Name ],
    scripts				= [
        '{0}/scripts/{1}'.format(
			Name,
			Runtime
		),
    ]
)

