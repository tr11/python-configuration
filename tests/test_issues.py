from config import ConfigurationSet, config_from_dict


def test_issue_49():  # type: ignore
    d = {"path": {"to": {"value-a": "A", "value-b": "B"}}}
    base_cfg = config_from_dict(d)

    d = {"path": {"to": {"value-a": "C"}}}

    cfg = config_from_dict(d)
    cfg_set = ConfigurationSet(cfg, base_cfg)

    path_config = cfg_set.get("path")

    assert path_config == {"to.value-a": "C", "to.value-b": "B"}
