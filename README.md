# python-configuration
> A library to load configuration parameters from multiple sources and formats

[![version](https://img.shields.io/pypi/v/python-configuration)](https://pypi.org/project/python-configuration/)
![python](https://img.shields.io/pypi/pyversions/python-configuration)
![wheel](https://img.shields.io/pypi/wheel/python-configuration)
![license](https://img.shields.io/pypi/l/python-configuration)
[![build](https://img.shields.io/travis/tr11/python-configuration)](https://travis-ci.org/tr11/python-configuration)
[![codecov](https://codecov.io/gh/tr11/python-configuration/branch/master/graph/badge.svg)](https://codecov.io/gh/tr11/python-configuration)
[![Documentation Status](https://readthedocs.org/projects/python-configuration/badge/?version=latest)](https://python-configuration.readthedocs.io/en/latest/?badge=latest)

This library is intended as a helper mechanism to load configuration files
hierarchically.  Current format types are:
* Python files
* Dictionaries
* Environment variables
* Filesystem paths
* JSON files
* INI files

and optionally
* YAML files
* TOML files
* Azure Key Vault credentials
* AWS Secrets Manager credentials

## Installing

To install the library:
```shell
pip install python-configuration
```

To include the optional TOML and/or YAML loaders, install the optional
dependencies `toml` and ` yaml`. For example,
```shell
pip install python-configuration[toml, yaml]
```

## Getting started

This library converts the config types above into dictionaries with 
dotted-based keys. That is, given a config `cfg` from the structure
```python
{
    'a': {
        'b': 'value'
    }
}
```
we are able to refer to the parameter above as any of 
```python
cfg['a.b']
cfg['a']['b']
cfg['a'].b
cfg.a.b
```
and extract specific data types such as dictionaries:
```python
cfg['a'].as_dict == {'b': 'value'}
```
This is particularly useful in order to isolate group parameters.
For example, with the JSON configuration
```json
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
```
one can retrieve the dictionaries as 
```python
cfg.database.as_dict()
cfg.app.as_dict()
cfg.logging.as_dict()
```
or simply as 
```python
dict(cfg.database)
dict(cfg.app)
dict(cfg.logging)
```
## Configuration
There are two general types of objects in this library. The first one is the `Configuration`,
which represents a single config source.  The second is a `ConfigurationSet` that allows for
multiple `Configuration` objects to be specified.

### Single Config

#### Python Files
To load a configuration from a Python module, the `config_from_python` can be used.
The first parameter must be a Python module and can be specified as an absolute path to the Python file or as an importable module.

Optional parameters are the `prefix` and `separator`.  The following call 
```python
config_from_python('foo.bar', prefix='CONFIG', separator='__')
```
will read every variable in the `foo.bar` module that starts with `CONFIG__` and replace
every occurrence of `__` with a `.`. For example,
```python
# foo.bar
CONFIG__AA__BB_C = 1
CONFIG__AA__BB__D = 2
CONF__AA__BB__D = 3
```
would result in the configuration
```python
{
    'aa.bb_c': 1,
    'aa.bb.d': 2,
}
```
Note that the single underscore in `BB_C` is not replaced and the last line is not
prefixed by `CONFIG`. 

#### Dictionaries
Dictionaries are loaded with `config_from_dict` and are converted internally to a 
flattened `dict`. 
```python
{
    'a': {
        'b': 'value'
    }
}
```
becomes
```python
{
    'a.b': 'value'
}
```

#### Environment Variables
Environment variables starting with `prefix` can be read with `config_from_env`:
```python
config_from_env(prefix, separator='_')
```

#### Filesystem Paths
Folders with files named as `xxx.yyy.zzz` can be loaded with the `config_from_path` function.  This format is useful to load mounted
Kubernetes [ConfigMaps](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/#populate-a-volume-with-data-stored-in-a-configmap)
or [Secrets](https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#create-a-pod-that-has-access-to-the-secret-data-through-a-volume).

#### JSON, INI, YAML, TOML
JSON, INI, YAML, TOML files are loaded respectively with
`config_from_json`,
`config_from_ini`,
`config_from_yaml`, and
`config_from_toml`.
The parameter `read_from_file` controls
whether a string should be interpreted as a filename.

###### Caveats
In order for `Configuration` objects to act as `dict` and allow the syntax
`dict(cfg)`, the `keys()` method is implemented as the typical `dict` keys.
If `keys` is an element in the configuration `cfg` then the `dict(cfg)` call will fail.
In that case, it's necessary to use the `cfg.as_dict()` method to retrieve the
`dict` representation for the `Configuration` object.

The same applies to the methods `values()` and `items()`.
 

### Configuration Sets
Configuration sets are used to hierarchically load configurations and merge
settings. Sets can be loaded by constructing a `ConfigurationSet` object directly or
using the simplified `config` function.

To construct a `ConfigurationSet`, pass in as many of the simple `Configuration` objects as needed:
```python
cfg = ConfigurationSet(
    config_from_env(prefix=PREFIX),
    config_from_json(path, read_from_file=True),
    config_from_dict(DICT),
)
```
The example above will read first from Environment variables prefixed with `PREFIX`, 
and fallback first to the JSON file at `path`, and finally use the dictionary `DICT`.

The `config` function simplifies loading sets by assuming some defaults.
The example above can also be obtained by
```python
cfg = config(
    ('env', PREFIX),
    ('json', path, True),
    ('dict', DICT),
)
```
or, even simpler if `path` points to a file with a `.json` suffix:
```python
cfg = config('env', path, DICT, prefix=PREFIX)
```
The `config` function automatically detects the following:
* extension `.py` for python modules
* dot-separated python identifiers as a python module (e.g. `foo.bar`)
* extension `.json` for JSON files
* extension `.yaml` for YAML files
* extension `.toml` for TOML files
* extension `.ini` for INI files
* filesystem folders as Filesystem Paths
* the strings `env` or `environment` for Environment Variables

###### Caveats
As long as the data types are consistent across all the configurations that are
part of a `ConfigurationSet`, the behavior should be straightforward.  When different
configuration objects are specified with competing data types, the first configuration to
define the elements sets its datatype. For example, if in the example above 
`element` is interpreted as a `dict` from environment variables, but the 
JSON file specifies it as anything else besides a mapping, then the JSON value will be
dropped automatically. 

## Extras
The `config.contrib` package contains extra implementations of the `Configuration` class
used for special cases. Currently the following are implemented:
* `AzureKeyVaultConfiguration` in `config.contrib.azure`, which takes Azure Key Vault
  credentials into a `Configuration`-compatible instance. To install the needed dependencies
  execute
  ```shell
  pip install python-configuration[azure]
* `AWSSecretsManagerConfiguration` in `config.contrib.aws`, which takes AWS Secrets Manager
  credentials into a `Configuration`-compatible instance. To install the needed dependencies
  execute
  ```shell
  pip install python-configuration[aws]
  ```

## Developing

To develop this library, download the source code and install a local version.


## Features

* Load multiple configuration types
* Hierarchical configuration
* Ability to override with environment variables
* Merge parameters from different configuration types

## Contributing

If you'd like to contribute, please fork the repository and use a feature
branch. Pull requests are welcome.

## Links

- Repository: https://github.com/tr11/python-configuration
- Issue tracker: https://github.com/tr11/python-configuration/issues
- Documentation: https://python-configuration.readthedocs.io

## Licensing

The code in this project is licensed under MIT license.
