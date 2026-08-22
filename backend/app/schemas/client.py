from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class ClientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    status: str = Field("Active", max_length=50)
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    lead_id: Optional[str] = Field(None, max_length=36)


class ClientOut(ClientBase):
    id: str
    user_id: str
    lead_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
