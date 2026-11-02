"""
Security and Domain Constants
Gujarat Cyber Crime Social Media Intelligence & Early Warning System
"""

from enum import Enum


class DataClassification(str, Enum):
    """
    Government Data Classification Levels.
    Every record in the system carries an explicit classification level.
    """
    UNCLASSIFIED = "UNCLASSIFIED"
    RESTRICTED = "RESTRICTED"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"


class UserRole(str, Enum):
    """
    Role-Based Access Control (RBAC) Hierarchy for Gujarat Police Cyber Crime Cell.
    """
    SUPER_ADMIN = "SUPER_ADMIN"            # Full administrative and platform control
    NODAL_OFFICER = "NODAL_OFFICER"        # Senior police officer (SP/DYS/PI) with clearance for high-level intelligence
    LEAD_INVESTIGATOR = "LEAD_INVESTIGATOR"# Case lead managing alerts, cases, and intelligence dossiers
    CYBER_ANALYST = "CYBER_ANALYST"        # General analyst monitoring authorized feeds and flags
    AUDITOR = "AUDITOR"                    # Independent compliance and audit officer with read-only audit log access


class AuditAction(str, Enum):
    """Forensic action identifiers for immutable audit logging."""
    AUTH_LOGIN_SUCCESS = "AUTH_LOGIN_SUCCESS"
    AUTH_LOGIN_FAILURE = "AUTH_LOGIN_FAILURE"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    AUTH_TOKEN_REFRESH = "AUTH_TOKEN_REFRESH"

    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    USER_DELETE = "USER_DELETE"
    USER_ROLE_CHANGE = "USER_ROLE_CHANGE"

    DATA_QUERY = "DATA_QUERY"
    DATA_EXPORT = "DATA_EXPORT"
    DATA_CLASSIFICATION_CHANGE = "DATA_CLASSIFICATION_CHANGE"
    DATA_RETENTION_PURGE = "DATA_RETENTION_PURGE"
    EVIDENCE_SEAL = "EVIDENCE_SEAL"

    SYSTEM_CONFIG_CHANGE = "SYSTEM_CONFIG_CHANGE"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    HEALTH_CHECK = "HEALTH_CHECK"

    # Social Source Management Audit Actions
    SOURCE_CREATE = "SOURCE_CREATE"
    SOURCE_UPDATE = "SOURCE_UPDATE"
    SOURCE_DELETE = "SOURCE_DELETE"
    SOURCE_TOGGLE = "SOURCE_TOGGLE"
    SOURCE_TEST_CONNECTION = "SOURCE_TEST_CONNECTION"
    SOURCE_SYNC = "SOURCE_SYNC"

    # Monitored Keyword & Threat Intelligence Audit Actions
    KEYWORD_CREATE = "KEYWORD_CREATE"
    KEYWORD_UPDATE = "KEYWORD_UPDATE"
    KEYWORD_DELETE = "KEYWORD_DELETE"
    KEYWORD_TOGGLE = "KEYWORD_TOGGLE"
    KEYWORD_SCAN = "KEYWORD_SCAN"

    # Location & District Intelligence Audit Actions
    LOCATION_DETECTED = "LOCATION_DETECTED"
    LOCATION_NORMALIZED = "LOCATION_NORMALIZED"
    LOCATION_UPDATED = "LOCATION_UPDATED"
    LOCATION_VERIFIED = "LOCATION_VERIFIED"
    LOCATION_REJECTED = "LOCATION_REJECTED"
    LOCATION_MAPPING_CHANGED = "LOCATION_MAPPING_CHANGED"
    LOCATION_MASTER_CREATED = "LOCATION_MASTER_CREATED"
    LOCATION_MASTER_UPDATED = "LOCATION_MASTER_UPDATED"
    LOCATION_MASTER_DISABLED = "LOCATION_MASTER_DISABLED"
    LOCATION_EXPORT = "LOCATION_EXPORT"

    # Module 10 - Cybercrime Classification & Intelligence Audit Actions
    ANALYSIS_CREATED = "ANALYSIS_CREATED"
    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    ANALYSIS_REVIEWED = "ANALYSIS_REVIEWED"
    CLASSIFICATION_CHANGED = "CLASSIFICATION_CHANGED"
    FALSE_POSITIVE_MARKED = "FALSE_POSITIVE_MARKED"
    CATEGORY_CHANGED = "CATEGORY_CHANGED"
    ANALYST_OVERRIDE = "ANALYST_OVERRIDE"
    MODEL_VERSION_CHANGED = "MODEL_VERSION_CHANGED"
    RULE_CHANGED = "RULE_CHANGED"

    # Module 11 - IOC & Entity Extraction Audit Actions
    INDICATOR_EXTRACTED = "INDICATOR_EXTRACTED"
    INDICATOR_NORMALIZED = "INDICATOR_NORMALIZED"
    INDICATOR_MERGED = "INDICATOR_MERGED"
    INDICATOR_VERIFIED = "INDICATOR_VERIFIED"
    INDICATOR_REJECTED = "INDICATOR_REJECTED"
    INDICATOR_FALSE_POSITIVE = "INDICATOR_FALSE_POSITIVE"
    INDICATOR_VIEWED = "INDICATOR_VIEWED"
    INDICATOR_EXPORTED = "INDICATOR_EXPORTED"
    INDICATOR_NOTE_ADDED = "INDICATOR_NOTE_ADDED"
    INDICATOR_RELATION_CREATED = "INDICATOR_RELATION_CREATED"

    # Module 12 & 13 - Risk Scoring, Alerts & Notification Audit Actions
    RISK_CALCULATED = "RISK_CALCULATED"
    RISK_RECALCULATED = "RISK_RECALCULATED"
    ALERT_CREATED = "ALERT_CREATED"
    ALERT_GROUPED = "ALERT_GROUPED"
    ALERT_ACKNOWLEDGED = "ALERT_ACKNOWLEDGED"
    ALERT_ASSIGNED = "ALERT_ASSIGNED"
    ALERT_ESCALATED = "ALERT_ESCALATED"
    ALERT_RESOLVED = "ALERT_RESOLVED"
    ALERT_DISMISSED = "ALERT_DISMISSED"
    ALERT_FALSE_POSITIVE = "ALERT_FALSE_POSITIVE"
    RISK_OVERRIDE = "RISK_OVERRIDE"
    SEVERITY_OVERRIDE = "SEVERITY_OVERRIDE"
    NOTIFICATION_QUEUED = "NOTIFICATION_QUEUED"
    NOTIFICATION_SENT = "NOTIFICATION_SENT"
    NOTIFICATION_DELIVERED = "NOTIFICATION_DELIVERED"
    NOTIFICATION_FAILED = "NOTIFICATION_FAILED"
    NOTIFICATION_RETRIED = "NOTIFICATION_RETRIED"
    NOTIFICATION_SUPPRESSED = "NOTIFICATION_SUPPRESSED"
    NOTIFICATION_CANCELLED = "NOTIFICATION_CANCELLED"
    NOTIFICATION_POLICY_CHANGED = "NOTIFICATION_POLICY_CHANGED"
    RISK_CONFIG_CHANGED = "RISK_CONFIG_CHANGED"

    # Module 14 - Incident & Investigation Case Management Audit Actions
    CASE_CREATED = "CASE_CREATED"
    CASE_OPENED = "CASE_OPENED"
    CASE_ASSIGNED = "CASE_ASSIGNED"
    CASE_REASSIGNED = "CASE_REASSIGNED"
    CASE_UPDATED = "CASE_UPDATED"
    CASE_NOTE_ADDED = "CASE_NOTE_ADDED"
    CASE_NOTE_EDITED = "CASE_NOTE_EDITED"
    CASE_TASK_CREATED = "CASE_TASK_CREATED"
    CASE_TASK_UPDATED = "CASE_TASK_UPDATED"
    IOC_LINKED = "IOC_LINKED"
    IOC_UNLINKED = "IOC_UNLINKED"
    ALERT_LINKED = "ALERT_LINKED"
    OBSERVATION_LINKED = "OBSERVATION_LINKED"
    ENTITY_LINKED = "ENTITY_LINKED"
    EVIDENCE_ADDED = "EVIDENCE_ADDED"
    EVIDENCE_ACCESSED = "EVIDENCE_ACCESSED"
    EVIDENCE_EXPORTED = "EVIDENCE_EXPORTED"
    EVIDENCE_VERIFIED = "EVIDENCE_VERIFIED"
    CASE_ESCALATED = "CASE_ESCALATED"
    CASE_MERGED = "CASE_MERGED"
    CASE_SPLIT = "CASE_SPLIT"
    CASE_REVIEW_REQUESTED = "CASE_REVIEW_REQUESTED"
    CASE_APPROVED = "CASE_APPROVED"
    CASE_CLOSED = "CASE_CLOSED"
    CASE_REOPENED = "CASE_REOPENED"
    CASE_ARCHIVED = "CASE_ARCHIVED"
    CASE_REPORT_GENERATED = "CASE_REPORT_GENERATED"
    CASE_EXPORTED = "CASE_EXPORTED"


