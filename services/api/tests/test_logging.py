import json
import logging

from django.http import HttpResponse
from django.test import RequestFactory

from config.logging_utils import JsonFormatter, RequestIdFilter, request_id_var
from config.middleware import RequestIdMiddleware


def _record(msg: str) -> logging.LogRecord:
    record = logging.LogRecord("t", logging.INFO, __file__, 1, msg, None, None)
    RequestIdFilter().filter(record)
    return record


def test_log_lines_are_json_with_required_fields() -> None:
    line = JsonFormatter().format(_record("hello"))
    data = json.loads(line)
    assert {"timestamp", "level", "logger", "message", "request_id"} <= data.keys()
    assert data["message"] == "hello"


def test_request_id_is_in_logs_during_a_request() -> None:
    seen: list[str] = []

    def view(request: object) -> HttpResponse:
        seen.append(json.loads(JsonFormatter().format(_record("x")))["request_id"])
        return HttpResponse("ok")

    request = RequestFactory().get("/", headers={"X-Request-ID": "abc-12345678"})
    response = RequestIdMiddleware(view)(request)
    assert seen == ["abc-12345678"]
    assert response["X-Request-ID"] == "abc-12345678"
    assert request_id_var.get() == "-"  # context restored after the request


def test_unsafe_client_request_id_is_replaced() -> None:
    request = RequestFactory().get("/", headers={"X-Request-ID": "bad id\nforged=1"})
    response = RequestIdMiddleware(lambda r: HttpResponse("ok"))(request)
    assert response["X-Request-ID"] != "bad id\nforged=1"
    assert "\n" not in response["X-Request-ID"]
