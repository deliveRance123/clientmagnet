from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    pricing: Optional[str] = Field(None, max_length=255)
    target_clients: Optional[str] = None
    portfolio_links: Optional[str] = None
    is_active: bool = True


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    pricing: Optional[str] = Field(None, max_length=255)
    target_clients: Optional[str] = None
    portfolio_links: Optional[str] = None
    is_active: Optional[bool] = None


class ServiceOut(ServiceBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
