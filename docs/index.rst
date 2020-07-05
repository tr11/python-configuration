.. python-configuration documentation master file, created by
   sphinx-quickstart on Mon Jul 15 10:49:38 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


================================================
Welcome to python-configuration's documentation!
================================================

This library is intended as a helper mechanism to load configuration files
hierarchically.  Current format types are:

- Python files
- Dictionaries
- Environment variables
- Filesystem paths
- JSON files
- INI files

and optionally

- YAML files
- TOML files
- Azure Key Vault credentials
- AWS Secrets Manager credentials
- GCP Secret Manager credentials


Installing
==========

To install the library:

.. code-block:: bash

   $ pip install python-configuration


To include the optional TOML and/or YAML loaders, install the optional
dependencies :term:`toml` and :term:`yaml`. For example,

.. code-block:: bash

   $ pip install python-configuration[toml,yaml]

Getting started
===============

This library converts the config types above into dictionaries with
dotted-based keys. That is, given a config ``cfg`` from the structure

.. code-block:: python

   {
       'a': {
           'b': 'value'
       }
   }

we are able to refer to the parameter above as any of

.. code-block:: python

   cfg['a.b']
   cfg['a']['b']
   cfg['a'].b
   cfg.a.b

and extract specific data types such as dictionaries:

.. code-block:: python

   cfg['a'].as_dict == {'b': 'value'}

This is particularly useful in order to isolate group parameters.
For example, with the JSON configuration

.. code-block:: json

    {
     "database.host": "something",
     "database.port": 12345,
     "database.driver": "name",
     "app.debug": true,
     "app.environment": "development",
     "app.secrets": "super secret",
     "logging": {
       "service": "service",
       "token": "token",
       "tags": "tags"
     }
   }

one can retrieve the dictionaries as

.. code-block:: python

   cfg.database.as_dict()
   cfg.app.as_dict()
   cfg.logging.as_dict()

or simply as

.. code-block:: python

   dict(cfg.database)
   dict(cfg.app)
   dict(cfg.logging)


Configuration
=============

There are two general types of objects in this library. The first one is the :class:`~config.configuration.Configuration`,
which represents a single config source.  The second is a :class:`~config.configuration_set.ConfigurationSet` that allows for
multiple :class:`~config.configuration.Configuration` objects to be specified.

Single Config
-------------

Python Files
************

To load a configuration from a Python module, the :func:`~config.config_from_python` can be used.
The first parameter must be a Python module and can be specified as an absolute path to the Python file or as an importable module.

Optional parameters are the ``prefix`` and ``separator``.  The following call

.. code-block:: python

   config_from_python('foo.bar', prefix='CONFIG', separator='__')

will read every variable in the ``foo.bar`` module that starts with ``CONFIG__`` and replace
every occurrence of ``__`` with a ``.``. For example,

.. code-block:: python

   # foo.bar
   CONFIG__AA__BB_C = 1
   CONFIG__AA__BB__D = 2
   CONF__AA__BB__D = 3

would result in the configuration

.. code-block:: python

   {
       'aa.bb_c': 1,
       'aa.bb.d': 2,
   }

Note that the single underscore in ``BB_C`` is not replaced and the last line is not
prefixed by ``CONFIG``.

Dictionaries
************
Dictionaries are loaded with :func:`~config.config_from_dict` and are converted internally to a
flattened ``dict``.

.. code-block:: python

   {
       'a': {
           'b': 'value'
       }
   }

becomes

.. code-block:: python

   {
       'a.b': 'value'
   }


Environment Variables
*********************
Environment variables starting with ``prefix`` can be read with :func:`~config.config_from_env`:

.. code-block:: python

   config_from_env(prefix, separator='_')


Filesystem Paths
****************
Folders with files named as ``xxx.yyy.zzz`` can be loaded with the :func:`~config.config_from_path` function.  This format is useful to load mounted
Kubernetes `ConfigMaps <https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/#populate-a-volume-with-data-stored-in-a-configmap>`_.
or `Secrets <https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#create-a-pod-that-has-access-to-the-secret-data-through-a-volume>`_.

JSON, INI, YAML, TOML
*********************
JSON, INI, YAML, TOML files are loaded respectively with
:func:`~config.config_from_json`,
:func:`~config.config_from_ini`,
:func:`~config.config_from_yaml`, and
:func:`~config.config_from_toml`.
The parameter ``read_from_file`` controls
whether a string should be interpreted as a filename.

Caveats
*******
In order for :class:`~config.configuration.Configuration` objects to act as ``dict`` and allow the syntax
``dict(cfg)``, the ``keys()`` method is implemented as the typical ``dict`` keys.
If ``keys`` is an element in the configuration ``cfg`` then the ``dict(cfg)`` call will fail.
In that case, it's necessary to use the :meth:`cfg.as_dict() <config.Configuration.as_dict>` method to retrieve the
``dict`` representation for the :class:`~config.configuration.Configuration` object.

The same applies to the methods :meth:`~config.configuration.Configuration.values` and :meth:`~config.configuration.Configuration.items()`.


