from __future__ import annotations

from dataclasses import asdict, dataclass

from packages.schemas.common.enums import NovelType


@dataclass(frozen=True, slots=True)
class TypeLensDefinition:
    lens_id: str
    label: str


_NOVEL_TYPE_LABELS: dict[NovelType, str] = {
    NovelType.FEMALE_GENERAL: "女频通用",
    NovelType.FANTASY_UPGRADE: "玄幻升级",
    NovelType.URBAN_REALITY: "都市现实",
    NovelType.HISTORY_MILITARY: "历史军事",
    NovelType.SCI_FI_APOCALYPSE: "科幻末世",
    NovelType.SUSPENSE_HORROR: "悬疑惊悚",
    NovelType.GAME_DERIVATIVE: "游戏衍生",
    NovelType.GENERAL_FALLBACK: "通用兜底",
}

_TYPE_LENS_CATALOG: dict[NovelType, tuple[TypeLensDefinition, ...]] = {
    NovelType.FEMALE_GENERAL: (
        TypeLensDefinition("emotionImmersion", "情绪钩子与代入"),
        TypeLensDefinition("relationshipAppeal", "关系张力与人物吸引"),
        TypeLensDefinition("emotionPayoff", "情绪递进与兑现"),
        TypeLensDefinition("companionshipValue", "圈层承诺与陪伴价值"),
    ),
    NovelType.FANTASY_UPGRADE: (
        TypeLensDefinition("upgradeLoop", "升级回路清晰度"),
        TypeLensDefinition("powerSystem", "力量体系可读性"),
        TypeLensDefinition("rewardDensity", "奖励密度"),
        TypeLensDefinition("spectaclePayoff", "奇观/爽点兑现"),
    ),
    NovelType.URBAN_REALITY: (
        TypeLensDefinition("realityHook", "现实抓手"),
        TypeLensDefinition("mobilityTension", "地位跃迁/经营张力"),
        TypeLensDefinition("industryCredibility", "行业/现实可信度"),
        TypeLensDefinition("conversionHook", "连载转化抓手"),
    ),
    NovelType.HISTORY_MILITARY: (
        TypeLensDefinition("powerMap", "权力/战争格局清晰度"),
        TypeLensDefinition("historicalTexture", "历史质感与可信度"),
        TypeLensDefinition("strategyPayoff", "谋略兑现"),
        TypeLensDefinition("campaignMomentum", "长线争霸推进"),
    ),
    NovelType.SCI_FI_APOCALYPSE: (
        TypeLensDefinition("conceptUtility", "概念可利用度"),
        TypeLensDefinition("ruleClosure", "规则闭环"),
        TypeLensDefinition("pressureSystem", "生存/技术压力系统"),
        TypeLensDefinition("worldExpansion", "世界扩展潜力"),
    ),
    NovelType.SUSPENSE_HORROR: (
        TypeLensDefinition("mysteryHook", "谜面钩子"),
        TypeLensDefinition("clueFairness", "线索公平性"),
        TypeLensDefinition("tensionSustain", "紧张维持"),
        TypeLensDefinition("revealPayoff", "揭示兑现"),
    ),
    NovelType.GAME_DERIVATIVE: (
        TypeLensDefinition("loopClarity", "副本/循环清晰度"),
        TypeLensDefinition("ruleFeedback", "规则反馈明确性"),
        TypeLensDefinition("buildVariation", "build/玩法变化"),
        TypeLensDefinition("longRunEscalation", "长线 escalations"),
    ),
    NovelType.GENERAL_FALLBACK: (
        TypeLensDefinition("premiseHook", "premise 与钩子"),
        TypeLensDefinition("coreConflict", "核心冲突与目标"),
        TypeLensDefinition("executionReadability", "执行与可读性"),
        TypeLensDefinition("serialPotential", "连载潜力"),
    ),
}


def get_novel_type_label(novel_type: NovelType) -> str:
    return _NOVEL_TYPE_LABELS[novel_type]


def get_type_lens_definitions(novel_type: NovelType) -> tuple[TypeLensDefinition, ...]:
    return _TYPE_LENS_CATALOG[novel_type]


def get_type_lens_ids(novel_type: NovelType) -> tuple[str, ...]:
    return tuple(definition.lens_id for definition in get_type_lens_definitions(novel_type))


def build_type_lens_catalog_payload() -> dict[str, object]:
    return {
        "types": {
            novel_type.value: {
                "label": get_novel_type_label(novel_type),
                "lenses": [asdict(definition) for definition in get_type_lens_definitions(novel_type)],
            }
            for novel_type in NovelType
        }
    }
