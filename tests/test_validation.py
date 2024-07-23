"""Validation tests."""

# ruff: noqa: D103

import pytest
from config import (
    config_from_dict,
)

try:
    import jsonschema
except ImportError:
    jsonschema = None


@pytest.mark.skipif("jsonschema is None")
def test_validation_ok():  # type: ignore
    d = {"items": [1, 3]}
    cfg = config_from_dict(d)

    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {"enum": [1, 2, 3]},
                "maxItems": 2,
            },
        },
    }

    assert cfg.validate(schema)


@pytest.mark.skipif("jsonschema is None")
def test_validation_fail():  # type: ignore
    from jsonschema.exceptions import ValidationError

    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {"enum": [1, 2, 3]},
                "maxItems": 2,
            },
        },
    }

    with pytest.raises(ValidationError) as err:
        d = {"items": [1, 4]}
        cfg = config_from_dict(d)
        assert not cfg.validate(schema)
        cfg.validate(schema, raise_on_error=True)
    assert "4 is not one of [1, 2, 3]" in str(err)

    with pytest.raises(ValidationError) as err:
        d = {"items": [1, 2, 3]}
        cfg = config_from_dict(d)
        assert not cfg.validate(schema)
        cfg.validate(schema, raise_on_error=True)
    assert "[1, 2, 3] is too long" in str(err)


@pytest.mark.skipif("jsonschema is None")
def test_validation_format():  # type: ignore
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import ValidationError

    schema = {
        "type": "object",
        "properties": {
            "ip": {"format": "ipv4"},
        },
    }

    cfg = config_from_dict({"ip": "10.0.0.1"})
    assert cfg.validate(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    # this passes since we didn't specify the format checker
    cfg = config_from_dict({"ip": "10"})
    assert cfg.validate(schema)

    # fails with the format checker
    with pytest.raises(ValidationError) as err:
        cfg = config_from_dict({"ip": "10"})
        cfg.validate(
            schema,
            raise_on_error=True,
            format_checker=Draft202012Validator.FORMAT_CHECKER,
        )
    assert "'10' is not a 'ipv4'" in str(err)


@pytest.mark.skipif("jsonschema is None")
def test_validation_nested():  # type: ignore
    d = {"item": {"sub1": 1, "sub2": "abc"}}
    cfg = config_from_dict(d)

    schema = {
        "type": "object",
        "properties": {
            "item.sub1": {"type": "number"},
            "item.sub2": {"type": "string"},
        },
        "required": ["item.sub1", "item.sub2"],
    }
    assert cfg.validate(schema)

    schema = {
        "type": "object",
        "properties": {
            "item": {
                "type": "object",
                "properties": {
                    "sub1": {"type": "number"},
                    "sub2": {"type": "string"},
                },
                "required": ["sub1", "sub2"],
            },
        },
        "required": ["item"],
    }
    assert cfg.validate(schema, nested=True)
