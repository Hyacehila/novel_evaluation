from __future__ import annotations


class PromptRuntimeError(RuntimeError):
    """Prompt runtime 基类错误。"""


class PromptAssetNotFoundError(PromptRuntimeError):
    """缺少可用 Prompt 资产。"""


class PromptAssetAmbiguityError(PromptRuntimeError):
    """Prompt 资产选择结果不唯一。"""


class PromptAssetInvalidError(PromptRuntimeError):
    """Prompt 资产内容或结构非法。"""
