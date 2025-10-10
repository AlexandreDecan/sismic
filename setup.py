from os import path
from codecs import open
from setuptools import setup, find_packages

import sismic

# Get the long description from the README file
with open(path.join(path.abspath(path.dirname(__file__)), 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=sismic.__package__,
    version=sismic.__version__,
    license=sismic.__licence__,

    author=sismic.__author__,
    url=sismic.__url__,

    description=sismic.__description__,
    long_description=long_description,

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
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
    ],
    keywords='statechart state machine interpreter model uml scxml harel',

    packages=find_packages(exclude=['docs', 'tests']),
    python_requires='>=3.9',
    install_requires=[
        'ruamel.yaml>=0.18.2',
        'schema>=0.5.0',
        'behave>=1.2.6',
    ],

    entry_points={
        'console_scripts': [
            'sismic-bdd=sismic.bdd.__main__:cli',
            'sismic-plantuml=sismic.io.plantuml:cli',
        ],
    },

    include_package_data=True,
    zip_safe=True,
)
