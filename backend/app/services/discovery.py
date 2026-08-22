import csv
import io
import json
import logging
import re
import uuid
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery import LeadDiscoveryRun, LeadDiscoverySource
from app.models.lead import Lead
from app.models.lead_source import LeadSource
from app.models.user import User
from app.schemas.ai import LeadAnalysisRequest
from app.schemas.discovery import (
    CSVImportResult,
    CSVRowError,
    ManualLeadImportRequest,
    NormalizedOpportunity,
    RawOpportunity,
)
from app.services.ai import AIService

logger = logging.getLogger("app.discovery")


# ---------------------------------------------------------------------------
# Provider Abstraction & Implementations
# ---------------------------------------------------------------------------

class BaseSourceProvider(ABC):
    """Abstract base class for all lead discovery source providers."""

    source_type: str = "BASE"

    @abstractmethod
    async def fetch_opportunities(
        self, config: Dict[str, Any], **kwargs
    ) -> List[RawOpportunity]:
        """Fetches raw opportunities from the provider."""
        pass


class JobBoardFeedProvider(BaseSourceProvider):
    """Parses public structured JSON feeds from job boards (e.g. RemoteOK, public dev boards)."""

    source_type: str = "JOB_BOARD"

    async def fetch_opportunities(
        self, config: Dict[str, Any], **kwargs
    ) -> List[RawOpportunity]:
        feed_url = config.get("feed_url")
        if not feed_url:
            raise ValueError("JobBoardFeedProvider requires 'feed_url' in config.")

        headers = {
            "User-Agent": "ClientMagnetDiscovery/1.0 (Business Opportunity Scout; legitimate client matching)",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(feed_url, headers=headers)
                if resp.status_code == 429:
                    raise RuntimeError(f"Rate limit reached on feed: {feed_url}")
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch job board feed '{feed_url}': {e}")
            raise

        opportunities: List[RawOpportunity] = []

        # Some feeds return a list (like RemoteOK), others return {"jobs": [...]} or {"items": [...]}
        items = data if isinstance(data, list) else data.get("jobs", data.get("items", []))

        for item in items:
            if not isinstance(item, dict):
                continue

            # Skip metadata items (e.g. legal notices in RemoteOK)
            title = item.get("position") or item.get("title") or item.get("role")
            if not title:
                continue

            company = item.get("company") or item.get("company_name")
            description = item.get("description") or item.get("details") or title
            url = item.get("url") or item.get("apply_url") or item.get("link")
            location = item.get("location") or "Remote"
            ext_id = str(item.get("id") or item.get("slug") or url)

            opportunities.append(
                RawOpportunity(
                    external_id=ext_id,
                    title=title,
                    company=company,
                    description=description,
                    url=url,
                    location=location,
                    platform="JOB_BOARD",
                    source=config.get("name", "Public Job Board"),
                    raw_data=item,
                )
            )

        return opportunities


class RSSFeedProvider(BaseSourceProvider):
    """Parses standard RSS 2.0 and Atom XML public feeds."""

    source_type: str = "RSS"

    async def fetch_opportunities(
        self, config: Dict[str, Any], **kwargs
    ) -> List[RawOpportunity]:
        feed_url = config.get("feed_url")
        if not feed_url:
            raise ValueError("RSSFeedProvider requires 'feed_url' in config.")

        headers = {
            "User-Agent": "ClientMagnetDiscovery/1.0 (RSS Opportunity Reader)",
            "Accept": "application/rss+xml, application/xml, text/xml",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(feed_url, headers=headers)
                resp.raise_for_status()
                xml_text = resp.text
        except Exception as e:
            logger.error(f"Failed to fetch RSS feed '{feed_url}': {e}")
            raise

        opportunities: List[RawOpportunity] = []
        try:
            root = ET.fromstring(xml_text)
            # Find RSS items or Atom entries
            items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

            for item in items:
                title_elem = item.find("title") or item.find("{http://www.w3.org/2005/Atom}title")
                desc_elem = (
                    item.find("description")
                    or item.find("content")
                    or item.find("{http://www.w3.org/2005/Atom}content")
                    or item.find("{http://www.w3.org/2005/Atom}summary")
                )
                link_elem = item.find("link") or item.find("{http://www.w3.org/2005/Atom}link")
                guid_elem = item.find("guid") or item.find("{http://www.w3.org/2005/Atom}id")

                title = title_elem.text if title_elem is not None and title_elem.text else "Opportunity Post"
                description = desc_elem.text if desc_elem is not None and desc_elem.text else title
                link = ""
                if link_elem is not None:
                    link = link_elem.get("href") or link_elem.text or ""
                guid = guid_elem.text if guid_elem is not None and guid_elem.text else link

                opportunities.append(
                    RawOpportunity(
                        external_id=guid,
                        title=title,
                        description=description,
                        url=link,
                        platform="RSS",
                        source=config.get("name", "RSS Feed"),
                    )
                )
        except Exception as e:
            logger.error(f"Error parsing XML feed from '{feed_url}': {e}")
            raise

        return opportunities


class MockDiscoveryProvider(BaseSourceProvider):
    """Mock discovery provider producing realistic opportunities for development and testing."""

    source_type: str = "MOCK"

    async def fetch_opportunities(
        self, config: Dict[str, Any], **kwargs
    ) -> List[RawOpportunity]:
        return [
            RawOpportunity(
                external_id="mock-opp-001",
                title="Looking for a modern Next.js website redesign for our fintech startup",
                company="Nexus Finance Inc",
                description="We need an experienced web designer/developer to overhaul our marketing pages, pricing calculator, and client portal.",
                url="https://jobs.example.com/nexus-web-redesign",
                location="Remote (Global)",
                platform="JOB_BOARD",
                source="Tech Opportunities Feed",
                email="contact@nexusfinance.io",
                website="https://nexusfinance.io",
            ),
            RawOpportunity(
                external_id="mock-opp-002",
                title="Need custom automated WhatsApp & Telegram customer support bot",
                company="Swift Logistics Corp",
                description="Our dispatch operations need an automated WhatsApp and Telegram bot for driver notifications, package tracking, and support FAQ.",
                url="https://jobs.example.com/swift-bot-automation",
                location="North America / Remote",
                platform="JOB_BOARD",
                source="Freelance Contract Board",
                website="https://swiftlogistics.com",
            ),
            RawOpportunity(
                external_id="mock-opp-003",
                title="Full brand identity and UI/UX graphics package for mobile fitness app",
                company="AuraFit Studios",
                description="Seeking a talented graphics and UI designer for complete mobile app design, vector icon set, and marketing social templates.",
                url="https://jobs.example.com/aurafit-graphics",
                location="Remote",
                platform="JOB_BOARD",
                source="Creative Freelancers Network",
                email="design@aurafit.com",
            ),
        ]


# ---------------------------------------------------------------------------
# Lead Normalizer
# ---------------------------------------------------------------------------

class LeadNormalizer:
    """Standardizes disparate raw opportunity structures into NormalizedOpportunity."""

    @staticmethod
    def strip_html(text: str) -> str:
        if not text:
            return ""
        # Remove HTML tags
        clean = re.sub(r"<[^>]+>", " ", text)
        # Collapse whitespace
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    @classmethod
    def normalize(cls, raw: RawOpportunity) -> NormalizedOpportunity:
        clean_desc = cls.strip_html(raw.description)
        name = raw.title.strip()

        # If title contains company (e.g. "Acme Corp: Web Developer"), extract
        company = raw.company
        if not company and ":" in name:
            parts = name.split(":", 1)
            company = parts[0].strip()

        # Ensure description is not empty
        if not clean_desc or len(clean_desc) < 10:
            clean_desc = name

        return NormalizedOpportunity(
            name=name[:255],
            company=company[:255] if company else None,
            email=raw.email,
            phone=None,
            website=raw.website,
            platform=raw.platform or "WEB",
            profile_url=None,
            location=raw.location,
            description=clean_desc,
            source=raw.source or "DISCOVERY_ENGINE",
            source_url=raw.url,
            external_id=raw.external_id,
        )


# ---------------------------------------------------------------------------
# Multi-Signal Deduplication Service
# ---------------------------------------------------------------------------

class DeduplicationService:
    """
    Checks multiple unique criteria in PostgreSQL to ensure no duplicate leads are created.
    Signals checked:
    1. Matching source_url
    2. Matching email (for the same user)
    3. Matching website (for the same user)
    4. Matching name + company (for the same user)
    5. Matching external_id on lead_sources
    """

    @staticmethod
    async def is_duplicate(
        db: AsyncSession, user_id: str, opportunity: NormalizedOpportunity
    ) -> Tuple[bool, Optional[str]]:
        # 1. Match Source URL
        if opportunity.source_url:
            query = select(Lead).where(
                Lead.user_id == user_id,
                Lead.source_url == opportunity.source_url,
            )
            existing = (await db.execute(query)).scalar_one_or_none()
            if existing:
                return True, f"Duplicate source URL: {opportunity.source_url}"

        # 2. Match Email
        if opportunity.email:
            query = select(Lead).where(
                Lead.user_id == user_id,
                Lead.email == opportunity.email,
            )
            existing = (await db.execute(query)).scalar_one_or_none()
            if existing:
                return True, f"Duplicate email address: {opportunity.email}"

        # 3. Match Website
        if opportunity.website:
            clean_web = opportunity.website.rstrip("/").lower()
            query = select(Lead).where(
                Lead.user_id == user_id,
                Lead.website == clean_web,
            )
            existing = (await db.execute(query)).scalar_one_or_none()
            if existing:
                return True, f"Duplicate website URL: {opportunity.website}"

        # 4. Match Name + Company
        if opportunity.name and opportunity.company:
            query = select(Lead).where(
                Lead.user_id == user_id,
                Lead.name == opportunity.name,
                Lead.company == opportunity.company,
            )
            existing = (await db.execute(query)).scalar_one_or_none()
            if existing:
                return True, f"Duplicate prospect name & company: {opportunity.name} ({opportunity.company})"

        # 5. Match Source URL on lead_sources
        if opportunity.source_url:
            query = select(LeadSource).where(
                LeadSource.user_id == user_id,
                LeadSource.source_url == opportunity.source_url,
            )
            existing_src = (await db.execute(query)).scalar_one_or_none()
            if existing_src:
                return True, f"Duplicate source URL in lead sources: {opportunity.source_url}"

        return False, None


# ---------------------------------------------------------------------------
# Discovery Engine Orchestrator
# ---------------------------------------------------------------------------

class DiscoveryEngine:
    """
    Orchestrates opportunity discovery across configured sources,
    runs normalization, deduplication, Gemini AI analysis, and PostgreSQL persistence.
    """

    def __init__(self, ai_service: Optional[AIService] = None):
        self.ai_service = ai_service

    def get_provider(self, source_type: str) -> BaseSourceProvider:
        """Resolves source provider implementation."""
        type_upper = source_type.upper()
        if type_upper == "JOB_BOARD":
            return JobBoardFeedProvider()
        elif type_upper == "RSS":
            return RSSFeedProvider()
        elif type_upper == "MOCK":
            return MockDiscoveryProvider()
        else:
            return MockDiscoveryProvider()

    async def run_source(
        self,
        db: AsyncSession,
        user: User,
        source: LeadDiscoverySource,
        analyze_with_ai: bool = True,
    ) -> LeadDiscoveryRun:
        """Executes a single discovery source for the user."""
        started_at = datetime.now(timezone.utc)
        provider = self.get_provider(source.source_type)

        config: Dict[str, Any] = {
            "name": source.name,
            "feed_url": source.feed_url,
        }
        if source.config_json:
            try:
                config.update(json.loads(source.config_json))
            except Exception:
                pass

        total_discovered = 0
        accepted_count = 0
        duplicate_count = 0
        rejected_count = 0
        error_msg = None

        try:
            raw_opps = await provider.fetch_opportunities(config)
            total_discovered = len(raw_opps)

            for raw in raw_opps:
                try:
                    # 1. Normalize
                    norm = LeadNormalizer.normalize(raw)

                    # 2. Check Deduplication
                    is_dup, dup_reason = await DeduplicationService.is_duplicate(
                        db, user.id, norm
                    )
                    if is_dup:
                        duplicate_count += 1
                        logger.info(f"Skipping duplicate opportunity '{norm.name}': {dup_reason}")
                        continue

                    # 3. AI Analysis & Service Matching (using Gemini / AIService)
                    detected_need = None
                    intent_score = 50.0
                    matched_service_id = None

                    if analyze_with_ai and self.ai_service:
                        try:
                            ai_analysis = await self.ai_service.analyze_lead(
                                db=db,
                                user=user,
                                request=LeadAnalysisRequest(
                                    lead_name=norm.name,
                                    lead_company=norm.company,
                                    lead_description=norm.description,
                                    source=norm.source,
                                ),
                            )
                            detected_need = ai_analysis.detected_need
                            intent_score = ai_analysis.intent_score
                            matched_service_id = ai_analysis.matched_service_id
                        except Exception as ai_e:
                            logger.warning(f"AI enrichment failed for lead '{norm.name}': {ai_e}")

                    # 4. Create and persist Lead in PostgreSQL
                    lead = Lead(
                        id=str(uuid.uuid4()),
                        user_id=user.id,
                        name=norm.name,
                        company=norm.company,
                        email=norm.email,
                        phone=norm.phone,
                        website=norm.website,
                        platform=norm.platform,
                        profile_url=norm.profile_url,
                        location=norm.location,
                        description=norm.description,
                        detected_need=detected_need,
                        source=norm.source,
                        source_url=norm.source_url,
                        matched_service_id=matched_service_id,
                        intent_score=intent_score,
                        status="NEW",
                    )
                    db.add(lead)
                    await db.flush()

                    # 5. Create LeadSource record
                    lead_source = LeadSource(
                        id=str(uuid.uuid4()),
                        user_id=user.id,
                        lead_id=lead.id,
                        source_type=norm.source or "DISCOVERY_ENGINE",
                        source_url=norm.source_url,
                        source_platform=norm.platform,
                    )
                    db.add(lead_source)

                    accepted_count += 1
                except Exception as opp_e:
                    logger.error(f"Error processing opportunity '{raw.title}': {opp_e}")
                    rejected_count += 1

            source.last_run_at = started_at
            status = "SUCCESS" if rejected_count == 0 else "PARTIAL"

        except Exception as e:
            logger.error(f"Discovery run failed for source '{source.name}': {e}")
            error_msg = str(e)
            status = "FAILED"

        finished_at = datetime.now(timezone.utc)

        # Record Discovery Run
        run = LeadDiscoveryRun(
            id=str(uuid.uuid4()),
            user_id=user.id,
            source_id=source.id,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            total_discovered=total_discovered,
            accepted_count=accepted_count,
            duplicate_count=duplicate_count,
            rejected_count=rejected_count,
            error_message=error_msg,
            metadata_json=json.dumps({
                "source_name": source.name,
                "source_type": source.source_type,
            }),
        )
        db.add(run)
        await db.commit()
        return run

    async def run_all_active_sources(
        self, db: AsyncSession, user: User, analyze_with_ai: bool = True
    ) -> List[LeadDiscoveryRun]:
        """Runs discovery for all active sources of the user."""
        query = select(LeadDiscoverySource).where(
            LeadDiscoverySource.user_id == user.id,
            LeadDiscoverySource.is_active == True,
        )
        sources = (await db.execute(query)).scalars().all()

        runs: List[LeadDiscoveryRun] = []
        for source in sources:
            run = await self.run_source(
                db=db, user=user, source=source, analyze_with_ai=analyze_with_ai
            )
            runs.append(run)
        return runs

    async def import_manual_lead(
        self, db: AsyncSession, user: User, request: ManualLeadImportRequest
    ) -> Lead:
        """Manually creates a lead with optional AI enrichment and duplicate check."""
        norm = NormalizedOpportunity(
            name=request.name.strip(),
            company=request.company.strip() if request.company else None,
            email=request.email.strip() if request.email else None,
            phone=request.phone.strip() if request.phone else None,
            website=request.website.strip() if request.website else None,
            platform=request.platform or "MANUAL",
            location=request.location,
            description=request.description.strip(),
            source=request.source or "MANUAL",
            source_url=request.source_url,
        )

        is_dup, dup_reason = await DeduplicationService.is_duplicate(db, user.id, norm)
        if is_dup:
            raise ValueError(f"Duplicate lead detected: {dup_reason}")

        detected_need = None
        intent_score = 50.0
        matched_service_id = None

        if request.analyze_with_ai and self.ai_service:
            try:
                ai_analysis = await self.ai_service.analyze_lead(
                    db=db,
                    user=user,
                    request=LeadAnalysisRequest(
                        lead_name=norm.name,
                        lead_company=norm.company,
                        lead_description=norm.description,
                        source=norm.source,
                    ),
                )
                detected_need = ai_analysis.detected_need
                intent_score = ai_analysis.intent_score
                matched_service_id = ai_analysis.matched_service_id
            except Exception as e:
                logger.warning(f"AI enrichment failed for manual lead: {e}")

        lead = Lead(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name=norm.name,
            company=norm.company,
            email=norm.email,
            phone=norm.phone,
            website=norm.website,
            platform=norm.platform,
            location=norm.location,
            description=norm.description,
            detected_need=detected_need,
            source=norm.source,
            source_url=norm.source_url,
            matched_service_id=matched_service_id,
            intent_score=intent_score,
            status="NEW",
        )
        db.add(lead)
        await db.flush()

        lead_source = LeadSource(
            id=str(uuid.uuid4()),
            user_id=user.id,
            lead_id=lead.id,
            source_type=norm.source or "MANUAL",
            source_url=norm.source_url,
            source_platform=norm.platform,
        )
        db.add(lead_source)
        await db.commit()
        await db.refresh(lead)
        return lead

    async def import_csv_leads(
        self,
        db: AsyncSession,
        user: User,
        csv_content: str,
        analyze_with_ai: bool = False,
    ) -> CSVImportResult:
        """Parses and validates a CSV file, importing valid non-duplicate rows."""
        f = io.StringIO(csv_content.strip())
        reader = csv.DictReader(f)

        total_rows = 0
        imported_count = 0
        duplicate_count = 0
        rejected_count = 0
        errors: List[CSVRowError] = []

        if not reader.fieldnames:
            return CSVImportResult(
                total_rows=0,
                imported_count=0,
                duplicate_count=0,
                rejected_count=0,
                errors=[CSVRowError(row_number=0, error="CSV file is empty or missing headers")],
            )

        # Normalize field names to lowercase
        field_map = {fn.lower().strip(): fn for fn in reader.fieldnames if fn}

        for row_idx, row in enumerate(reader, start=1):
            total_rows += 1
            try:
                name_key = field_map.get("name") or field_map.get("prospect") or field_map.get("title")
                desc_key = field_map.get("description") or field_map.get("notes") or field_map.get("need")
                email_key = field_map.get("email")
                company_key = field_map.get("company")
                phone_key = field_map.get("phone")
                website_key = field_map.get("website")
                source_key = field_map.get("source")
                url_key = field_map.get("url") or field_map.get("source_url")

                name = row.get(name_key, "").strip() if name_key else ""
                desc = row.get(desc_key, "").strip() if desc_key else ""

                if not name:
                    rejected_count += 1
                    errors.append(CSVRowError(row_number=row_idx, error="Missing required 'name' field", row_data=row))
                    continue

                if not desc:
                    desc = f"Imported lead for {name}"

                email = row.get(email_key, "").strip() if email_key else None
                if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    rejected_count += 1
                    errors.append(CSVRowError(row_number=row_idx, error=f"Invalid email format: '{email}'", row_data=row))
                    continue

                norm = NormalizedOpportunity(
                    name=name,
                    company=row.get(company_key, "").strip() if company_key else None,
                    email=email,
                    phone=row.get(phone_key, "").strip() if phone_key else None,
                    website=row.get(website_key, "").strip() if website_key else None,
                    platform="CSV_IMPORT",
                    description=desc,
                    source=row.get(source_key, "CSV_IMPORT").strip() if source_key else "CSV_IMPORT",
                    source_url=row.get(url_key, "").strip() if url_key else None,
                )

                # Check duplicate
                is_dup, dup_reason = await DeduplicationService.is_duplicate(db, user.id, norm)
                if is_dup:
                    duplicate_count += 1
                    continue

                lead = Lead(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    name=norm.name,
                    company=norm.company,
                    email=norm.email,
                    phone=norm.phone,
                    website=norm.website,
                    platform=norm.platform,
                    description=norm.description,
                    source=norm.source,
                    source_url=norm.source_url,
                    intent_score=50.0,
                    status="NEW",
                )
                db.add(lead)
                await db.flush()

                lead_src = LeadSource(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    lead_id=lead.id,
                    source_type=norm.source or "CSV_IMPORT",
                    source_url=norm.source_url,
                    source_platform=norm.platform,
                )
                db.add(lead_src)
                imported_count += 1

            except Exception as row_e:
                rejected_count += 1
                errors.append(CSVRowError(row_number=row_idx, error=str(row_e), row_data=row))

        await db.commit()

        return CSVImportResult(
            total_rows=total_rows,
            imported_count=imported_count,
            duplicate_count=duplicate_count,
            rejected_count=rejected_count,
            errors=errors,
        )
