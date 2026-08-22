import asyncio
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.models.user import User
from app.models.service import Service
from app.core.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.db.seed")


async def seed_development_data(db_session: Optional[AsyncSession] = None):
    logger.info("==================================================")
    logger.info("   WARNING: RUNNING DEVELOPMENT ONLY SEEDING...   ")
    logger.info("==================================================")

    if db_session is not None:
        await _seed_with_db(db_session)
    else:
        async with SessionLocal() as db:
            await _seed_with_db(db)


async def _seed_with_db(db: AsyncSession):
    # 1. Create development user if not exists
    dev_email = "dev@clientmagnet.local"
    query = select(User).where(User.email == dev_email)
    result = await db.execute(query)
    dev_user = result.scalar_one_or_none()

    if not dev_user:
        logger.info(f"Creating test user: {dev_email}")
        dev_user = User(
            email=dev_email,
            hashed_password=hash_password("Password123!"),
            full_name="Developer Account",
            company_name="Client Magnet Dev Inc.",
            is_active=True,
            is_verified=True,
        )
        db.add(dev_user)
        await db.commit()
        await db.refresh(dev_user)
        logger.info(f"Test user created with ID: {dev_user.id}")
    else:
        logger.info(f"Test user already exists with ID: {dev_user.id}")

    # 2. Create the three initial services
    initial_services = [
        {
            "name": "Website Design",
            "description": "High-converting web design, custom landing pages, and responsive web apps.",
            "pricing": "Starting at $1,500",
            "target_clients": "E-commerce stores, SaaS startups, and local service businesses needing modern online presence.",
            "portfolio_links": "https://example.com/portfolio/web1, https://example.com/portfolio/web2",
        },
        {
            "name": "Graphics Design",
            "description": "Brand identity, logos, vector illustration, and high-CTR marketing creatives.",
            "pricing": "Starting at $500",
            "target_clients": "Agencies, creators, brands, and marketing teams.",
            "portfolio_links": "https://example.com/portfolio/branding",
        },
        {
            "name": "Bot/Automation Development",
            "description": "Custom workflow automations, intelligent chatbots, and CRM sync pipelines.",
            "pricing": "Starting at $2,000",
            "target_clients": "Agencies, e-commerce brands, and sales teams seeking to automate repetitive tasks.",
            "portfolio_links": "https://example.com/portfolio/bot-demo",
        },
    ]

    for svc_data in initial_services:
        svc_query = select(Service).where(
            Service.user_id == dev_user.id, Service.name == svc_data["name"]
        )
        svc_result = await db.execute(svc_query)
        existing_svc = svc_result.scalar_one_or_none()

        if not existing_svc:
            logger.info(f"Seeding service: {svc_data['name']}")
            new_svc = Service(
                user_id=dev_user.id,
                name=svc_data["name"],
                description=svc_data["description"],
                pricing=svc_data["pricing"],
                target_clients=svc_data["target_clients"],
                portfolio_links=svc_data["portfolio_links"],
                is_active=True,
            )
            db.add(new_svc)
        else:
            logger.info(f"Service '{svc_data['name']}' already exists.")

    await db.commit()
    logger.info("==================================================")
    logger.info("      DEVELOPMENT SEEDING COMPLETED SUCCESSFULLY   ")
    logger.info("==================================================")


if __name__ == "__main__":
    # Run the async seeder
    asyncio.run(seed_development_data())