class CybercrimeClassification(str, Enum):
    """High-level determination of suspect content."""
    POTENTIAL_CYBERCRIME = "POTENTIAL_CYBERCRIME"
    NOT_CYBERCRIME_RELATED = "NOT_CYBERCRIME_RELATED"
    AWARENESS_OR_NEWS = "AWARENESS_OR_NEWS"
    UNKNOWN = "UNKNOWN"


class ContentContext(str, Enum):
    """Contextual intent/nature of the social media publication."""
    VICTIM_REPORT = "VICTIM_REPORT"
    NEWS_REPORT = "NEWS_REPORT"
    AWARENESS = "AWARENESS"
    ADVISORY = "ADVISORY"
    GENERAL_DISCUSSION = "GENERAL_DISCUSSION"
    PROMOTIONAL = "PROMOTIONAL"
    WARNING = "WARNING"
    LAW_ENFORCEMENT_UPDATE = "LAW_ENFORCEMENT_UPDATE"
    UNKNOWN = "UNKNOWN"


class AnalysisPipelineStatus(str, Enum):
    """Asynchronous worker pipeline lifecycle state."""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class AnalystReviewStatus(str, Enum):
    """Forensic verification state by authorized police officer."""
    UNREVIEWED = "UNREVIEWED"
    CONFIRMED_RELEVANT = "CONFIRMED_RELEVANT"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    ESCALATED = "ESCALATED"


