from fastapi import APIRouter

from app.api.v1 import (
    auth,
    leads,
    ai,
    discovery,
    social,
    social_schedule,
    email,
    whatsapp,
    clients,
    crm,
    content,
    inbox,
    follow_ups,
    notifications,
    settings,
    services,
    search,
    activities,
    health,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
api_router.include_router(social.router, prefix="/social", tags=["social"])
api_router.include_router(social_schedule.router, prefix="/social", tags=["social_schedule"])
api_router.include_router(email.router, prefix="/email", tags=["email"])
api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["whatsapp"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(crm.router, prefix="/crm", tags=["crm"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(inbox.router, prefix="/inbox", tags=["inbox"])
api_router.include_router(follow_ups.router, prefix="/follow-ups", tags=["follow_ups"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(health.router, tags=["health"])
