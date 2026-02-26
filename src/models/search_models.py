from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from src.settings import DEFAULT_RESULT_LIMIT, MAX_RESULT_LIMIT


class SearchInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    query: str = Field(min_length=1, max_length=2000)
    project_id: Optional[str] = Field(None, alias="projectId")
    limit: int = Field(default=DEFAULT_RESULT_LIMIT, ge=1, le=MAX_RESULT_LIMIT)