class EvidenceType(str, Enum):
    """Nature of supporting forensic evidence."""
    KEYWORD_MATCH = "KEYWORD_MATCH"
    FINANCIAL_LOSS = "FINANCIAL_LOSS"
    CREDENTIAL_THEFT = "CREDENTIAL_THEFT"
    MALICIOUS_URL = "MALICIOUS_URL"
    ACCOUNT_TAKEOVER = "ACCOUNT_TAKEOVER"
    FIRST_PERSON_INCIDENT = "FIRST_PERSON_INCIDENT"
    SUSPECTED_IOC = "SUSPECTED_IOC"
    RULE_PATTERN = "RULE_PATTERN"
    CONTEXT_INDICATOR = "CONTEXT_INDICATOR"


class RuleType(str, Enum):
    """Classification rule evaluation mechanism."""
    BOOLEAN_EXPRESSION = "BOOLEAN_EXPRESSION"
    KEYWORD_COMBINATION = "KEYWORD_COMBINATION"
    REGEX = "REGEX"
    CONTEXT_CONDITIONAL = "CONTEXT_CONDITIONAL"


class LocationType(str, Enum):
    """Geographic administrative hierarchy entity types."""
    STATE = "STATE"
    DISTRICT = "DISTRICT"
    TALUKA = "TALUKA"
    CITY = "CITY"
    LOCALITY = "LOCALITY"


