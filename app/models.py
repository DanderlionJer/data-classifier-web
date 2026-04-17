from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FieldDescriptor(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    database: str = ""
    schema_name: str = Field(default="", alias="schema")
    table: str = ""
    column: str = ""
    data_type: str = ""
    comment: str = ""


class RuleMatch(BaseModel):
    rule_id: str
    rule_name: str
    matched_on: str  # column | comment
    standard_refs: list[str] = Field(default_factory=list)


class DataCategory(BaseModel):
    """High-level data type derived from rule tags (see app/rules/tag_categories.json)."""

    id: str
    label_zh: str


class AIEnhancementInfo(BaseModel):
    model: str | None = None
    baseline_level: int
    baseline_tags: list[str] = Field(default_factory=list)
    baseline_rationale: str = ""
    review_suggested: bool = False
    note: str | None = None


class ClassifiedField(BaseModel):
    field: FieldDescriptor
    level: int
    tags: list[str]
    tags_zh: list[str] = Field(
        default_factory=list,
        description="Chinese label per tags[] entry (same order); empty string if unmapped.",
    )
    categories: list[DataCategory] = Field(default_factory=list)
    matches: list[RuleMatch]
    rationale: str
    ai: AIEnhancementInfo | None = None


class ClassifyResponse(BaseModel):
    fields: list[ClassifiedField]
    summary: dict[str, int]  # level -> count
    category_summary: dict[str, int] = Field(default_factory=dict)
    category_labels: dict[str, str] = Field(default_factory=dict)
    tag_labels_zh: dict[str, str] = Field(default_factory=dict)
    country: str | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 from request when provided (audit / UI).",
    )
    applied_frameworks: list[str] = Field(default_factory=list)
    ai_enhancement_applied: bool = False
    ai_model: str | None = None
    ai_provider: str | None = None

