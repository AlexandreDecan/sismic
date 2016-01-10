Installation
============

Sismic can be installed using ``pip`` as usual: ``pip install sismic``.
This will install the latest stable version.

You can also install Sismic from its repository by cloning it.
The development occurs in the *master* branch, the latest stable distributed version is in the *stable* branch.

Sismic requires Python >=3.4 but should also work with Python 3.3.
You can isolate Sismic installation by using virtual environments:

1. Get the tool to create environment: ``pip install virtualenv``
2. Create the environment: ``virtualenv -p python3.4 env``
3. Jump into: ``source env/bin/activate``
4. Install dependencies: ``pip install -r requirements.txt``
5. Test PySS: ``python -m unittest discover``
