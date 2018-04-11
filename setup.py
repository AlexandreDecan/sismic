# To use a consistent encoding
from codecs import open
from os import path

from setuptools import setup, find_packages

import sismic

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='sismic',
    version=sismic.__version__,
    description=sismic.__description__,
    long_description=long_description,
    url=sismic.__url__,
    author=sismic.__author__,
    author_email=sismic.__email__,
    license=sismic.__licence__,
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 5 - Production/Stable',

        'Environment :: Console',

        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',

        'Topic :: Software Development :: Interpreters',
        'Topic :: Software Development :: Testing',
        'Topic :: Scientific/Engineering',

        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',

        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',

    ],
    keywords='statechart state machine interpreter model uml scxml harel',
    packages=find_packages(exclude=['docs', 'tests']),
    python_requires='>=3.4',
    install_requires=[
        'ruamel.yaml>=0.12.10',
        'schema>=0.6.2',
        'behave>=1.2.6',
        'typing>=3.5.1'
    ],
    entry_points={
        'console_scripts': [
            'sismic-bdd=sismic.bdd.__main__:cli',
        ],
    },
    # Copy all files listed in MANIFEST.in to installation folder
    include_package_data=True,
)
