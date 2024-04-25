from pathlib import Path

import uvicorn
from fastapi import FastAPI

from versioned_fastapi import FastApiVersioner, version

# The main app
app = FastAPI(
    title="App with mounted sub applications",
)


# Main app can have normal routes
@version(1)
@app.get("/")
async def root_v1() -> dict:
    return {"message": "Hello World"}


@version(2)
@app.get("/")
async def root_v2() -> dict:
    return {"message": "Hello Universe"}


# Create a sub application as normal (https://fastapi.tiangolo.com/advanced/sub-applications/)
admin_app = FastAPI(title="A admins page as sub application")


@version(1)
@admin_app.get("/")
async def admin_root_v1() -> dict:
    return {"message": "Hello Admin"}


@version(2)
@admin_app.get("/")
async def admin_root_v2() -> dict:
    return {"message": "Hello Superadmin"}


FastApiVersioner(
    app,
).version_fastapi()

FastApiVersioner(
    admin_app,
).version_fastapi()

app.mount("/admin", admin_app)

if __name__ == "__main__":
    uvicorn.run(
        f"{Path(__file__).stem}:app",
        reload=True,
        reload_dirs=[".", "../versioned_fastapi"],
    )
