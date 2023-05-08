Installation
============

Using pip
---------

Sismic requires Python >=3.7, and can be installed using ``pip`` as usual: ``pip install sismic``.
This will install the latest stable version.
Starting from release 1.0.0, Sismic adheres to a `semantic versioning <https://semver.org>`__ scheme.

You can isolate Sismic installation by using virtual environments:

1. Get the tool to create virtual environments: ``pip install virtualenv``
2. Create the environment: ``virtualenv -p python3.5 env``
3. Jump into: ``source env/bin/activate``
4. Install Sismic: ``pip install sismic``

Consider using `pew <https://github.com/berdario/pew>`__ or `pipenv <https://docs.pipenv.org/>`__ to manage your virtual environments.

The development version can also be installed directly from its git repository:
``pip install git+git://github.com/AlexandreDecan/sismic.git``


From GitHub
-----------

You can also install Sismic from its repository by cloning it.

1. Get the tool to create virtual environments: ``pip install virtualenv``
2. Create the environment: ``virtualenv -p python3.5 env``
3. Jump into: ``source env/bin/activate``
4. Clone the repository: ``git clone https://github.com/AlexandreDecan/sismic``
5. Install Sismic: ``pip install .`` or ``pip install -e .`` (editable mode)
6. Install test dependencies: ``pip install -r requirements.txt``

Sismic is now available from the root directory. Its code is in the *sismic* directory.
The documentation can be built from the *docs* directory using ``make html``.

Tests are available both for the code and the documentation:

- ``make doctest`` in the *docs* directory (documentation tests)
- ``python -m pytest tests/`` from the root directory (code tests)
