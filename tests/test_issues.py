from config import (
    Configuration,
    ConfigurationSet,
    EnvConfiguration,
    config,
    config_from_dict,
)


def test_issue_49():  # type: ignore
    d = {"path": {"to": {"value-a": "A", "value-b": "B"}}}
    base_cfg = config_from_dict(d)

    d = {"path": {"to": {"value-a": "C"}}}

    cfg = config_from_dict(d)
    cfg_set = ConfigurationSet(cfg, base_cfg)

    path_config = cfg_set.get("path")

    assert path_config == {"to.value-a": "C", "to.value-b": "B"}


def test_issue_63_a():  # type: ignore
    import os
    import tempfile

    ini = "[APP_NAME]\nfoo = bar\n\n[ANOTHER_APP]\nspam = egg"
    os.environ.update([("APP_NAME_EASTER", "egg")])

    with tempfile.NamedTemporaryFile(suffix=".ini") as f:
        f.file.write(ini.encode())
        f.file.flush()
        configs = config(f.name, "env", prefix="APP_NAME", separator="_")
        assert configs == {
            "APP_NAME": {"foo": "bar"},
            "EASTER": "egg",
            "ANOTHER_APP": {"spam": "egg"},
        }


def test_issue_63_b():  # type: ignore
    import os
    import tempfile

    ini = "[APP_NAME]\nfoo = bar\n\n[ANOTHER_APP]\nspam = egg"
    os.environ.update([("PREFIX__APP_NAME__EASTER", "egg")])

    with tempfile.NamedTemporaryFile(suffix=".ini") as f:
        f.file.write(ini.encode())
        f.file.flush()
        configs = config(f.name, "env", prefix="PREFIX", separator="__")
        assert configs == {
            "APP_NAME": {
                "foo": "bar",
                "EASTER": "egg",
            },
            "ANOTHER_APP": {"spam": "egg"},
        }


def test_issue_77():  # type: ignore
    env = EnvConfiguration(prefix="whatever")
    print(repr(env))
    assert repr(env).startswith("<EnvConfiguration")


def test_issue_78():  # type: ignore
    c = Configuration({})
    c == None


def test_issue_79():  # type: ignore
    import collections

    conf = Configuration({})
    data = collections.ChainMap({"abc": {"def": "ghi"}})
    conf.update(data)

    assert conf["abc.def"] == "ghi"
