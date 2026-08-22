import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.db.base_class import Base
from app.models import (
    User, Service, Lead, Client, SocialAccount, EmailAccount,
    Conversation, Message, FollowUp, Content, ScheduledPost, OptOut, AuditLog, ActivityLog
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.bootstrap")

async def bootstrap():
    engine = create_async_engine(settings.DATABASE_URL)
    
    logger.info("1. Creating all database tables in PostgreSQL...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tables created successfully.")

    Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        demo_emails = ["demo@clientmagnet.io", "dev@clientmagnet.local"]
        for email in demo_emails:
            q = select(User).where(User.email == email)
            res = await session.execute(q)
            existing = res.scalar_one_or_none()
            if not existing:
                user = User(
                    email=email,
                    hashed_password=hash_password("Password123!"),
                    full_name="Demo Founder",
                    company_name="Magnet Agency Global",
                    is_active=True,
                    is_verified=True,
                )
                session.add(user)
                await session.flush()
                logger.info(f"Created user: {email} with Password123!")

                services_data = [
                    {
                        "name": "Website Design & Development",
                        "description": "Modern Next.js, React, Tailwind CSS platforms, dashboards, and e-commerce web applications.",
                        "pricing": "$3,000 - $8,000",
                        "target_clients": "Startups, scaleups, and direct-to-consumer brands",
                    },
                    {
                        "name": "Graphics & Brand Identity",
                        "description": "Complete visual identity design, Figma UI/UX kits, 3D product renders, and marketing assets.",
                        "pricing": "$1,500 - $4,000",
                        "target_clients": "Funded startups, digital creators, and retail brands",
                    },
                    {
                        "name": "Bot & Automation Development",
                        "description": "Custom conversational bots, WhatsApp Business API integrations, lead routing, and workflow automations.",
                        "pricing": "$2,500 - $6,000",
                        "target_clients": "E-commerce stores, real estate agencies, and SaaS platforms",
                    },
                ]
                for s in services_data:
                    svc = Service(
                        user_id=user.id,
                        name=s["name"],
                        description=s["description"],
                        pricing=s["pricing"],
                        target_clients=s["target_clients"],
                        is_active=True,
                    )
                    session.add(svc)
                logger.info(f"Seeded 3 core services for {email}")
            else:
                logger.info(f"User {email} already exists.")

        await session.commit()
    logger.info("Database bootstrap and seeding completed!")

if __name__ == "__main__":
    asyncio.run(bootstrap())
