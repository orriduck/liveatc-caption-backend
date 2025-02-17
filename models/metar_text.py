from typing import List, Optional

from pydantic import BaseModel


class MetarText(BaseModel):
    query: str