import pytest
from alembic.config import Config
from alembic import command
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.lead import Lead
from app.models.service import Service
from app.models.client import Client
from app.models.social_account import SocialAccount
from app.models.opt_out import OptOut


def test_alembic_migrations_run_cleanly():
    """Verify Alembic configurations compile and migration files can be parsed."""
    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    alembic_cfg = Config(str(ini_path))
    # Override script_location to be absolute so it works regardless of cwd
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    # Test that we can read migration directory structure cleanly without exceptions
    try:
        command.history(alembic_cfg, verbose=False)
    except Exception as e:
        pytest.fail(f"Alembic migration parsing failed: {e}")


@pytest.mark.asyncio
async def test_cascading_deletes(db_session: AsyncSession):
    # 1. Create a User
    user = User(
        email="test_cascade@example.com",
        hashed_password="hashedpassword123",
        full_name="Cascade Tester",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 2. Add User-owned records
    lead = Lead(user_id=user.id, name="Test Lead")
    service = Service(user_id=user.id, name="Website Design", pricing="$1000")
    social = SocialAccount(user_id=user.id, platform="Twitter", account_identifier="test_user")
    opt_out = OptOut(user_id=user.id, contact_identifier="spam@spam.com", platform="email")
    
    db_session.add_all([lead, service, social, opt_out])
    await db_session.commit()
    
    # 3. Create a Client (linked to lead)
    client = Client(user_id=user.id, lead_id=lead.id, name="Test Client")
    db_session.add(client)
    await db_session.commit()

    # Verify they exist
    assert (await db_session.execute(select(Lead).where(Lead.user_id == user.id))).scalars().first() is not None
    assert (await db_session.execute(select(Service).where(Service.user_id == user.id))).scalars().first() is not None
    
    # 4. Delete User and verify cascade deletion of all dependencies
    await db_session.delete(user)
    await db_session.commit()
    
    # Confirm cascading deleted all user-owned records
    assert (await db_session.execute(select(Lead).where(Lead.user_id == user.id))).scalars().first() is None
    assert (await db_session.execute(select(Service).where(Service.user_id == user.id))).scalars().first() is None
    assert (await db_session.execute(select(SocialAccount).where(SocialAccount.user_id == user.id))).scalars().first() is None
    assert (await db_session.execute(select(OptOut).where(OptOut.user_id == user.id))).scalars().first() is None
    assert (await db_session.execute(select(Client).where(Client.user_id == user.id))).scalars().first() is None


@pytest.mark.asyncio
async def test_opt_out_unique_constraint(db_session: AsyncSession):
    user = User(email="opt_out_test@example.com", hashed_password="hashedpassword123")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    opt1 = OptOut(user_id=user.id, contact_identifier="target@example.com", platform="email", reason="unsubscribed")
    db_session.add(opt1)
    await db_session.commit()
    
    # Adding duplicate opt-out for the same user, contact, and platform should fail unique constraint
    opt2 = OptOut(user_id=user.id, contact_identifier="target@example.com", platform="email", reason="another reason")
    db_session.add(opt2)
    
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
