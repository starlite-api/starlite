from asyncio import sleep
from functools import lru_cache
from typing import Any, Optional, cast

import pytest
from pydantic import BaseConfig
from pydantic.fields import ModelField
from starlette.requests import Request
from starlette.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)
from starlette.responses import Response as StarletteResponse
from starlette.responses import StreamingResponse
from starlette.status import HTTP_200_OK, HTTP_204_NO_CONTENT

from starlite import (
    HttpMethod,
    ImproperlyConfiguredException,
    Provide,
    Response,
    get,
    route,
)
from starlite.request import (
    create_function_signature_model,
    get_kwargs_from_request,
    handle_request,
    parse_query_params,
)
from starlite.testing import create_test_request
from tests.utils import Person, PersonFactory


def test_parse_query_params():
    query = {
        "value": 10,
        "veggies": ["tomato", "potato", "aubergine"],
        "calories": 122.53,
        "healthy": True,
        "polluting": False,
    }
    request = create_test_request(query=query)
    result = parse_query_params(request=request)
    assert result == query


@pytest.mark.asyncio
async def test_get_kwargs_from_request():
    class Config(BaseConfig):
        arbitrary_types_allowed = True

    person_instance = PersonFactory.build()
    fields = {
        **Person.__fields__,
        "data": ModelField(name="data", type_=Person, class_validators=[], model_config=Config),
        "headers": ModelField(name="headers", type_=dict, class_validators=[], model_config=Config),
        "request": ModelField(name="request", type_=Request, class_validators=[], model_config=Config),
    }
    request = create_test_request(
        content=person_instance, headers={"MyHeader": "xyz"}, query={"user": "123"}, http_method=HttpMethod.POST
    )
    result = await get_kwargs_from_request(request=request, fields=fields)
    assert result["data"]
    assert result["headers"]
    assert result["request"]


def test_create_function_signature_model_parameter_parsing():
    @get()
    def my_fn(a: int, b: str, c: Optional[bytes], d: bytes = b"123", e: Optional[dict] = None):
        pass

    model = create_function_signature_model(my_fn.fn)
    fields = model.__fields__
    assert fields.get("a").type_ == int
    assert fields.get("a").required
    assert fields.get("b").type_ == str
    assert fields.get("b").required
    assert fields.get("c").type_ == bytes
    assert fields.get("c").allow_none
    assert fields.get("c").default is None
    assert fields.get("d").type_ == bytes
    assert fields.get("d").default == b"123"
    assert fields.get("e").type_ == dict
    assert fields.get("e").allow_none
    assert fields.get("e").default is None


def test_create_function_signature_model_ignore_return_annotation():
    @get(path="/health", status_code=HTTP_204_NO_CONTENT)
    async def health_check() -> None:
        return

    assert create_function_signature_model(health_check.fn)().dict() == {}


def test_create_function_signature_model_validation():
    provide = Provide(lru_cache(maxsize=0)(lambda x: x))

    with pytest.raises(ImproperlyConfiguredException):
        create_function_signature_model(provide.dependency)


@pytest.mark.asyncio
async def test_handle_request_async_await():
    @route(http_method=HttpMethod.POST, path="/person")
    async def test_function(data: Person):
        assert isinstance(data, Person)
        await sleep(0.1)
        return data

    person_instance = PersonFactory.build()
    request = create_test_request(content=person_instance, http_method=HttpMethod.POST)

    response = await handle_request(route_handler=cast(Any, test_function), request=request)
    assert response.body.decode("utf-8") == person_instance.json()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        Response(status_code=HTTP_200_OK, content=b"abc"),
        StarletteResponse(status_code=HTTP_200_OK, content=b"abc"),
        PlainTextResponse(content="abc"),
        HTMLResponse(content="<div><span/></div"),
        JSONResponse(status_code=HTTP_200_OK, content={}),
        RedirectResponse(url="/person"),
        StreamingResponse(status_code=HTTP_200_OK, content=b"abc"),
        FileResponse("./test_request.py"),
    ],
)
async def test_handle_request_when_handler_returns_starlette_responses(response):
    @get(path="/test")
    def test_path():
        return response

    request = create_test_request(content=None, http_method=HttpMethod.GET)
    assert await handle_request(route_handler=cast(Any, test_path), request=request) == response


@pytest.mark.asyncio
async def test_handle_request_redirect_response():
    @get(path="/test", response_class=RedirectResponse)
    def test_path():
        return "/somewhere-else"

    request = create_test_request(content=None, http_method=HttpMethod.GET)
    response = await handle_request(route_handler=cast(Any, test_path), request=request)
    assert isinstance(response, RedirectResponse)
    assert response.headers["location"] == "/somewhere-else"