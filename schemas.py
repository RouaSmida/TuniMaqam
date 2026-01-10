"""
TuniMaqam Marshmallow Schemas
=============================
Data validation and serialization schemas using Marshmallow.
Provides type-safe input validation and consistent output formatting.
"""

from marshmallow import Schema, fields, validate, ValidationError


# =============================================================================
# INPUT SCHEMAS (Request Validation)
# =============================================================================

class NotesAnalysisSchema(Schema):
    """Schema for validating note analysis requests."""
    notes = fields.List(
        fields.String(validate=validate.Length(min=1, max=20)),
        required=True,
        validate=validate.Length(min=1, max=50),
        error_messages={"required": "notes list is required"}
    )
    optional_mood = fields.String(
        validate=validate.Length(max=50),
        load_default=None
    )


class ContributionSchema(Schema):
    """Schema for validating maqam contribution submissions."""
    type = fields.String(
        required=True,
        error_messages={"required": "contribution type is required"}
    )
    payload = fields.Dict(
        required=True,
        error_messages={"required": "payload is required"}
    )


class NewMaqamSchema(Schema):
    """Schema for proposing a new maqam."""
    name_en = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "name_en is required"}
    )
    name_ar = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "name_ar is required"}
    )
    emotion = fields.String(validate=validate.Length(max=50), load_default=None)
    usage = fields.String(validate=validate.Length(max=255), load_default=None)
    regions = fields.List(fields.String(), load_default=[])
    ajnas = fields.List(fields.Dict(), load_default=[])
    description_en = fields.String(load_default=None)
    description_ar = fields.String(load_default=None)


class QuizAnswerSchema(Schema):
    """Schema for validating quiz answer submissions."""
    answers = fields.List(
        fields.Raw(allow_none=True),  # Can be string, integer, or None
        required=True,
        error_messages={"required": "answers list is required"}
    )


class RecommendationRequestSchema(Schema):
    """Schema for maqam recommendation requests."""
    mood = fields.String(validate=validate.Length(max=50), load_default=None)
    event = fields.String(validate=validate.Length(max=100), load_default=None)
    region = fields.String(validate=validate.Length(max=50), load_default=None)
    time_period = fields.String(validate=validate.Length(max=50), load_default=None)
    season = fields.String(validate=validate.Length(max=50), load_default=None)
    preserve_heritage = fields.Boolean(load_default=False)
    simple_for_beginners = fields.Boolean(load_default=False)


class ContributionReviewSchema(Schema):
    """Schema for reviewing contributions."""
    status = fields.String(
        required=True,
        validate=validate.OneOf(["accepted", "rejected"]),
        error_messages={"required": "status is required"}
    )


# =============================================================================
# OUTPUT SCHEMAS (Response Serialization)
# =============================================================================

class LocalizedStringSchema(Schema):
    """Schema for bilingual string fields."""
    en = fields.String(allow_none=True)
    ar = fields.String(allow_none=True)


class MaqamBasicSchema(Schema):
    """Schema for basic maqam information (list views)."""
    id = fields.Integer()
    name = fields.Nested(LocalizedStringSchema)
    emotion = fields.Nested(LocalizedStringSchema)
    usage = fields.Dict()
    regions = fields.Dict()
    rarity_level = fields.Nested(LocalizedStringSchema)
    difficulty_label = fields.Nested(LocalizedStringSchema)


class JinsSchema(Schema):
    """Schema for jins (ajnas) data."""
    name = fields.Raw()  # Can be string or dict
    notes = fields.List(fields.String())


class MaqamFullSchema(MaqamBasicSchema):
    """Schema for full maqam details."""
    ajnas = fields.List(fields.Nested(JinsSchema), allow_none=True)
    descriptions = fields.Nested(LocalizedStringSchema)
    related = fields.List(fields.Integer(), allow_none=True)
    emotion_weights = fields.Dict(allow_none=True)
    historical_periods = fields.Dict()
    seasonal_usage = fields.Dict()
    audio_urls = fields.List(fields.String())


class UserStatSchema(Schema):
    """Schema for user statistics."""
    user_id = fields.String()
    best_score = fields.Float()
    quizzes = fields.Integer()
    activities = fields.Integer()
    level = fields.String()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class ContributionOutputSchema(Schema):
    """Schema for contribution output."""
    id = fields.Integer()
    type = fields.String()
    status = fields.String()
    payload = fields.Dict()
    contributor_id = fields.String(allow_none=True)
    created_at = fields.DateTime()


class AnalysisCandidateSchema(Schema):
    """Schema for maqam analysis candidate results."""
    maqam_id = fields.Integer()
    name_en = fields.String()
    name_ar = fields.String()
    confidence = fields.Float()
    precision = fields.Float()
    coverage = fields.Float()
    matched_notes = fields.List(fields.String())


class RecommendationSchema(Schema):
    """Schema for maqam recommendation results."""
    maqam_id = fields.Integer()
    name = fields.String()
    score = fields.Float()
    confidence = fields.Float()
    evidence = fields.List(fields.String())
    reason = fields.String()


class QuizResultSchema(Schema):
    """Schema for quiz grading results."""
    quiz_id = fields.Integer()
    score = fields.Float()
    correct = fields.Integer()
    total = fields.Integer()
    level = fields.String()
    details = fields.List(fields.Dict())


class ErrorSchema(Schema):
    """Schema for error responses."""
    error = fields.String(required=True)
    details = fields.Dict(load_default=None)


# =============================================================================
# SCHEMA INSTANCES (Ready to use)
# =============================================================================

# Input schemas
notes_analysis_schema = NotesAnalysisSchema()
contribution_schema = ContributionSchema()
new_maqam_schema = NewMaqamSchema()
quiz_answer_schema = QuizAnswerSchema()
recommendation_request_schema = RecommendationRequestSchema()
contribution_review_schema = ContributionReviewSchema()

# Output schemas
maqam_basic_schema = MaqamBasicSchema()
maqam_full_schema = MaqamFullSchema()
maqamet_schema = MaqamFullSchema(many=True)
user_stat_schema = UserStatSchema()
contribution_output_schema = ContributionOutputSchema()
contributions_schema = ContributionOutputSchema(many=True)
analysis_candidate_schema = AnalysisCandidateSchema(many=True)
recommendation_schema = RecommendationSchema(many=True)
quiz_result_schema = QuizResultSchema()
error_schema = ErrorSchema()
