Moby
####

Moby is a tool to automate running scripts in a docker container.
This can be used to run tests or other stuff that depend on binaries or other
stuff you don't want to install.


Usage
=====

Moby assumes there is a `Dockerfile` in the current directory. Currently there
is no way to configure otherwise. So there should be a `Dockerfile`.

Create a file called `moby.yml`, this is the configuration file moby will
search for. Example:

.. code-block:: yaml

    envlist: [test, build]

    test:
      before:
        push:
          - tests
          - tox.ini
        run:
          - apt-get install -y tox
      run:
        - tox

    build:
      run:
        - ./build.sh
      after:
        pull:
          - dist

Then run `moby`.

When the example is ran, moby builds and launches the container from the
`Dockerfile`. The `test` environment is ran first. The `tests` directory and
the `tox.ini` file are pushed to the running container (to the working dir).
Then `apt-get install -y tox` is ran. Lastly, `tox` is executed.
Then the `build` environment is ran. `./build.sh` is executed and the `dist`
directory is downloaded from the container to the current directory.
After all this, the container is shut down.


Configuration reference
=======================

after
-----

An environment can have an `after` entry. This entry is considered an
environment that is ran after the environment is ran.

before
------

An environment can have an `after` entry. This entry is considered an
environment that is ran before the environment is ran.

envlist
-------

`envlist` is a required entry, it states which environments are to be run.

environment
-----------

An environment is created at the root with an arbitrary name.
An environment only requires a `run` entry.

push
----

An environment can have a `push` entry. This states which files to push to
the container.

pull
----

An environment can have a `pull` entry. This states which files to pull from
the container.
