# Route Handlers

Route handlers are the core of Starlite. They are constructed by decorating a function or method with one of the handler
decorators exported from Starlite.

The base decorator is called `route`:

```python
from starlite import HttpMethod, route


@route(path="/my-endpoint", http_method=[HttpMethod.GET, HttpMethod.POST])
def my_endpoint() -> None:
    ...

```

What route does is wrap the given function or class method and replace it with an instance of the class `RouteHandler`.
In fact, route is merely an alias for `RouteHandler`, thus you could have done this instead:

```python
from starlite import HttpMethod, RouteHandler


@RouteHandler(path="/my-endpoint", http_method=[HttpMethod.GET, HttpMethod.POST])
def my_endpoint() -> None:
    ...

```

⚠️ **Important**: A function decorated by `route` or any of the other decorators discussed below **must** have an
annotated return value, even if the return value is `None` as in the above example. This limitation is enforced to
ensure consistent schema generation, as well as stronger typing.

The `route` decorator accepts the following required kwargs -

* `path` (**required**) - a path string, with or without [path parameters](#path-parameters).
* `http_method` (**required**) - a member of the enum `starlite.enums.HttpMethod` or a list of members,
  e.g. `HttpMethod.GET` or `[HttpMethod.Patch, HttpMethod.Put]`.

Additionally, you can pass the following optional kwargs:

* `status_code`: the status code for a success response. If not
  specified, [a default value will be used](4-responses.md#status-codes), unless you specify more than one http method,
  in which case you must specify a value or an exception will be raised.
* `media_type`: A string or a member of the enum `starlite.enums.MediaType`, which specifies the MIME Media Type for the
  response. Defaults to `MediaType.JSON`. See [media-type](4-responses.md#media-type).
* `response_class`: The response class to use. The value must be a subclass of `starlite.Response`.
  See [using custom responses](4-responses.md#using-custom-responses).
* `response_headers`: A dictionary of `ResponseHeader` instances.
* `dependencies`: A dictionary of `Provide` instances. See [dependency-injection](5-dependency-injection.md)
* `include_in_schema`: A boolean flag dictating whether the given route handler will appear in the generated OpenAPI
  schema. Defaults to `True`.
* `tags`: a list of openapi-pydantic `Tag` models, which correlate to
  the [tag specification](https://spec.openapis.org/oas/latest.html#tag-object).
* `summary`: Text used for the route's schema _summary_ section.
* `description`: Text used for the route's schema _description_ section.
* `response_description`: Text used for the route's response schema _description_ section.
* `operation_id`: An identifier used for the route's schema _operationId_. Defaults to the `__name__` of the wrapped
  function.
* `deprecated`: A boolean dictating whether this route should be marked as deprecated in the OpenAPI schema. Defaults
  to `False`.
* `raises`: A list of exception classes extending from `starlite.HttpException`. This list should describe all
  exceptions raised within the route handler's function/method. The Starlite `ValidationException` will be added
  automatically for the schema if any validation is involved.

## Semantic Handler Decorators

Starlite also includes "semantic" decorators, that is, decorators the pre-set the `http_method` kwarg to a specific HTTP
verb, which correlates with their name:

* `delete`
* `get`
* `patch`
* `post`
* `put`

These are used exactly like `route` with the sole exception that you cannot configure the `http_method`:

```python
from typing import List

from starlite import delete, get, patch, post, put

from my_api.models import Resource


@get(path="/resources")
def list_resources() -> List[Resource]:
    ...


@post(path="/resources")
def create_resource() -> Resource:
    ...


@get(path="/resources/{pk:int}")
def retrieve_resource(pk: int) -> Resource:
    ...


@put(path="/resources/{pk:int}")
def update_resource(pk: int) -> Resource:
    ...


@patch(path="/resources/{pk:int}")
def partially_update_resource(pk: int) -> Resource:
    ...


@delete(path="/resources/{pk:int}")
def delete_resource(pk: int) -> None:
    ...
```

Although these decorators are merely subclasses of `PathHandler` that pre-set the `http_method`, using  _get_, _patch_
, _put_, _delete_ or _post_ instead of _route_ makes the code clearer and simpler.

Furthermore, in the OpenAPI specification each unique combination of http verb (e.g. "GET", "POST" etc.) and path is
regarded as a distinct [operation](https://spec.openapis.org/oas/latest.html#operation-object), and each operation
should be distinguished by a unique `operationId` and optimally also have a `summary` and `description` sections.

As such, using the `route` decorator is discouraged. Instead, the preferred pattern is to share code using secondary
class methods or by abstracting code to reusable functions.