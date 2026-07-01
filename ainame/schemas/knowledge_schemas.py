from datetime import datetime

from pydantic import BaseModel


class KnowledgeFileOutSchema(BaseModel):
    id: int
    filename: str
    file_path: str
    file_type: str | None = None
    file_size: int | None = None
    status: str
    error_message: str | None = None
    retry_count: int = 0
    is_deleted: bool = False
    processed_at: datetime | None = None
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
