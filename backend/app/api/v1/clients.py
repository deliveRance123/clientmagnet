from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db_session
from app.models.client import Client
from app.models.lead import Lead
from app.models.user import User
from app.schemas.client import ClientCreate, ClientOut

router = APIRouter()


@router.get(
    "/",
    response_model=List[ClientOut],
    status_code=status.HTTP_200_OK,
    summary="List all clients owned by the authenticated user",
)
async def get_clients(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieves all clients owned by the authenticated user.
    """
    query = (
        select(Client)
        .where(Client.user_id == current_user.id)
        .order_by(Client.name.asc())
    )
    result = await db.execute(query)
    clients = result.scalars().all()
    return [ClientOut.model_validate(client) for client in clients]


@router.post(
    "/",
    response_model=ClientOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create/promote a new client for the authenticated user",
)
async def create_client(
    client_in: ClientCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Creates a new client. Optionally links to a lead if lead_id is provided.
    """
    if client_in.lead_id:
        lead_query = select(Lead).where(
            Lead.id == client_in.lead_id, Lead.user_id == current_user.id
        )
        lead_result = await db.execute(lead_query)
        lead = lead_result.scalar_one_or_none()
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referenced lead not found or access denied.",
            )

    new_client = Client(
        user_id=current_user.id,
        lead_id=client_in.lead_id,
        name=client_in.name.strip(),
        company=client_in.company.strip() if client_in.company else None,
        email=client_in.email,
        status=client_in.status.strip(),
        notes=client_in.notes.strip() if client_in.notes else None,
    )
    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)
    return ClientOut.model_validate(new_client)
