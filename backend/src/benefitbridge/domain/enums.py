"""Wire values from API.md; distinct concepts deliberately have distinct enums."""

from enum import StrEnum


class FactAttribute(StrEnum):
    LOCATION_COUNTRY = "location.country"
    CITIZENSHIP_COUNTRIES = "citizenship.countries"
    WORK_AUTHORIZATION_COUNTRIES = "work_authorization.countries"
    EDUCATION_ENROLLED = "education.enrolled"
    EDUCATION_LEVEL = "education.level"
    EDUCATION_FIELD = "education.field"
    EDUCATION_INSTITUTION = "education.institution"
    EDUCATION_GRADUATION = "education.graduation"
    DATE_OF_BIRTH = "date_of_birth"
    EDUCATION_GPA = "education.gpa"
    SKILLS = "skills"
    EXPERIENCE = "experience"
    LANGUAGE_TESTS = "language_tests"


class FactType(StrEnum):
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    COUNTRY_SET = "COUNTRY_SET"
    STRING_SET = "STRING_SET"
    GPA = "GPA"
    DATE = "DATE"
    EXPERIENCE = "EXPERIENCE"
    LANGUAGE_TESTS = "LANGUAGE_TESTS"
    UNKNOWN = "UNKNOWN"


class UnknownReason(StrEnum):
    USER_UNSURE = "USER_UNSURE"
    NOT_PROVIDED = "NOT_PROVIDED"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"


class DatePrecision(StrEnum):
    DAY = "DAY"
    MONTH = "MONTH"
    YEAR = "YEAR"


class Provenance(StrEnum):
    USER_CONFIRMED = "USER_CONFIRMED"
    USER_CONFIRMED_DOCUMENT = "USER_CONFIRMED_DOCUMENT"
    CONFLICTING = "CONFLICTING"


class AccountStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DELETING = "DELETING"


class DocumentKind(StrEnum):
    CV = "CV"
    TRANSCRIPT = "TRANSCRIPT"
    ENROLLMENT = "ENROLLMENT"


class DocumentStatus(StrEnum):
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    QUEUED = "QUEUED"
    PARSING = "PARSING"
    READY = "READY"
    FAILED = "FAILED"
    DELETING = "DELETING"


class DocumentQuality(StrEnum):
    READABLE = "READABLE"
    MANUAL_ENTRY_REQUIRED = "MANUAL_ENTRY_REQUIRED"


