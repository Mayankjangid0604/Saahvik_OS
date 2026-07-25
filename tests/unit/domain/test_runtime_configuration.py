from enterprise_os.domain.ceo.runtime_configuration import RuntimeConfiguration


def test_runtime_configuration_rejects_negative_loop_interval() -> None:
    try:
        RuntimeConfiguration.from_mapping(
            {
                "runtime_name": "EnterpriseOS",
                "log_level": "INFO",
                "loop_interval_seconds": -1,
            }
        )
    except ValueError as exc:
        assert "loop_interval_seconds" in str(exc)
    else:
        raise AssertionError("RuntimeConfiguration should reject negative intervals")
