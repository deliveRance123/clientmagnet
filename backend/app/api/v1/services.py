from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db_session
from app.models.service import Service
from app.models.user import User
from app.schemas.service import ServiceCreate, ServiceOut, ServiceUpdate

router = APIRouter()


@router.get(
    "/",
    response_model=List[ServiceOut],
    status_code=status.HTTP_200_OK,
    summary="List all services offered by the authenticated user",
)
async def get_services(
    active_only: bool = Query(False, description="Filter for active services only"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieves all services owned by the authenticated user.
    """
    query = select(Service).where(Service.user_id == current_user.id)
    if active_only:
        query = query.where(Service.is_active.is_(True))
    query = query.order_by(Service.name.asc())

    result = await db.execute(query)
    services = result.scalars().all()
    return [ServiceOut.model_validate(service) for service in services]


@router.post(
    "/",
    response_model=ServiceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new service offered by the authenticated user",
)
async def create_service(
    service_in: ServiceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Creates a new service offered by the authenticated user.
    """
    new_service = Service(
        user_id=current_user.id,
        name=service_in.name.strip(),
        description=service_in.description.strip() if service_in.description else None,
        pricing=service_in.pricing.strip() if service_in.pricing else None,
        target_clients=service_in.target_clients.strip() if service_in.target_clients else None,
        portfolio_links=service_in.portfolio_links.strip() if service_in.portfolio_links else None,
        is_active=service_in.is_active,
    )
    db.add(new_service)
    await db.commit()
    await db.refresh(new_service)
    return ServiceOut.model_validate(new_service)


@router.get(
    "/{service_id}",
    response_model=ServiceOut,
    status_code=status.HTTP_200_OK,
    summary="Get service details by ID",
)
async def get_service_by_id(
    service_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieves a service by ID only if it belongs to the authenticated user.
    """
    query = select(Service).where(
        Service.id == service_id, Service.user_id == current_user.id
    )
    result = await db.execute(query)
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or access denied.",
        )

    return ServiceOut.model_validate(service)


@router.patch(
    "/{service_id}",
    response_model=ServiceOut,
    status_code=status.HTTP_200_OK,
    summary="Update a service",
)
async def update_service(
    service_id: str,
    service_in: ServiceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Updates a service owned by the authenticated user.
    """
    query = select(Service).where(
        Service.id == service_id, Service.user_id == current_user.id
    )
    result = await db.execute(query)
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or access denied.",
        )

    update_data = service_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(service, field, value)

    await db.commit()
    await db.refresh(service)
    return ServiceOut.model_validate(service)


@router.patch(
    "/{service_id}/toggle",
    response_model=ServiceOut,
    status_code=status.HTTP_200_OK,
    summary="Toggle active status of a service",
)
async def toggle_service_active(
    service_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Toggles the is_active flag of a service.
    """
    query = select(Service).where(
        Service.id == service_id, Service.user_id == current_user.id
    )
    result = await db.execute(query)
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or access denied.",
        )

    service.is_active = not service.is_active
    await db.commit()
    await db.refresh(service)
    return ServiceOut.model_validate(service)


@router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a service",
)
async def delete_service(
    service_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Deletes a service owned by the authenticated user.
    """
    query = select(Service).where(
        Service.id == service_id, Service.user_id == current_user.id
    )
    result = await db.execute(query)
    service = result.scalar_one_or_none()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or access denied.",
        )

    await db.delete(service)
    await db.commit()
    return None
