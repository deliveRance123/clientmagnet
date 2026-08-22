import logging
from typing import Dict, Any, List

logger = logging.getLogger("app.compliance")


class ComplianceError(Exception):
    """Exception raised when an action violates platform policies or safety rules."""
    pass


class ComplianceService:
    """
    Architectural Gatekeeper that reviews actions before they are executed.
    Ensures adherence to official API rules, rate limits, opt-out lists, and safety.
    """

    def __init__(self):
        # In-memory placeholders. These will be backed by PostgreSQL tables in later stages.
        self._opted_out_identifiers: Set[str] = {
            "spam-target@example.com",
            "+15550199",
            "@spammer_handle"
        }
        
        # Allowed official action typologies
        self._allowed_action_types = {
            "send_email",
            "send_whatsapp",
            "send_whatsapp_message",
            "post_social_content",
            "retrieve_official_leads"
        }

    async def check_action(self, user_id: str, action_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates whether a business action complies with safety, rate, and platform rules.
        
        Returns:
            Dict containing:
                "allowed": bool
                "reason": Optional[str]
                "code": Optional[str]
        """
        logger.info(f"Checking compliance for action '{action_type}' initiated by user '{user_id}'")

        # 1. Reject actions designed to violate rules or bypass controls
        if action_type not in self._allowed_action_types:
            logger.warning(f"Compliance violation: Unsanctioned action type '{action_type}' blocked.")
            return {
                "allowed": False,
                "reason": (
                    f"Action type '{action_type}' is not supported. The platform permits only official, "
                    "compliance-aligned integrations. Scraping, CAPTCHA bypass, and account-evasion are strictly blocked."
                ),
                "code": "UNSUPPORTED_ACTION"
            }

        # 2. Check Opt-Out status (e.g., recipient has unsubscribed)
        recipient = payload.get("recipient")
        if recipient and recipient in self._opted_out_identifiers:
            logger.warning(f"Compliance violation: Recipient '{recipient}' is on the opt-out registry.")
            return {
                "allowed": False,
                "reason": f"The recipient '{recipient}' has opted out of communication from this platform.",
                "code": "RECIPIENT_OPT_OUT"
            }

        # 3. Check for mass unsolicited messaging / spam limits
        if action_type in ("send_email", "send_whatsapp_message"):
            # Mock restriction: limit size of payload or check content for suspicious outreach
            content = payload.get("body", "")
            if len(content) < 5:
                return {
                    "allowed": False,
                    "reason": "Outreach body is too short or empty.",
                    "code": "INVALID_CONTENT"
                }

        # 4. Check for banned keywords (safety moderation)
        content = str(payload.get("body", "")).lower()
        banned_keywords = ["buy followers", "get rich quick", "win cash prize", "viagra", "cryptocurrency double"]
        for keyword in banned_keywords:
            if keyword in content:
                logger.warning(f"Compliance violation: Banned keyword '{keyword}' detected.")
                return {
                    "allowed": False,
                    "reason": f"Content contains blacklisted keyword/phrase: '{keyword}'",
                    "code": "PROHIBITED_CONTENT"
                }

        # 5. Success
        return {
            "allowed": True,
            "reason": None,
            "code": "COMPLIANT"
        }
        
    async def register_opt_out(self, identifier: str) -> None:
        """Add an identifier (email, phone, social handle) to the opt-out list."""
        self._opted_out_identifiers.add(identifier)
        logger.info(f"Registered new opt-out: {identifier}")
