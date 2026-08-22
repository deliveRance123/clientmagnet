import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.seed import seed_development_data
from app.models.user import User
from app.models.service import Service


@pytest.mark.asyncio
async def test_seed_development_data(db_session: AsyncSession):
    # 1. Run seed data
    await seed_development_data(db_session)
    
    # 2. Query test user
    user_query = select(User).where(User.email == "dev@clientmagnet.local")
    user_result = await db_session.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    assert user is not None
    assert user.full_name == "Developer Account"
    
    # 3. Query seeded services
    svc_query = select(Service).where(Service.user_id == user.id)
    svc_result = await db_session.execute(svc_query)
    services = svc_result.scalars().all()
    
    assert len(services) == 3
    service_names = {s.name for s in services}
    assert "Website Design" in service_names
    assert "Graphics Design" in service_names
    assert "Bot/Automation Development" in service_names
    
    # 4. Verify seed data is idempotent (re-running does not duplicate)
    await seed_development_data(db_session)
    
    svc_result_re = await db_session.execute(svc_query)
    services_re = svc_result_re.scalars().all()
    assert len(services_re) == 3
