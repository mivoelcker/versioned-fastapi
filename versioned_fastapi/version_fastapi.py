from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, List, Tuple, TypeVar, Union

from fastapi import APIRouter, FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.routing import APIRoute
from starlette.routing import BaseRoute

CallableT = TypeVar("CallableT", bound=Callable[..., Any])


def version(*version: Union[int, str, None]) -> Callable[[CallableT], CallableT]:
    """
    Annotates a route with one or multiple versions.

    :param version:
        One or more versions. Use None to avoid any path modifications.
    """

    def decorator(func: CallableT) -> CallableT:
        func._route_version = [None if v is None else str(v) for v in version]
        return func

    return decorator


class FastApiVersioner:
    title_format: str = "{title}"
    """Defines the format of the swagger title, can contain "{title}" and "{version}"."""
    description_format: str = "## Route version {version}\n{description}"
    """Defines the format of the swagger description, can contain "{description}" and "{version}" and supports markdown."""
    summary_format: str = "{summary}"
    """Defines the format of the swagger summary, can contain "{summary}" and "{version}". Available since OpenAPI 3.1.0, FastAPI 0.99.0."""
    swagger_js_urls: Iterable[str] = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js",
    )
    """The URLs to use to load the Swagger UI JavaScript."""
    swagger_css_urls: Union[Iterable[str], None] = [
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"
    ]
    """The URLs to use to load Swagger UI CSS. Leave None to use FastAPIs default."""
    swagger_favicon_url: Union[str, None] = None
    """The URL of the favicon to use. Leave None to use FastAPIs default."""

    def __init__(
        self,
        app: FastAPI,
        *,
        default_version: Union[int, str, None] = "1",
        prefix_format: str = "/v{version}",
        include_all_routes: bool = True,
        primary_swagger_version: Union[int, str, None] = None,
        filter_tags: bool = False,
    ):
        """
        :param app:
            The FastAPI app.
        :param default_version:
            Default version to use if a route is not annotated with @version.
        :param prefix_format:
            Defines the format of the path prefix, should contain "{version}".
        :param include_all_routes:
            If True, the main openapi route without version prefix will be included in swagger as "All Routes".
        :param primary_swagger_version:
            The version to be displayed when the swagger ui loads.
            If None "All Routes" or the first version will be selected.
        :param filter_tags:
            If True, only tags used by the selected version will be displayed in swagger. Will not effect the "All Routes" version.
        """
        self.app = app
        self.default_version: Union[str, None] = (
            str(default_version) if default_version is not None else None
        )
        self.prefix_format = prefix_format
        self.primary_swagger_version = primary_swagger_version and str(
            primary_swagger_version
        )
        self.include_main_openapi = include_all_routes
        self.filter_tags = filter_tags

    def version_fastapi(self) -> List[str]:
        """
        Versions the fastapi app by adding a prefix to the route's path.

        :return:
            All used versions as sorted list of strings.
        """
        routes_by_version, routes_to_remove = self._get_routes()
        self.app.router.routes = [
            r for r in self.app.router.routes if r not in routes_to_remove
        ]

        for version, routes in routes_by_version.items():
            router = self._create_versioned_router(version, routes)
            self.app.include_router(router)

        versions = sorted(routes_by_version.keys())
        if self.app.openapi_url and self.app.docs_url:
            self._override_swagger_docs(versions)

        return versions

    def _get_routes(self) -> Tuple[Dict[str, List[APIRoute]], List[BaseRoute]]:
        """Gets versions and routes."""
        routes_by_version: Dict[str, List[APIRoute]] = defaultdict(list)
        routes_to_remove: List[BaseRoute] = []

        for route in self.app.routes:
            if isinstance(route, APIRoute):
                route_versions: List[Union[str, None]] = getattr(
                    route.endpoint, "_route_version", [self.default_version]
                )
                for version in route_versions:
                    if version is not None:
                        routes_by_version[version].append(route)
                        routes_to_remove.append(route)
            if getattr(route, "path", None) == self.app.docs_url:
                routes_to_remove.append(route)

        return routes_by_version, routes_to_remove

    def _create_versioned_router(
        self, version: str, routes: List[APIRoute]
    ) -> APIRouter:
        """Creates a routes with all routes."""
        version_prefix = self.prefix_format.format(version=version)
        _router = APIRouter()
        _router.routes.extend(routes)
        router = APIRouter(prefix=version_prefix)
        router.include_router(_router)
        if self.app.openapi_url:
            self._add_openapi_route(version, router)
        return router

    def _add_openapi_route(self, version: str, router: APIRouter):
        """Adds an openapi route to the router."""
        openapi_kwargs = {
            "title": self.title_format.format(title=self.app.title, version=version),
            "description": self.description_format.format(
                description=self.app.description, version=version
            ),
            "version": self.app.version,
            "terms_of_service": self.app.terms_of_service,
            "contact": self.app.contact,
            "license_info": self.app.license_info,
            "openapi_version": self.app.openapi_version,
            "routes": router.routes,
            "tags": self.app.openapi_tags,
            "servers": self.app.servers,
        }
        # Available since OpenAPI 3.1.0, FastAPI 0.99.0.
        if summary := getattr(self.app, "summary", None):
            openapi_kwargs["summary"] = self.summary_format.format(
                summary=summary, version=version
            )
        if webhooks := getattr(self.app, "webhooks", None):
            openapi_kwargs["webhooks"] = webhooks.routes
        # Available since FastAPI 0.102.0
        if separate_schemas := getattr(self.app, "separate_input_output_schemas", None):
            openapi_kwargs["separate_input_output_schemas"] = separate_schemas

        async def get_versioned_openapi(request: Request):
            openapi_definition = get_openapi(**openapi_kwargs)
            if self.filter_tags:
                used_tags = set()
                for path in openapi_definition["paths"].values():
                    for method in path.values():
                        used_tags.update(method.get("tags", []))
                openapi_definition["tags"] = [
                    t for t in openapi_definition["tags"] if t["name"] in used_tags
                ]
            return JSONResponse(openapi_definition)

        router.add_route(
            router.prefix + self.app.openapi_url,  # type: ignore
            get_versioned_openapi,
            include_in_schema=False,
        )

    def _override_swagger_docs(self, versions: List[str]):
        """Overwrites the swagger docs to enable a dropdown menu for version selection."""
        # Swagger api definition urls, see https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
        openapi_urls = []
        if self.include_main_openapi:
            openapi_urls.append({"name": "All Routes", "url": self.app.openapi_url})
        openapi_urls.extend(
            [
                {
                    "name": f"Version {v}",
                    "url": f"{self.prefix_format.format(version=v)}{self.app.openapi_url}",
                }
                for v in versions
            ]
        )
        swagger_html_kwargs = {
            "swagger_js_url": '"></script><script src="'.join(self.swagger_js_urls),
            "swagger_ui_parameters": {
                "layout": "StandaloneLayout",
                "urls": openapi_urls,
            },
            "title": self.app.title + " - Swagger UI",
        }
        if self.primary_swagger_version:
            swagger_html_kwargs["swagger_ui_parameters"][
                "urls.primaryName"
            ] = f"Version {self.primary_swagger_version}"
        if self.swagger_css_urls:
            swagger_html_kwargs[
                "swagger_css_url"
            ] = '"><link type="text/css" rel="stylesheet" href="'.join(
                self.swagger_css_urls
            )
        if self.swagger_favicon_url:
            swagger_html_kwargs["swagger_favicon_url"] = self.swagger_favicon_url

        async def get_versioned_swagger_ui_html(request: Request) -> HTMLResponse:
            root_path = request.scope.get("root_path", "").rstrip("/")
            openapi_url = root_path + self.app.openapi_url  # type: ignore
            oauth2_redirect_url = (
                self.app.swagger_ui_oauth2_redirect_url
                and root_path + self.app.swagger_ui_oauth2_redirect_url
            )
            if root_path:
                for openapi_url in swagger_html_kwargs["swagger_ui_parameters"]["urls"]:
                    openapi_url["url"] = root_path + openapi_url["url"]

            swagger_html_kwargs.update(
                {
                    "openapi_url": openapi_url,  # Will be overridden by 'urls' anyway
                    "oauth2_redirect_url": oauth2_redirect_url,
                }
            )
            if self.app.swagger_ui_parameters:
                swagger_html_kwargs["swagger_ui_parameters"].update(
                    self.app.swagger_ui_parameters
                )

            # It might be better to override get_swagger_ui_html completely instead of modifying its response...
            html_body = get_swagger_ui_html(**swagger_html_kwargs).body
            html_body = html_body.replace(
                b"SwaggerUIBundle.SwaggerUIStandalonePreset",
                b"SwaggerUIStandalonePreset",
            )
            html_body = html_body.replace(
                b"<body>", b"<body style='margin:0;padding:0'>"
            )
            return HTMLResponse(html_body)

        self.app.add_route(
            self.app.docs_url,  # type: ignore
            get_versioned_swagger_ui_html,
            include_in_schema=False,
        )
