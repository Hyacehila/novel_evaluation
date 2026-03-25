from __future__ import annotations

from pydantic import computed_field, field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import InputComposition, SubmissionSourceType
from packages.schemas.common.validators import (
    derive_input_composition,
    ensure_non_empty_text,
)


class ManuscriptChapter(SchemaModel):
    title: str | None = None
    content: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return ensure_non_empty_text(value, "chapter.title")

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        return ensure_non_empty_text(value, "chapter.content")


class ManuscriptOutline(SchemaModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        return ensure_non_empty_text(value, "outline.content")


class Manuscript(SchemaModel):
    title: str
    chapters: list[ManuscriptChapter] | None = None
    outline: ManuscriptOutline | None = None
    sourceType: SubmissionSourceType

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return ensure_non_empty_text(value, "title")

    @model_validator(mode="after")
    def validate_input_presence(self) -> "Manuscript":
        if not self.hasChapters and not self.hasOutline:
            raise ValueError("chapters 与 outline 至少存在一侧。")
        return self

    @computed_field
    @property
    def hasChapters(self) -> bool:
        return bool(self.chapters)

    @computed_field
    @property
    def hasOutline(self) -> bool:
        return self.outline is not None

    @computed_field
    @property
    def inputComposition(self) -> InputComposition:
        return derive_input_composition(
            has_chapters=self.hasChapters,
            has_outline=self.hasOutline,
        )
