from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

import sismic

# python setup.py register
# python setup.py sdist bdist_wheel upload

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='sismic',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=sismic.__version__,

    description=sismic.__description__,
    long_description=long_description,

    # The project's main homepage.
    url=sismic.__url__,

    # Author details
    author=sismic.__author__,
    author_email=sismic.__email__,

    # Choose your license
    license=sismic.__licence__,

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',

        'Environment :: Console',

        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',

        'Topic :: Software Development :: Interpreters',
        'Topic :: Software Development :: Testing',
        'Topic :: Scientific/Engineering',

        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',

        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',

    ],

    # What does your project relate to?
    keywords='statechart state machine interpreter model uml scxml harel',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['docs', 'venv', 'tests']),

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #py_modules=['sismic'],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['ruamel.yaml>=0.12.10', 'schema>=0.6.2', 'behave>=1.2.5', 'typing>=3.5.1', 'pyparsing>=2.1.1'],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        #'dev': ['check-manifest'],
    },

    include_package_data=True,

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'sismic-behave=sismic.testing.behave:main',
        ],
    },
)
