from pathlib import Path
from typing import Dict, List, Union

import uvicorn
from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel, Field

from versioned_fastapi import version, FastApiVersioner

# Example db
db: Dict[int, "Item"] = {}


# Versioned models
class Item(BaseModel):
    id: int
    name: str
    description: Union[str, None] = None


class ItemV2(Item):
    description: str


class ItemV3(ItemV2):
    price: int = Field(description="Item price in cent", examples=[199])


# Create the FastAPI app ...
app = FastAPI(
    title="Simple example API",
    description="Simple example of Versioned FastAPI.",
)

# ... and routers as normal
items_router = APIRouter(prefix="/items", tags=["Items"])


# Use the @version annotation to add a version
# Versioned FastAPI will add the prefix "/v1" to this route
@version(1)
@items_router.post("", status_code=201, deprecated=True)
async def create_item(item: Item):
    db[item.id] = item
    return item


@version(1)
@items_router.get("")
async def get_items() -> List[Item]:
    return list(db.values())


@version(1)
@items_router.get("/{item_id}")
async def get_item(item_id: int) -> Item:
    if item_id in db:
        return db[item_id]
    raise HTTPException(status_code=404, detail="Item not found")


@version(2)
@items_router.post("", status_code=201, deprecated=True)
async def create_item_v2(item: ItemV2) -> ItemV2:
    db[item.id] = item
    return item


@version(2)
@items_router.get("/{item_id}")
async def get_item_v2(item_id: int) -> ItemV2:
    item = db.get(item_id)
    if isinstance(item, ItemV2):
        return item
    raise HTTPException(status_code=404, detail="Item not found")


@version(3)
@items_router.post("", status_code=201)
async def create_item_v3(item: ItemV3) -> ItemV3:
    db[item.id] = item
    return item


# You can pass None to avoid any modification to a route
@version(None)
@app.get("/health")
async def get_health() -> str:
    return "OK"


app.include_router(items_router)

# Version your app
# It will add version prefixes and customize the swagger docs
versions = FastApiVersioner(
    app,
).version_fastapi()


if __name__ == "__main__":
    uvicorn.run(
        f"{Path(__file__).stem}:app",
        reload=True,
        reload_dirs=[".", "../versioned_fastapi"],
    )
