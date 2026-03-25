from __future__ import annotations

from packages.schemas.common.enums import InputComposition


def ensure_non_empty_text(value: str, field_name: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} 不能为空。")
    return text


def ensure_optional_text(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    return ensure_non_empty_text(value, field_name)


def derive_input_composition(has_chapters: bool, has_outline: bool) -> InputComposition:
    if has_chapters and has_outline:
        return InputComposition.CHAPTERS_OUTLINE
    if has_chapters:
        return InputComposition.CHAPTERS_ONLY
    if has_outline:
        return InputComposition.OUTLINE_ONLY
    raise ValueError("chapters 与 outline 至少存在一侧。")


def validate_input_composition(
    *,
    has_chapters: bool,
    has_outline: bool,
    input_composition: InputComposition,
) -> InputComposition:
    expected = derive_input_composition(has_chapters, has_outline)
    if input_composition is not expected:
        raise ValueError("inputComposition 必须由输入内容派生，不能手工篡改。")
    return input_composition


def validate_percentage(value: int, field_name: str) -> int:
    if value < 0 or value > 100:
        raise ValueError(f"{field_name} 必须在 0 到 100 之间。")
    return value


def validate_confidence(value: float, field_name: str) -> float:
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} 必须在 0 到 1 之间。")
    return value
