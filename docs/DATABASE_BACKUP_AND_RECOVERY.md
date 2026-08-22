# PostgreSQL Database Backup, Migration & Disaster Recovery

This guide outlines disaster recovery, point-in-time recovery, Alembic migration maintenance, and failover procedures for **Client Magnet** in production.

---

## 1. Managed Backups on Render

Render Managed PostgreSQL includes automated daily backups with continuous WAL archiving on standard/pro tiers.

### Automated Backups
- Render automatically captures daily snapshot backups retained for 7 to 30 days depending on the plan.
- Manual point-in-time snapshots can be created directly from the Render Dashboard under **Database > Backups > Manual Backup**.

### Manual Command-Line Backup (`pg_dump`)
To download an offsite copy of the production database:
```bash
# Dump the production database to a compressed SQL archive
pg_dump "$DATABASE_URL" --format=custom --no-owner --no-privileges --file=client_magnet_backup_$(date +%Y%m%d_%H%M%S).dump
```

---

## 2. Restoring a Backup

### Restoring via Render Dashboard
1. Navigate to the Render PostgreSQL instance.
2. Select the **Backups** tab.
3. Click **Restore** next to the desired timestamp. Render will spin up a new database containing the restored state.
4. Update the `DATABASE_URL` environment variable on the web and worker services to point to the restored instance.

### Restoring via CLI (`pg_restore`)
```bash
# Drop existing connections and restore data into target database
pg_restore --clean --if-exists --no-owner --no-privileges -d "$DATABASE_URL" client_magnet_backup_20260822.dump
```

---

## 3. Database Migrations with Alembic

### Running Migrations in Production
During deployment on Render, the build script `backend/render_build.sh` automatically executes:
```bash
alembic upgrade head
```

### Safe Rollback Procedure
If a deployment fails or a schema change needs to be reverted:
```bash
# Rollback the last migration
alembic downgrade -1

# Rollback to a specific revision ID
alembic downgrade 007_unified_communication_and_whatsapp
```

---

## 4. Disaster Recovery & Outage Playbook

| Scenario | Immediate Action | Recovery Strategy |
| :--- | :--- | :--- |
| **Backend Web Service Down** | Render automatically restarts unhealthy containers via `/health` probe. | Check container logs in Render Dashboard. Check if DATABASE_URL or API keys are misconfigured. |
| **Database Connection Exhaustion** | Backend pool recycling (`pool_recycle=300, max_overflow=20`) clears idle connections. | Verify worker concurrency. Scale Render PostgreSQL instance tier if simultaneous connections exceed 100. |
| **Corrupted Data / Accidental Deletion** | Stop write traffic. | Restore the latest automated daily snapshot or WAL point-in-time backup. |
