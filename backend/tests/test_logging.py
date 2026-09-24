import json
import logging

from app.core.logging import JsonFormatter


def test_json_formatter_outputs_structured_record() -> None:
    record = logging.LogRecord(
        name="aspa.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request complete",
        args=(),
        exc_info=None,
    )
    record.method = "GET"
    record.path = "/ready"
    payload = json.loads(JsonFormatter().format(record))
    assert payload["level"] == "INFO"
    assert payload["logger"] == "aspa.test"
    assert payload["message"] == "request complete"
    assert payload["method"] == "GET"
    assert payload["path"] == "/ready"
    assert payload["timestamp"]
