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
    standard_refs: list[str] = []


class ClassifiedField(BaseModel):
    field: FieldDescriptor
    level: int
    tags: list[str]
    matches: list[RuleMatch]
    rationale: str


class ClassifyResponse(BaseModel):
    fields: list[ClassifiedField]
    summary: dict[str, int]  # level -> count