class LocationSemanticRole(str, Enum):
    """Semantic context of a geographic entity in cybercrime intelligence."""
    INCIDENT_LOCATION = "INCIDENT_LOCATION"
    SOURCE_LOCATION = "SOURCE_LOCATION"
    MENTIONED_LOCATION = "MENTIONED_LOCATION"
    ORGANIZATION_LOCATION = "ORGANIZATION_LOCATION"
    OTHER = "OTHER"


class LocationVerificationStatus(str, Enum):
    """Verification state of an extracted location lead."""
    UNKNOWN = "UNKNOWN"
    DETECTED = "DETECTED"
    PROBABLE = "PROBABLE"
    CONFIRMED = "CONFIRMED"
    AMBIGUOUS = "AMBIGUOUS"
    REJECTED = "REJECTED"


class LocationExtractionMethod(str, Enum):
    """Method utilized to identify and extract the geographic candidate."""
    DICTIONARY = "DICTIONARY"
    ALIAS = "ALIAS"
    FUZZY_MATCH = "FUZZY_MATCH"
    NER = "NER"
    CONTEXTUAL = "CONTEXTUAL"
    SOURCE_METADATA = "SOURCE_METADATA"
    MANUAL = "MANUAL"


class AlertSeverity(str, Enum):
    """Early warning threat alert levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class KeywordCategory(str, Enum):
    """Statutory Cybercrime Threat Taxonomies."""
    FINANCIAL_FRAUD = "Financial Fraud"
    PHISHING = "Phishing"
    ACCOUNT_COMPROMISE = "Account Compromise"
    IDENTITY_ABUSE = "Identity Abuse"
    EXTORTION = "Extortion"
    OTHER = "Other"


class KeywordMatchType(str, Enum):
    """Detection pattern matching modes."""
    PHRASE = "PHRASE"
    EXACT = "EXACT"
    REGEX = "REGEX"


class SourceType(str, Enum):
    """Supported authorized social media source types."""
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    OTHER_AUTHORIZED_SOURCE = "OTHER_AUTHORIZED_SOURCE"


class SourceStatus(str, Enum):
    """Operational status of a monitored social media source."""
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    ERROR = "ERROR"
    PENDING_AUTHORIZATION = "PENDING_AUTHORIZATION"


class SourceHealth(str, Enum):
    """API connection health for a monitored source."""
    OPERATIONAL = "OPERATIONAL"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    RATE_LIMITED = "RATE_LIMITED"


class IndicatorType(str, Enum):
    """Categorization of cyber indicators and forensic entities."""
    URL = "URL"
    DOMAIN = "DOMAIN"
    IPV4 = "IPV4"
    IPV6 = "IPV6"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    USERNAME = "USERNAME"
    PROFILE = "PROFILE"
    CRYPTO_ADDRESS = "CRYPTO_ADDRESS"
    HASH = "HASH"
    FILE = "FILE"
    APK = "APK"
    UPI = "UPI"
    OTHER = "OTHER"


class IndicatorStatus(str, Enum):
    """Investigative confidence and verification status of an indicator."""
    EXTRACTED = "EXTRACTED"
    POTENTIAL = "POTENTIAL"
    SUSPECTED = "SUSPECTED"
    VERIFIED = "VERIFIED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    REJECTED = "REJECTED"


class IndicatorContext(str, Enum):
    """Contextual role of the indicator in the source text."""
    BENIGN_REFERENCE = "BENIGN_REFERENCE"
    WARNING = "WARNING"
    VICTIM_REPORT = "VICTIM_REPORT"
    SUSPECTED_FRAUD = "SUSPECTED_FRAUD"
    NEWS_REPORT = "NEWS_REPORT"
    LAW_ENFORCEMENT_REFERENCE = "LAW_ENFORCEMENT_REFERENCE"
    ADVERTISEMENT = "ADVERTISEMENT"
    UNKNOWN = "UNKNOWN"


class IndicatorExtractionMethod(str, Enum):
    """Mechanism utilized to identify the indicator candidate."""
    REGEX = "REGEX"
    RULE_ENGINE = "RULE_ENGINE"
    NLP = "NLP"
    HEURISTIC = "HEURISTIC"
    OCR = "OCR"
    MANUAL = "MANUAL"


class IndicatorRelationshipType(str, Enum):
    """Semantic relationship binding cyber entities or incidents."""
    URL_DOMAIN = "URL_DOMAIN"
    CO_OCCURRENCE = "CO_OCCURRENCE"
    INCIDENT_INDICATOR = "INCIDENT_INDICATOR"
    COMMUNICATION_CHANNEL = "COMMUNICATION_CHANNEL"
    PAYMENT_DESTINATION = "PAYMENT_DESTINATION"
    MALWARE_DELIVERY = "MALWARE_DELIVERY"
    SIMILAR_TO = "SIMILAR_TO"


class AlertStatus(str, Enum):
    """Lifecycle progression states for SOC early-warning alerts."""
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ASSIGNED = "ASSIGNED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    DISMISSED = "DISMISSED"
    EXPIRED = "EXPIRED"


class NotificationChannel(str, Enum):
    """Supported alert dispatch mediums."""
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    WEBHOOK = "WEBHOOK"


class NotificationStatus(str, Enum):
    """Operational dispatch status for individual notification deliveries."""
    QUEUED = "QUEUED"
    SENDING = "SENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


class EscalationLevel(str, Enum):
    """Hierarchy of alert notification escalation."""
    LEVEL_1_ANALYST = "LEVEL_1_ANALYST"
    LEVEL_2_SUPERVISOR = "LEVEL_2_SUPERVISOR"
    LEVEL_3_SENIOR_OFFICER = "LEVEL_3_SENIOR_OFFICER"
    LEVEL_4_EMERGENCY = "LEVEL_4_EMERGENCY"


class FeedbackType(str, Enum):
    """Analyst precision evaluations on risk score and priority."""
    CORRECT = "CORRECT"
    OVER_PRIORITIZED = "OVER_PRIORITIZED"
    UNDER_PRIORITIZED = "UNDER_PRIORITIZED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    MISSED_SEVERITY = "MISSED_SEVERITY"


class RiskProfileCode(str, Enum):
    """Configurable threat domain weighting profiles."""
    GENERAL_MONITORING = "GENERAL_MONITORING"
    FINANCIAL_FRAUD = "FINANCIAL_FRAUD"
    PHISHING = "PHISHING"
    ACCOUNT_COMPROMISE = "ACCOUNT_COMPROMISE"
    MALWARE = "MALWARE"
    EMERGENCY_THREAT = "EMERGENCY_THREAT"


# ============================================================================
# Module 14: Cybercrime Incident & Investigation Case Management Enums
# ============================================================================

class CaseStatus(str, Enum):
    """Lifecycle statuses for investigation cases."""
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    PENDING_REVIEW = "PENDING_REVIEW"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    REFERRED = "REFERRED"
    MERGED = "MERGED"
    DUPLICATE = "DUPLICATE"


class CasePriority(str, Enum):
    """Operational priority levels for investigation cases."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CaseCategoryEnum(str, Enum):
    """Statutory cybercrime categorization taxonomy."""
    FINANCIAL_CYBER_FRAUD = "FINANCIAL_CYBER_FRAUD"
    PHISHING = "PHISHING"
    ACCOUNT_COMPROMISE = "ACCOUNT_COMPROMISE"
    IDENTITY_IMPERSONATION = "IDENTITY_IMPERSONATION"
    ONLINE_EXTORTION = "ONLINE_EXTORTION"
    CYBER_HARASSMENT = "CYBER_HARASSMENT"
    MALWARE = "MALWARE"
    DATA_BREACH = "DATA_BREACH"
    JOB_INTERNSHIP_SCAM = "JOB_INTERNSHIP_SCAM"
    E_COMMERCE_FRAUD = "E_COMMERCE_FRAUD"
    CRYPTOCURRENCY_FRAUD = "CRYPTOCURRENCY_FRAUD"
    SOCIAL_MEDIA_ABUSE = "SOCIAL_MEDIA_ABUSE"
    OTHER_CYBERCRIME = "OTHER_CYBERCRIME"
    UNKNOWN = "UNKNOWN"


