import random
from datetime import datetime
from pathlib import Path
from typing import Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, PrivateAttr

from versioned_fastapi import FastApiVersioner, version


class Cookie(BaseModel):
    """Cookie recipe. Units may have been lost in translation..."""

    _timestamp: datetime = PrivateAttr(default_factory=datetime.now)
    butter: float
    chocolate: float
    eggs: int
    flour: float
    salt: float
    sugar: float
    vanilla: float
    heat: float
    baking_time: float


oven: Dict[int, Cookie] = {}

# All FastAPI parameters should be work as intended
app = FastAPI(
    title="Customized example API",
    description="Use FastAPI parameters to customize your app as usual.",
    summary="Customized example of Versioned FastAPI",
    version="1.2.3",
    openapi_url="/swagger.json",
    openapi_tags=[
        {"name": "Cookies", "description": "Cookies are delicious."},
        {"name": "Cake", "description": "The cake is a lie."},
    ],
    servers=[
        {"url": "http://localhost:8000", "description": "Localhost"},
        {"url": "http://127.0.0.1:8000", "description": "Loopback"},
    ],
    docs_url="/swagger",
    redoc_url=None,
    swagger_ui_oauth2_redirect_url="/swagger/oauth2-redirect",
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"},
)


# You can add multiple versions
@version(1, 2)
@app.post("/cookies", status_code=202, tags=["Cookies"])
async def bake_cookie(cookie: Cookie) -> int:
    cookie_id = random.randint(0, 127)  # Seems fine...
    oven[cookie_id] = cookie
    return cookie_id


@version(1)
@app.get("/cookies/{cookie_id}", status_code=200, deprecated=True, tags=["Cookies"])
async def get_cookie(cookie_id: int) -> str:
    """Returns cookie, but cookie might be burned or not backed enough."""
    if cookie_id not in oven:
        raise HTTPException(status_code=404, detail="Cookie not found.")
    oven.pop(cookie_id)
    return "🍪"


# If @version in missing, the default version (here v2) will be used
@app.get("/cookies/{cookie_id}", status_code=200, tags=["Cookies"])
async def get_cookie_default_version(cookie_id: int):
    """Returns perfectly backed cookie."""
    if cookie_id not in oven:
        raise HTTPException(status_code=404, detail="Cookie not found.")

    cookie = oven.pop(cookie_id)
    current_baking_time = (datetime.now() - cookie._timestamp).total_seconds()
    if current_baking_time < 0.9 * cookie.baking_time:
        oven[cookie_id] = cookie
        raise HTTPException(
            status_code=412, detail="Too early, cookie is not yet backed."
        )
    if current_baking_time > 1.1 * cookie.baking_time:
        raise HTTPException(
            status_code=410,
            detail="Too late, cookie is burned.",
        )
    return "🍪"


@version(1)
@app.get("/cake", tags=["Cake"])
async def get_cake():
    raise HTTPException(status_code=404, detail="The cake is a lie.")


# FastApiVersioner offers some further customization
versioner = FastApiVersioner(
    app,
    default_version=2,  # Default if no version provided
    prefix_format="/version{version}",  # Modify prefix format
    include_all_routes=False,  # Removes 'All Routes' from swagger docs
    primary_swagger_version=2,  # Swagger ui will load with version 2 as default
    filter_tags=True,  # Remove tags defined in 'openapi_tags' that are not used in any route
)
# For even more customizations, you can override some class variables
versioner.title_format = "{title} - Version {version}"
versioner.description_format = "{description}"
versioner.summary_format = "{summary} - Version {version}"
versioner.swagger_favicon_url = "https://www.google.com/favicon.ico"
versioner.swagger_css_urls = (
    "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
)

versions = versioner.version_fastapi()

if __name__ == "__main__":
    uvicorn.run(
        f"{Path(__file__).stem}:app",
        reload=True,
        reload_dirs=[".", "../versioned_fastapi"],
    )
