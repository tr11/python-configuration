# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.10.0] - 2024-02-19

- Use the standard lib for `toml` in Python >= 3.11
- Switched to `hatch` instead of `poetry`

## [0.9.1] - 2023-08-06

### Added

- Allow to pass a `ignore_missing_paths` parameter to each config method
- Support for Hashicorp Vault credentials (in `config.contrib`)
- Added a `validate` method to validate `Configuration` instances against a [json schema](https://json-schema.org/understanding-json-schema/basics.html#basics).


## [0.9.0] - 2023-08-04

### Added

- Added the `section_prefix` parameter that filters sections by prefix in INI/toml files
- Allow the `ignore_missing_paths` parameter to be specified individually on Configuration Sets

### Fixed

- Errors when passing objects implementing `Mapping` instead of `dict`
- Comparison to objects that are not a `Mapping`  

### Changed

- Replaced TravisCI with GitHub Actions


## [0.8.3] - 2021-10-11

### Fixed

- Configurations from ini file won't be converted to lower case if `lowercase_keys = False`


## [0.8.2] - 2021-01-30

### Fixed

- The behavior of merging sets was incorrect since version 0.8.0


## [0.8.0] - 2020-08-01

### Changed

- The behavior of the dict-like methods `keys`, `items`, and `values` now give only the first level configuration keys instead of the old behavior of returning all the nested keys. To achieve the same behavior as before, use the `dotter_iter` context manager:

```python
cfg.keys()  # returns only the top level keys

with cfg.dotted_iter():
    cfg.keys()  # returns all the keys at all depths using '.' as a separator
```

### Fixed

- Configuration objects are now immutable

### Added

- Attribute dictionaries
- Support for _.env_-type files
- Option for deep interpolation. To activate that mode, use one of the enum values in `InterpolateEnumType` as the `interpolate_type` parameter. This allows for hierachical _templates_, in which configuration objects use the values from lower ones to interpolate instead of simply overriding.


## [0.7.1] - 2020-07-05

### Fixed

- Installation with `poetry` because of changes to pytest-black


## [0.7.0] - 2020-05-06

### Added

- New string interpolation feature


## [0.6.1] - 2020-04-24

### Changed

- Added a `separator` argument to `config` function


## [0.6.0] - 2020-01-22

### Added

- Added missing `dict` methods so a `Configuration` instance acts like a dictionary for most use cases
- Added a `reload` method to refresh a `Configuration` instance (can be used to reload a configuration from a file that may have changed).
- Added a `configs` method to expose the underlying instances of a `ConfigurationSet`


## [0.5.0] - 2020-01-08

### Added

- Support for Azure Key Vault credentials (in `config.contrib`)
- Support for AWS Secrets Manager credentials (in `config.contrib`)
- Tox support

### Changed

- Changed the `__repr__` and `__str__` methods so possibly sensitive values are not printed by default.


## [0.4.0] - 2019-10-11

### Added

- Allow path-based failures using the `config` function.
- Added a levels option to the dict-like objects.


## [0.3.1] - 2019-08-20

### Added

- Project now builds fine on ReadTheDocs
- TravisCI support
- Codecov


## [0.3.0] - 2019-08-16

### Changed

- Changed the old behavior in which every key was converted to lower case.


## [0.2.0] - 2019-07-16

### Added

- Added Sphinx documentation
- Added a `remove_levels` parameter to the config function


## [0.1.0] - 2019-01-16

### Added

- Initial version

[unreleased]: https://github.com/tr11/python-configuration/compare/0.9.1...HEAD
[0.9.1]: https://github.com/tr11/python-configuration/compare/0.9.0...0.9.1
[0.9.0]: https://github.com/tr11/python-configuration/compare/0.8.3...0.9.0
[0.8.3]: https://github.com/tr11/python-configuration/compare/0.8.2...0.8.3
[0.8.2]: https://github.com/tr11/python-configuration/compare/0.8.0...0.8.2
[0.8.0]: https://github.com/tr11/python-configuration/compare/0.7.1...0.8.0
[0.7.1]: https://github.com/tr11/python-configuration/compare/0.7.0...0.7.1
[0.7.0]: https://github.com/tr11/python-configuration/compare/0.6.1...0.7.0
[0.6.1]: https://github.com/tr11/python-configuration/compare/0.6.0...0.6.1
[0.6.0]: https://github.com/tr11/python-configuration/compare/0.5.0...0.6.0
[0.5.0]: https://github.com/tr11/python-configuration/compare/0.4.0...0.5.0
[0.4.0]: https://github.com/tr11/python-configuration/compare/0.3.1...0.4.0
[0.3.1]: https://github.com/tr11/python-configuration/compare/0.3.0...0.3.1
[0.3.0]: https://github.com/tr11/python-configuration/compare/0.2.0...0.3.0
[0.2.0]: https://github.com/tr11/python-configuration/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/tr11/python-configuration/releases/tag/0.1.0