class CaseConfidentiality(str, Enum):
    """Security classification & compartmentalization for case dossiers."""
    PUBLIC_INTERNAL = "PUBLIC_INTERNAL"
    RESTRICTED = "RESTRICTED"
    CONFIDENTIAL = "CONFIDENTIAL"
    HIGHLY_RESTRICTED = "HIGHLY_RESTRICTED"


class CaseNoteType(str, Enum):
    """Investigative note categorization."""
    GENERAL = "GENERAL"
    ANALYSIS = "ANALYSIS"
    LEAD = "LEAD"
    FOLLOW_UP = "FOLLOW_UP"
    SUPERVISORY = "SUPERVISORY"
    LEGAL_REVIEW = "LEGAL_REVIEW"
    TECHNICAL = "TECHNICAL"


class CaseTaskStatus(str, Enum):
    """Actionable task workflow statuses."""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CaseEntityType(str, Enum):
    """Types of entities tracked within an investigation."""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    SOCIAL_MEDIA_ACCOUNT = "SOCIAL_MEDIA_ACCOUNT"
    WEBSITE = "WEBSITE"
    DOMAIN = "DOMAIN"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    CRYPTO_ADDRESS = "CRYPTO_ADDRESS"
    LOCATION = "LOCATION"
    OTHER = "OTHER"


