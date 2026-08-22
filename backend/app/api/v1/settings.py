from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_session,
    get_unified_inbox_service,
)
from app.models.user import User
from app.schemas.unified_inbox import (
    UserCommunicationPreferencesOut,
    UserCommunicationPreferencesUpdate,
)
from app.services.unified_inbox import UnifiedInboxService

router = APIRouter()


class UserBusinessProfileOut(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    email: str
    business_description: Optional[str] = None
    business_website: Optional[str] = None
    portfolio_links_json: Optional[str] = None
    preferred_tone: Optional[str] = None
    default_signature: Optional[str] = None
    business_intro: Optional[str] = None
    preferred_cta: Optional[str] = None
    notify_new_lead: bool = True
    notify_new_reply: bool = True
    notify_follow_up_due: bool = True
    notify_post_failed: bool = True
    notify_account_warning: bool = True


class UserBusinessProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    business_description: Optional[str] = None
    business_website: Optional[str] = None
    portfolio_links_json: Optional[str] = None
    preferred_tone: Optional[str] = None
    default_signature: Optional[str] = None
    business_intro: Optional[str] = None
    preferred_cta: Optional[str] = None
    notify_new_lead: Optional[bool] = None
    notify_new_reply: Optional[bool] = None
    notify_follow_up_due: Optional[bool] = None
    notify_post_failed: Optional[bool] = None
    notify_account_warning: Optional[bool] = None


@router.get(
    "/business-profile",
    response_model=UserBusinessProfileOut,
    summary="Get user profile, business information, and notification settings",
)
async def get_business_profile(
    current_user: User = Depends(get_current_active_user),
):
    return UserBusinessProfileOut(
        full_name=current_user.full_name,
        company_name=current_user.company_name,
        email=current_user.email,
        business_description=current_user.business_description,
        business_website=current_user.business_website,
        portfolio_links_json=current_user.portfolio_links_json,
        preferred_tone=current_user.preferred_tone,
        default_signature=current_user.default_signature,
        business_intro=current_user.business_intro,
        preferred_cta=current_user.preferred_cta,
        notify_new_lead=current_user.notify_new_lead,
        notify_new_reply=current_user.notify_new_reply,
        notify_follow_up_due=current_user.notify_follow_up_due,
        notify_post_failed=current_user.notify_post_failed,
        notify_account_warning=current_user.notify_account_warning,
    )


@router.patch(
    "/business-profile",
    response_model=UserBusinessProfileOut,
    summary="Update user profile, business information, and notification settings",
)
async def update_business_profile(
    payload: UserBusinessProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()
    if payload.company_name is not None:
        current_user.company_name = payload.company_name.strip()
    if payload.business_description is not None:
        current_user.business_description = payload.business_description.strip()
    if payload.business_website is not None:
        current_user.business_website = payload.business_website.strip()
    if payload.portfolio_links_json is not None:
        current_user.portfolio_links_json = payload.portfolio_links_json
    if payload.preferred_tone is not None:
        current_user.preferred_tone = payload.preferred_tone
    if payload.default_signature is not None:
        current_user.default_signature = payload.default_signature
    if payload.business_intro is not None:
        current_user.business_intro = payload.business_intro
    if payload.preferred_cta is not None:
        current_user.preferred_cta = payload.preferred_cta
    if payload.notify_new_lead is not None:
        current_user.notify_new_lead = payload.notify_new_lead
    if payload.notify_new_reply is not None:
        current_user.notify_new_reply = payload.notify_new_reply
    if payload.notify_follow_up_due is not None:
        current_user.notify_follow_up_due = payload.notify_follow_up_due
    if payload.notify_post_failed is not None:
        current_user.notify_post_failed = payload.notify_post_failed
    if payload.notify_account_warning is not None:
        current_user.notify_account_warning = payload.notify_account_warning

    await db.commit()
    await db.refresh(current_user)

    return UserBusinessProfileOut(
        full_name=current_user.full_name,
        company_name=current_user.company_name,
        email=current_user.email,
        business_description=current_user.business_description,
        business_website=current_user.business_website,
        portfolio_links_json=current_user.portfolio_links_json,
        preferred_tone=current_user.preferred_tone,
        default_signature=current_user.default_signature,
        business_intro=current_user.business_intro,
        preferred_cta=current_user.preferred_cta,
        notify_new_lead=current_user.notify_new_lead,
        notify_new_reply=current_user.notify_new_reply,
        notify_follow_up_due=current_user.notify_follow_up_due,
        notify_post_failed=current_user.notify_post_failed,
        notify_account_warning=current_user.notify_account_warning,
    )


@router.get(
    "/communication-preferences",
    response_model=UserCommunicationPreferencesOut,
    summary="Get user communication and AI drafting preferences",
)
async def get_communication_preferences(
    current_user: User = Depends(get_current_active_user),
    service: UnifiedInboxService = Depends(get_unified_inbox_service),
):
    return await service.get_preferences(user=current_user)


@router.patch(
    "/communication-preferences",
    response_model=UserCommunicationPreferencesOut,
    summary="Update user communication and AI drafting preferences",
)
async def update_communication_preferences(
    payload: UserCommunicationPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    service: UnifiedInboxService = Depends(get_unified_inbox_service),
):
    return await service.update_preferences(db=db, user=current_user, data=payload)
