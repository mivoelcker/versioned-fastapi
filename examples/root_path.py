from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request

from version_fastapi import version, FastApiVersioner

app = FastAPI(root_path="/root/path")


@version(1)
@app.get("/app")
def read_main(request: Request):
    return {"message": "Hello World", "root_path": request.scope.get("root_path")}


@version(2)
@app.get("/app")
def read_main(request: Request):
    return {"message": "Hello New World", "root_path": request.scope.get("root_path")}


versions = FastApiVersioner(app).version_fastapi()

if __name__ == '__main__':
    uvicorn.run(f"{Path(__file__).stem}:app", reload=True, reload_dirs=[".", "../versioned_fastapi"])
