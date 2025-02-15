from fastapi import FastAPI,__version__
from datetime import time, datetime
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.get("/")
async def hello():
    return {'res': 'pong', 'version': __version__, "time": time()}


@app.get("/healthcheck")
async def healthcheck():
    return {'status': True, 'version': __version__, "time": datetime.now().isoformat()}

@app.post('/item')
async def create_item(item: Item):
    isotime = datetime.now().isoformat()
    return {'status': True,
            'version': __version__,
            'time': isotime,
            'item': item.model_dump_json()
            }