Configuration Sets
==================
Configuration sets are used to hierarchically load configurations and merge
settings. Sets can be loaded by constructing a :class:`~config.configuration_set.ConfigurationSet` object directly or
using the simplified :func:`~config.config` function.

To construct a :class:`~config.configuration_set.ConfigurationSet`, pass in as many of the simple :class:`~config.configuration.Configuration` objects as needed:

.. code-block:: python

   cfg = ConfigurationSet(
       config_from_env(prefix=PREFIX),
       config_from_json(path, read_from_file=True),
       config_from_dict(DICT),
   )

The example above will read first from Environment variables prefixed with ``PREFIX``,
and fallback first to the JSON file at ``path``, and finally use the dictionary ``DICT``.

The :func:`~config.config` function simplifies loading sets by assuming some defaults.
The example above can also be obtained by

.. code-block:: python

   cfg = config(
       ('env', PREFIX),
       ('json', path, True),
       ('dict', DICT),
   )

or, even simpler if ``path`` points to a file with a ``.json`` suffix:

.. code-block:: python

   cfg = config('env', path, DICT, prefix=PREFIX)

The :func:`~config.config` function automatically detects the following:

- extension ``.py`` for python modules
- dot-separated python identifiers as a python module (e.g. ``foo.bar``)
- extension ``.json`` for JSON files
- extension ``.yaml`` for YAML files
- extension ``.toml`` for TOML files
- extension ``.ini`` for INI files
- filesystem folders as Filesystem Paths
- the strings ``env`` or ``environment`` for Environment Variables

Merging Values
--------------
:class:`~config.configuration_set.ConfigurationSet` instances
are constructed by inspecting each configuration source, taking into account nested dictionaries, and merging at the most granular level.
For example, the instance obtained from ``cfg = config(d1, d2)`` for the dictionaries below

.. code-block:: python

   d1 = {'sub': {'a': 1, 'b': 4}}
   d2 = {'sub': {'b': 2, 'c': 3}}

is such that ``cfg['sub']`` equals

.. code-block:: python

   {'a': 1, 'b': 4, 'c': 3}

Note that the nested dictionaries of ``'sub'`` in each of ``d1`` and ``d2`` do not overwrite each other, but are merged into a single
dictionary with keys from both ``d1`` and ``d2``, giving priority to the values of ``d1`` over those from ``d2``.

Caveats
*******
As long as the data types are consistent across all the configurations that are
part of a :class:`~config.configuration_set.ConfigurationSet`, the behavior should be straightforward.  When different
configuration objects are specified with competing data types, the first configuration to
define the elements sets its datatype. For example, if in the example above
``element`` is interpreted as a ``dict`` from environment variables, but the
JSON file specifies it as anything else besides a mapping, then the JSON value will be
dropped automatically.

Other Features
==============

String Interpolation
--------------------

When setting the ``interpolate`` parameter in any :class:`~config.configuration.Configuration` instance, the library will
perform a string interpolation step using the
`str.format <https://docs.python.org/3/library/string.html#formatstrings>`_
syntax.  In particular, this allows to format configuration values automatically:

.. code-block:: python
   cfg = config_from_dict({
       "percentage": "{val:.3%}",
       "with_sign": "{val:+f}",
       "val": 1.23456}, interpolate=True)

   assert cfg.val == 1.23456
   assert cfg.with_sign == "+1.234560"
   assert cfg.percentage == "123.456%"


Extras
======
The :mod:`~config.contrib` package contains extra implementations of the :class:`~config.configuration.Configuration` class
used for special cases. Currently the following are implemented:

- :class:`~config.contrib.azure.AzureKeyVaultConfiguration` in :mod:`~config.contrib.azure`, which takes Azure Key Vault
  credentials into a :class:`~config.configuration.Configuration`-compatible instance. To install the needed dependencies
  execute

  .. code-block:: shell

     pip install python-configuration[azure]

- :class:`~config.contrib.aws.AWSSecretsManagerConfiguration` in :mod:`~config.contrib.aws`, which takes AWS Secrets Manager
  credentials into a :class:`~config.configuration.Configuration`-compatible instance. To install the needed dependencies
  execute

  .. code-block:: shell

     pip install python-configuration[aws]

- :class:`~config.contrib.gpc.GCPSecretManagerConfiguration` in :mod:`~config.contrib.gcp`, which takes GCP Secret Manager
  credentials into a :class:`~config.configuration.Configuration`-compatible instance. To install the needed dependencies
  execute

  .. code-block:: shell

     pip install python-configuration[gcp]


Developing
==========

To develop this library, download the source code and install a local version.


Features
========

* Load multiple configuration types
* Hierarchical configuration
* Ability to override with environment variables
* Merge parameters from different configuration types

Contributing
============

If you'd like to contribute, please fork the repository and use a feature
branch. Pull requests are welcome.

Links
=====

- Repository: https://github.com/tr11/python-configuration
- Issue tracker: https://github.com/tr11/python-configuration/issues

Licensing
=========

The code in this project is licensed under MIT license.


=================
Table of Contents
=================

.. toctree::
   :maxdepth: 2

   api
   glossary