class CandidateState(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    CORRECTED = "CORRECTED"
    REJECTED = "REJECTED"


class RunKind(StrEnum):
    DOCUMENT_PARSE = "DOCUMENT_PARSE"
    DISCOVERY = "DISCOVERY"
    IMPORT = "IMPORT"
    EVALUATE = "EVALUATE"
    DRAFT_GENERATE = "DRAFT_GENERATE"
    DRAFT_VALIDATE = "DRAFT_VALIDATE"
    REFRESH = "REFRESH"
    DOCUMENT_DELETE = "DOCUMENT_DELETE"
    ACCOUNT_DELETE = "ACCOUNT_DELETE"
    DEMO_RESET = "DEMO_RESET"


class RunStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_USER = "WAITING_USER"
    SUCCEEDED = "SUCCEEDED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DeadlinePrecision(StrEnum):
    INSTANT = "INSTANT"
    DATE = "DATE"
    MONTH = "MONTH"
    YEAR = "YEAR"
    UNKNOWN = "UNKNOWN"


class Lane(StrEnum):
    INTERNSHIP_RESEARCH = "INTERNSHIP_RESEARCH"
    SCHOLARSHIP_PROGRAM = "SCHOLARSHIP_PROGRAM"


class Authority(StrEnum):
    OFFICIAL = "OFFICIAL"
    CORROBORATED = "CORROBORATED"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    UNRESOLVED = "UNRESOLVED"


class Availability(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    NOT_YET_OPEN = "NOT_YET_OPEN"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"


class FreshnessState(StrEnum):
    FRESH = "FRESH"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class EvaluationState(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    NOT_EVALUATED = "NOT_EVALUATED"


class Completeness(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    CONFLICTED = "CONFLICTED"


class Modality(StrEnum):
    MANDATORY = "MANDATORY"
    PREFERRED = "PREFERRED"
    OPTIONAL = "OPTIONAL"
    AMBIGUOUS = "AMBIGUOUS"


class RuleType(StrEnum):
    ALL = "ALL"
    ANY = "ANY"
    NOT = "NOT"
    PREDICATE = "PREDICATE"


class Operator(StrEnum):
    EQ = "EQ"
    NE = "NE"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
    IN = "IN"
    NOT_IN = "NOT_IN"
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    OVERLAPS = "OVERLAPS"
    EXISTS = "EXISTS"
    SEMANTIC_MATCH = "SEMANTIC_MATCH"


class ReferenceTime(StrEnum):
    APPLICATION = "APPLICATION"
    PROGRAM_START = "PROGRAM_START"
    EXPLICIT = "EXPLICIT"


class Interpretation(StrEnum):
    DIRECT = "DIRECT"
    SEMANTIC_REVIEWED = "SEMANTIC_REVIEWED"
    UNRESOLVED = "UNRESOLVED"


class EvidenceExpectation(StrEnum):
    KNOWN_FACT = "KNOWN_FACT"
    REQUIRED_CREDENTIAL = "REQUIRED_CREDENTIAL"


class Eligibility(StrEnum):
    MET = "MET"
    NOT_MET = "NOT_MET"
    UNKNOWN = "UNKNOWN"


class Truth(StrEnum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


class EvaluationMethod(StrEnum):
    DETERMINISTIC = "DETERMINISTIC"
    SEMANTIC = "SEMANTIC"


class Currentness(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    HISTORICAL = "HISTORICAL"


class ReasonCode(StrEnum):
    MISSING_PROFILE_FACT = "MISSING_PROFILE_FACT"
    MISSING_SOURCE = "MISSING_SOURCE"
    SOURCE_CONFLICT = "SOURCE_CONFLICT"
    AMBIGUOUS_POLICY = "AMBIGUOUS_POLICY"
    UNSUPPORTED_RULE = "UNSUPPORTED_RULE"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    EXTRACTION_INCOMPLETE = "EXTRACTION_INCOMPLETE"
    INCOMPATIBLE_SCALE = "INCOMPATIBLE_SCALE"
    DATE_PRECISION_INSUFFICIENT = "DATE_PRECISION_INSUFFICIENT"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    BUDGET_LIMIT = "BUDGET_LIMIT"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    INPUT_VERSION_CHANGED = "INPUT_VERSION_CHANGED"


class TaskKind(StrEnum):
    DOCUMENT = "DOCUMENT"
    TASK = "TASK"
    STATEMENT = "STATEMENT"


class Applicability(StrEnum):
    APPLIES = "APPLIES"
    DOES_NOT_APPLY = "DOES_NOT_APPLY"
    UNKNOWN = "UNKNOWN"


class ChecklistStatus(StrEnum):
    TODO = "TODO"
    DONE = "DONE"


class ApplicationState(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"


class DraftValidation(StrEnum):
    PENDING = "PENDING"
    VALID = "VALID"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"


class ClaimStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNVERIFIABLE = "UNVERIFIABLE"


class NotificationKind(StrEnum):
    SOURCE_CHANGED = "SOURCE_CHANGED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


class DeletionStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class ReviewAction(StrEnum):
    ACCEPT = "ACCEPT"
    CORRECT = "CORRECT"
    REJECT = "REJECT"


class DemoScenario(StrEnum):
    MET_READY = "MET_READY"
    GPA_NOT_MET = "GPA_NOT_MET"
    UNKNOWN_AUTHORIZATION = "UNKNOWN_AUTHORIZATION"


class ArtifactType(StrEnum):
    OPPORTUNITY = "opportunity"
    EVALUATION = "evaluation"
    DRAFT = "draft"