class CaseEntityRelationship(str, Enum):
    """
    Relationship of an entity to the case.
    Strict non-adjudicative framing: No automatic OFFENDER designation.
    """
    VICTIM = "VICTIM"
    REPORTER = "REPORTER"
    WITNESS = "WITNESS"
    ORGANIZATION = "ORGANIZATION"
    ACCOUNT = "ACCOUNT"
    WEBSITE = "WEBSITE"
    UNKNOWN = "UNKNOWN"


class CaseEvidenceType(str, Enum):
    """Forensic evidence classifications for case management."""
    SOCIAL_MEDIA_POST = "SOCIAL_MEDIA_POST"
    SCREENSHOT = "SCREENSHOT"
    URL = "URL"
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"
    DOCUMENT = "DOCUMENT"
    CHAT_EXPORT = "CHAT_EXPORT"
    LOG = "LOG"
    IOC = "IOC"
    ANALYST_NOTE = "ANALYST_NOTE"
    EXTERNAL_DOCUMENT = "EXTERNAL_DOCUMENT"
    OTHER = "OTHER"


class ChainOfCustodyAction(str, Enum):
    """Forensic chain-of-custody immutable events."""
    EVIDENCE_COLLECTED = "EVIDENCE_COLLECTED"
    EVIDENCE_UPLOADED = "EVIDENCE_UPLOADED"
    EVIDENCE_ACCESSED = "EVIDENCE_ACCESSED"
    EVIDENCE_TRANSFERRED = "EVIDENCE_TRANSFERRED"
    EVIDENCE_EXPORTED = "EVIDENCE_EXPORTED"
    EVIDENCE_REVIEWED = "EVIDENCE_REVIEWED"
    EVIDENCE_ARCHIVED = "EVIDENCE_ARCHIVED"


class CaseRelationType(str, Enum):
    """Relationships between distinct cases."""
    RELATED_CASE = "RELATED_CASE"
    DUPLICATE_CASE = "DUPLICATE_CASE"
    PARENT_CASE = "PARENT_CASE"
    CHILD_CASE = "CHILD_CASE"
    REFERRED_CASE = "REFERRED_CASE"


class CaseClosureReason(str, Enum):
    """Statutory justification categories for closing an investigation."""
    RESOLVED = "RESOLVED"
    NO_ACTION_REQUIRED = "NO_ACTION_REQUIRED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    DUPLICATE = "DUPLICATE"
    REFERRED = "REFERRED"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    OUTSIDE_JURISDICTION = "OUTSIDE_JURISDICTION"
    OTHER = "OTHER"




