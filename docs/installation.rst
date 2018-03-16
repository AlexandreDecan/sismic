Installation
============

Using pip
---------

Sismic can be installed using ``pip`` as usual: ``pip install sismic``.
This will install the latest stable version.
Sismic requires Python >=3.4.
You can isolate Sismic installation by using virtual environments:

1. Get the tool to create virtual environments: ``pip install virtualenv``
2. Create the environment: ``virtualenv -p python3.4 env``
3. Jump into: ``source env/bin/activate``
4. Install Sismic: ``pip install sismic``

The development version can also be installed directly from its git repository:
``pip install git+git://github.com/AlexandreDecan/sismic.git@devel``

From GitHub
-----------

You can also install Sismic from its repository by cloning it.
The development occurs in the *devel* branch, the latest stable distributed version is in the *master* branch.

1. Get the tool to create virtual environments: ``pip install virtualenv``
2. Create the environment: ``virtualenv -p python3.4 env``
3. Jump into: ``source env/bin/activate``
4. Clone the repository: ``git clone https://github.com/AlexandreDecan/sismic``
5. Install Sismic: ``pip install .`` or ``pip install -e .`` (editable mode)
6. Install test dependencies: ``pip install -r requirements.txt``

Sismic is now available from the root directory. Its code is in the *sismic* repository.
The documentation can be built from the *docs* directory using ``make html``.

Tests are available both for the code and the documentation:

- ``make doctest`` in the *docs* directory (documentation tests)
- ``python -m pytest tests/`` from the root directory (code tests)
