# python-configuration
> A library to load configuration parameters hierarchically from multiple sources and formats

[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)
[![version](https://img.shields.io/pypi/v/python-configuration)](https://pypi.org/project/python-configuration/)
![python](https://img.shields.io/pypi/pyversions/python-configuration)
![wheel](https://img.shields.io/pypi/wheel/python-configuration)
![license](https://img.shields.io/pypi/l/python-configuration)
[![tests](https://github.com/tr11/python-configuration/actions/workflows/run_tests.yml/badge.svg)](https://github.com/tr11/python-configuration/actions/workflows/run_tests.yml)
[![codecov](https://codecov.io/gh/tr11/python-configuration/branch/main/graph/badge.svg?token=5zRYlGnDs7)](https://codecov.io/gh/tr11/python-configuration)
[![Documentation](https://github.com/tr11/python-configuration/actions/workflows/docs.yml/badge.svg)](https://github.com/tr11/python-configuration/actions/workflows/docs.yml)

This library is intended as a helper mechanism to load configuration files hierarchically.

## Supported Formats

The `python-configuration` library supports the following configuration formats and sources:

- Python files
- Dictionaries
- Environment variables
- Filesystem paths
- JSON files
- INI files 
- dotenv type files
- Optional support for:
  - YAML files: requires `yaml`
  - TOML files: requires `tomli` for Python < 3.11
  - Azure Key Vault credentials: requires `azure-keyvault`
  - AWS Secrets Manager credentials: requires `boto3`
  - GCP Secret Manager credentials: requires `google-cloud-secret-manager`
  - Hashicorp Vault credentials: requires `hvac`


## Installing

To install the library:

```shell
pip install python-configuration
```

To include the optional TOML and/or YAML loaders, install the optional dependencies `toml` and ` yaml`. For example,

```shell
pip install python-configuration[toml,yaml]
```

Without the optional dependencies, the TOML (Python < 3.11) and YAML loaders will not be available, 
and attempting to use them will raise an exception.

## Getting started

`python-configuration` converts the various config types into dictionaries with dotted-based keys. For example, given this JSON configuration

```json
{
    "a": {
        "b": "value"
    }
}
```

We can use the `config_from_json` method to parse it:

```python
from config import config_from_json

cfg = config_from_json("my_config_file.json", read_from_file=True)
```

(Similar methods exist for all the other supported configuration formats (eg. `config_from_toml`, etc.).)

We are then able to refer to the parameters in the config above using any of:

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

There are two general types of objects in this library. The first one is the `Configuration`, which represents a single config source.  The second is a `ConfigurationSet` that allows for multiple `Configuration` objects to be specified.

### Single Config

#### Python Files

To load a configuration from a Python module, the `config_from_python` can be used.
The first parameter must be a Python module and can be specified as an absolute path to the Python file or as an importable module.

Optional parameters are the `prefix` and `separator`.  The following call

```python
config_from_python('foo.bar', prefix='CONFIG', separator='__')
```

will read every variable in the `foo.bar` module that starts with `CONFIG__` and replace every occurrence of `__` with a `.`. For example,

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

Note that the single underscore in `BB_C` is not replaced and the last line is not prefixed by `CONFIG`.

#### Dictionaries

Dictionaries are loaded with `config_from_dict` and are converted internally to a flattened `dict`.

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

Folders with files named as `xxx.yyy.zzz` can be loaded with the `config_from_path` function.  This format is useful to load mounted Kubernetes [ConfigMaps](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/#populate-a-volume-with-data-stored-in-a-configmap) or [Secrets](https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#create-a-pod-that-has-access-to-the-secret-data-through-a-volume).

#### JSON, INI, .env, YAML, TOML

JSON, INI, YAML, TOML files are loaded respectively with
`config_from_json`,
`config_from_ini`,
`config_from_dotenv`,
`config_from_yaml`, and
`config_from_toml`.
The parameter `read_from_file` controls whether a string should be interpreted as a filename.

###### Caveats

In order for `Configuration` objects to act as `dict` and allow the syntax `dict(cfg)`, the `keys()` method is implemented as the typical `dict` keys. If `keys` is an element in the configuration `cfg` then the `dict(cfg)` call will fail. In that case, it's necessary to use the `cfg.as_dict()` method to retrieve the `dict` representation for the `Configuration` object.

The same applies to the methods `values()` and `items()`.


### Configuration Sets

Configuration sets are used to hierarchically load configurations and merge settings. Sets can be loaded by constructing a `ConfigurationSet` object directly or using the simplified `config` function.

To construct a `ConfigurationSet`, pass in as many of the simple `Configuration` objects as needed:

```python
cfg = ConfigurationSet(
    config_from_env(prefix=PREFIX),
    config_from_json(path, read_from_file=True),
    config_from_dict(DICT),
)
```
The example above will read first from Environment variables prefixed with `PREFIX`, and fallback first to the JSON file at `path`, and finally use the dictionary `DICT`.

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
* extension `.env` for dotenv type files
* filesystem folders as Filesystem Paths
* the strings `env` or `environment` for Environment Variables

#### Merging Values

`ConfigurationSet` instances are constructed by inspecting each configuration source, taking into account nested dictionaries, and merging at the most granular level.
For example, the instance obtained from `cfg = config(d1, d2)` for the dictionaries below

```python
d1 = {'sub': {'a': 1, 'b': 4}}
d2 = {'sub': {'b': 2, 'c': 3}}
```

is such that `cfg['sub']` equals

```python
{'a': 1, 'b': 4, 'c': 3}
```

Note that the nested dictionaries of `'sub'` in each of `d1` and `d2` do not overwrite each other, but are merged into a single dictionary with keys from both `d1` and `d2`, giving priority to the values of `d1` over those from `d2`.


###### Caveats

As long as the data types are consistent across all the configurations that are part of a `ConfigurationSet`, the behavior should be straightforward.  When different configuration objects are specified with competing data types, the first configuration to define the elements sets its datatype. For example, if in the example above `element` is interpreted as a `dict` from environment variables, but the JSON file specifies it as anything else besides a mapping, then the JSON value will be dropped automatically.

## Other Features

###### String Interpolation

When setting the `interpolate` parameter in any `Configuration` instance, the library will perform a string interpolation step using the [str.format](https://docs.python.org/3/library/string.html#formatstrings) syntax.  In particular, this allows to format configuration values automatically:

```python
cfg = config_from_dict({
    "percentage": "{val:.3%}",
    "with_sign": "{val:+f}",
    "val": 1.23456,
    }, interpolate=True)

assert cfg.val == 1.23456
assert cfg.with_sign == "+1.234560"
assert cfg.percentage == "123.456%"
```

###### Validation

Validation relies on the [jsonchema](https://github.com/python-jsonschema/jsonschema) library, which is automatically installed using the extra `validation`. To use it, call the `validate` method on any `Configuration` instance in a manner similar to what is described on the `jsonschema` library:

```python
schema = {
    "type" : "object",
    "properties" : {
        "price" : {"type" : "number"},
        "name" : {"type" : "string"},
    },
}

cfg = config_from_dict({"name" : "Eggs", "price" : 34.99})
assert cfg.validate(schema)

cfg = config_from_dict({"name" : "Eggs", "price" : "Invalid"})
assert not cfg.validate(schema)

# pass the `raise_on_error` parameter to get the traceback of validation failures
cfg.validate(schema, raise_on_error=True)
# ValidationError: 'Invalid' is not of type 'number'
```

To use the [format](https://python-jsonschema.readthedocs.io/en/latest/validate/#validating-formats) feature of the `jsonschema` library, the extra dependencies must be installed separately as explained in the documentation of `jsonschema`.   

```python
from jsonschema import Draft202012Validator

schema = {
    "type" : "object",
    "properties" : {
        "ip" : {"format" : "ipv4"},
    },
}

cfg = config_from_dict({"ip": "10.0.0.1"})
assert cfg.validate(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

cfg = config_from_dict({"ip": "10"})
assert not cfg.validate(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

# with the `raise_on_error` parameter:
c.validate(schema, raise_on_error=True, format_checker=Draft202012Validator.FORMAT_CHECKER)
# ValidationError: '10' is not a 'ipv4'
```


## Extras

The `config.contrib` package contains extra implementations of the `Configuration` class used for special cases. Currently the following are implemented:

* `AzureKeyVaultConfiguration` in `config.contrib.azure`, which takes Azure Key Vault
  credentials into a `Configuration`-compatible instance. To install the needed dependencies
  execute

  ```shell
  pip install python-configuration[azure]
  ```

* `AWSSecretsManagerConfiguration` in `config.contrib.aws`, which takes AWS Secrets Manager
  credentials into a `Configuration`-compatible instance. To install the needed dependencies
  execute

  ```shell
  pip install python-configuration[aws]
  ```

* `GCPSecretManagerConfiguration` in `config.contrib.gcp`, which takes GCP Secret Manager
  credentials into a `Configuration`-compatible instance. To install the needed dependencies
  execute

  ```shell
  pip install python-configuration[gcp]
  ```

* `HashicorpVaultConfiguration` in `config.contrib.vault`, which takes Hashicorp Vault
  credentials into a `Configuration`-compatible instance. To install the needed dependencies
  execute

  ```shell
  pip install python-configuration[vault]
  ```

## Features

* Load multiple configuration types
* Hierarchical configuration
* Ability to override with environment variables
* Merge parameters from different configuration types

## Contributing

If you'd like to contribute, please fork the repository and use a feature branch. Pull requests are welcome.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the details.

## Links

- Repository: https://github.com/tr11/python-configuration
- Issue tracker: https://github.com/tr11/python-configuration/issues
- Documentation: https://python-configuration.readthedocs.io

## Licensing

The code in this project is licensed under MIT license.
