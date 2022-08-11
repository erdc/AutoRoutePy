# -*- coding: utf-8 -*-
##
##  setup.py
##  AutoRoutePy
##
##  Created by Alan D. Snow.
##  Copyright © 2015-2016 Alan D Snow. All rights reserved.
##  License: BSD-3 Clause

from setuptools import setup, find_packages

setup(
    name='AutoRoutePy',
    version='2.1.0',
    description='Python scripting interface for the AutoRoute progam.'
                ' Has ability to Prepare input from RAPID output (www.rapid-hub.org).',
    keywords='AutoRoute',
    author='Alan Dee Snow',
    author_email='alan.d.snow@usace.army.mil',
    url='https://github.com/erdc/AutoRoutePy',
    download_url='https://github.com/erdc/AutoRoutePy/archive/2.1.0.tar.gz',
    license='BSD 3-Clause',
    packages=find_packages(),
    install_requires=['condorpy', 'psutil', 'gdal', 'numpy', 'RAPIDpy'],
    classifiers=[
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            ],
)
