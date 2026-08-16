"""Deterministic realistic ProjectBriefPack corpus for Window-PPTX v6.

The corpus is synthetic and standardized for reproducible evaluation.  The
academic dataset metadata is tied to the public DCRNN paper; all claimed
experiment results are explicitly tied to a synthetic experiment log.
"""

from __future__ import annotations

from typing import Any, Iterable

from .project_brief import lock_project_brief_pack


FLAGSHIP_SCENARIO_IDS = frozenset(
    {
        "annual-work-report",
        "campus-competition-defense",
        "academic-thesis-defense",
    }
)
REQUIRED_SCENARIO_IDS = frozenset(
    {
        *FLAGSHIP_SCENARIO_IDS,
        "business-operations-review",
        "project-proposal",
        "product-launch",
        "market-analysis",
        "sales-proposal",
        "investor-pitch",
        "strategy-planning",
        "data-analysis-report",
        "training-course",
        "brand-company-introduction",
        "project-kickoff",
        "ecommerce-marketing-plan",
    }
)


def _metric(
    fact_id: str,
    claim_key: str,
    value: str | int | float,
    unit: str,
    time_scope: str,
    *,
    source_id: str = "synthetic-client-source",
    text: str | None = None,
    semantic: str = "metrics",
) -> dict[str, Any]:
    return {
        "id": fact_id,
        "kind": "metric",
        "text": text or f"{claim_key}：{value} {unit}",
        "language": "zh-CN",
        "source_id": source_id,
        "locator": f"locked-facts/{fact_id}",
        "required": True,
        "value": value,
        "unit": unit,
        "claim_key": claim_key,
        "time_scope": time_scope,
        "status": "active",
        "recommended_semantic": semantic,
    }


def _claim(
    fact_id: str,
    text: str,
    *,
    source_id: str = "synthetic-client-source",
    semantic: str = "statement",
) -> dict[str, Any]:
    return {
        "id": fact_id,
        "kind": "claim",
        "text": text,
        "language": "zh-CN",
        "source_id": source_id,
        "locator": f"locked-facts/{fact_id}",
        "required": True,
        "status": "active",
        "recommended_semantic": semantic,
    }


def _sources(
    *,
    academic: bool = False,
) -> list[dict[str, str]]:
    if academic:
        return [
            {
                "id": "dcrnn-paper",
                "kind": "document",
                "locator": "https://arxiv.org/abs/1707.01926",
            },
            {
                "id": "synthetic-experiment-log",
                "kind": "data",
                "locator": "synthetic://mdgformer/experiment-log-v1",
            },
            {
                "id": "synthetic-defense-request",
                "kind": "request",
                "locator": "synthetic://academic-defense/client-request-v1",
            },
        ]
    return [
        {
            "id": "synthetic-client-source",
            "kind": "data",
            "locator": "synthetic://pptx-studio-v6/client-source",
        },
        {
            "id": "synthetic-client-request",
            "kind": "request",
            "locator": "synthetic://pptx-studio-v6/client-request",
        },
    ]


def _anatomy(
    sections: int,
    appendix: int,
) -> list[dict[str, Any]]:
    return [
        {"role": "cover", "required": True, "min_count": 1, "max_count": 1},
        {"role": "directory", "required": True, "min_count": 1, "max_count": 1},
        {
            "role": "section-divider",
            "required": True,
            "min_count": sections,
            "max_count": sections,
        },
        {"role": "evidence-body", "required": True, "min_count": 6, "max_count": 40},
        {"role": "decision", "required": True, "min_count": 1, "max_count": 3},
        {"role": "closing", "required": True, "min_count": 1, "max_count": 1},
        {
            "role": "appendix",
            "required": appendix > 0,
            "min_count": appendix,
            "max_count": appendix,
        },
    ]


def _assets(
    roles: Iterable[str],
    *,
    source_id: str = "synthetic-client-source",
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"asset-{index}-{role.replace('_', '-')}",
            "role": role,
            "source_id": source_id,
            "locator": f"synthetic://assets/{role}",
            "rights": "synthetic-evaluation-only",
            "required": True,
        }
        for index, role in enumerate(roles, start=1)
    ]


def _base_pack(
    *,
    scenario_id: str,
    title: str,
    request: str,
    audience: str,
    decision: str,
    facts: list[dict[str, Any]],
    asset_roles: tuple[str, ...],
    main: int,
    appendix: int,
    backup: int,
    presentation_minutes: int,
    qa_minutes: int,
    sections: int,
    tone: str,
    prohibitions: tuple[str, ...],
    academic: bool = False,
) -> dict[str, Any]:
    source_id = "synthetic-defense-request" if academic else "synthetic-client-request"
    fact_sources = _sources(academic=academic)
    pack = {
        "schema_version": "1.0",
        "brief_id": f"{scenario_id}-v1",
        "scenario_id": scenario_id,
        "state": "NeedsDiscussion",
        "raw_intake": {
            "request_id": f"V6-{scenario_id.upper()}-001",
            "received_at": "2026-07-29",
            "language": "zh-CN",
            "original_request": request,
            "attachments": [
                {
                    "id": "structured-source",
                    "locator": fact_sources[0]["locator"],
                    "kind": "data" if not academic else "document",
                    "rights": (
                        "public-citation-plus-synthetic-results"
                        if academic
                        else "synthetic-evaluation-only"
                    ),
                }
            ],
        },
        "fact_store": {
            "schema_version": "1.0",
            "project": {
                "title": title,
                "objective": decision,
                "audience": audience,
                "language": "zh-CN",
            },
            "sources": fact_sources,
            "facts": [
                *facts,
                _claim(
                    "presentation-decision",
                    f"本次演示必须促成的决定：{decision}",
                    source_id=source_id,
                    semantic="recommendation",
                ),
            ],
        },
        "assets": _assets(
            asset_roles,
            source_id=(
                "synthetic-experiment-log"
                if academic
                else "synthetic-client-source"
            ),
        ),
        "audience": {
            "primary": audience,
            "knowledge_level": "expert",
            "decision_role": decision,
        },
        "goals": {
            "purpose": title,
            "decision": decision,
            "success_outcomes": [
                "观众能够复述核心结论与证据链",
                "观众对下一步行动、责任人和边界形成明确决定",
            ],
        },
        "timing": {
            "presentation_minutes": presentation_minutes,
            "qa_minutes": qa_minutes,
        },
        "brand": {
            "tone": tone,
            "mode": "light",
            "required_colors": [],
            "forbidden_styles": ["neon", "cartoon", "random-gradient", "clip-art"],
        },
        "slide_budget": {
            "main": main,
            "minimum": max(8, main - 2),
            "maximum": main + 2,
            "appendix": appendix,
            "backup": backup,
        },
        "anatomy": _anatomy(sections, appendix),
        "decisions": [decision],
        "prohibitions": list(prohibitions),
        "rubric": [
            {"criterion": "narrative", "weight": 0.30, "minimum_score": 4.2},
            {"criterion": "art-direction", "weight": 0.30, "minimum_score": 4.2},
            {"criterion": "evidence", "weight": 0.20, "minimum_score": 4.2},
            {"criterion": "editability", "weight": 0.20, "minimum_score": 4.2},
        ],
        "unresolved_questions": [],
        "lock_sha256": None,
    }
    return lock_project_brief_pack(pack)


def _work_report() -> dict[str, Any]:
    facts: list[dict[str, Any]] = []
    quarterly = {
        "customer-count": ([46, 59, 76, 94], "家"),
        "monthly-active-users": ([1840, 2320, 3080, 4260], "人"),
        "self-service-rate": ([38, 46, 57, 68], "%"),
        "report-sla": ([89, 92, 95, 97], "%"),
        "p1-incidents": ([6, 4, 3, 2], "起"),
        "availability": ([99.82, 99.88, 99.92, 99.95], "%"),
        "query-cloud-cost": ([8.40, 7.60, 6.90, 6.10], "元/千次"),
    }
    for claim_key, (values, unit) in quarterly.items():
        for index, value in enumerate(values, start=1):
            facts.append(
                _metric(
                    f"{claim_key}-q{index}",
                    claim_key,
                    value,
                    unit,
                    f"2026-Q{index}",
                )
            )
    facts.extend(
        [
            _metric("customers-target", "customer-count", 90, "家", "2026-target"),
            _metric("customers-actual", "customer-count", 94, "家", "2026-actual"),
            _metric("self-service-target", "self-service-rate", 65, "%", "2026-target"),
            _metric("self-service-actual", "self-service-rate", 68, "%", "2026-actual"),
            _metric("projects-on-time", "on-time-projects", 10, "个", "2026"),
            _metric("projects-total", "total-projects", 12, "个", "2026"),
            _metric("nps-target", "nps", 42, "分", "2026-target"),
            _metric("nps-actual", "nps", 45, "分", "2026-actual"),
            _metric("budget-plan", "annual-budget", 12, "百万元", "2026-budget"),
            _metric("budget-actual", "annual-budget", 11.6, "百万元", "2026-actual"),
            _metric("governed-metrics", "governed-metrics", 38, "项", "2026-Q4"),
            _metric("duplicates-before", "duplicate-metrics", 126, "项", "before"),
            _metric("duplicates-after", "duplicate-metrics", 41, "项", "after"),
            _metric("weekly-queries", "weekly-queries", 2140, "次/周", "2026-Q4"),
            _metric("acceptance-rate", "acceptance-rate", 76, "%", "2026"),
            _metric("annual-savings", "annual-savings", 2.8, "百万元", "2026"),
            _metric("unowned-metrics", "unowned-metrics", 17, "项", "2026-Q4"),
            _metric("unmigrated-customers", "unmigrated-customers", 3, "家", "2026-Q4"),
            _claim("work-boundary", "节省金额为经财务确认的年度化估算，不等同于已回款收入。"),
        ]
    )
    return _base_pack(
        scenario_id="annual-work-report",
        title="2026 数据产品与客户成功年度经营复盘",
        request=(
            "为经营委员会制作年度工作汇报。必须同时呈现增长、质量、效率、"
            "项目交付、预算、客户价值与风险，保留目录、四个章节、决策页、"
            "结束页和四页附录；所有数字都来自本 brief，不得补造案例。"
        ),
        audience="经营委员会、财务负责人、产品与客户成功负责人",
        decision="批准 2027 年数据治理、客户迁移和自助分析三项投入优先级",
        facts=facts,
        asset_roles=(
            "quarterly-kpi-dashboard",
            "customer-case-photo",
            "editable-budget-table",
            "governance-before-after-diagram",
            "team-portrait-grid",
        ),
        main=28,
        appendix=4,
        backup=0,
        presentation_minutes=25,
        qa_minutes=10,
        sections=4,
        tone="institutional-annual-editorial",
        prohibitions=(
            "不得虚构客户名称、证言或合同金额",
            "不得将目标值写成已实现",
            "不得隐藏 17 项无负责人指标和 3 家未迁移客户",
        ),
    )


def _campus_defense() -> dict[str, Any]:
    facts = [
        _metric("sensor-nodes", "sensor-nodes", 18, "个", "pilot"),
        _metric("pilot-days", "pilot-days", 84, "天", "pilot"),
        _metric("sampling-interval", "sampling-interval", 10, "分钟", "pilot"),
        _metric("theoretical-records", "theoretical-records", 217728, "条", "pilot"),
        _metric("valid-records", "valid-records", 214680, "条", "pilot"),
        _metric("valid-rate", "valid-record-rate", 98.6, "%", "pilot"),
        _metric("paired-events", "paired-events", 612, "组", "pilot"),
        _metric("alerts", "alerts", 37, "次", "pilot"),
        _metric("confirmed-alerts", "confirmed-alerts", 30, "次", "pilot"),
        _metric("actual-events", "actual-events", 33, "次", "pilot"),
        _metric("precision", "alert-precision", 81.1, "%", "pilot"),
        _metric("recall", "alert-recall", 90.9, "%", "pilot"),
        _metric("f1", "alert-f1", 85.7, "%", "pilot"),
        _metric("lead-time", "lead-time", 42, "分钟", "pilot"),
        _metric("hours-before", "inspection-hours", 9.6, "小时/周", "before-pilot"),
        _metric("hours-pilot", "inspection-hours", 4.1, "小时/周", "pilot"),
        _metric("student-interviews", "interviews-students", 38, "人", "research"),
        _metric("staff-interviews", "interviews-staff", 29, "人", "research"),
        _metric("manager-interviews", "interviews-managers", 24, "人", "research"),
        _metric("bom", "bom-cost", 1860, "元", "prototype"),
        _metric("price", "list-price", 2980, "元", "proposal"),
        _metric("service-fee", "annual-service-fee", 680, "元/年", "proposal"),
        _metric("market", "addressable-campus", 4120, "所", "estimate"),
        _metric("serviceable-market", "serviceable-campus", 620, "所", "estimate"),
        _claim("pilot-limitation", "9.6 小时降至 4.1 小时仅在单校 84 天试点成立。"),
    ]
    return _base_pack(
        scenario_id="campus-competition-defense",
        title="校园实验室安全巡检与提前预警系统竞赛答辩",
        request=(
            "为省级大学生创新竞赛制作 7 分钟答辩。需要问题洞察、用户访谈、"
            "系统架构、硬件样机、校园地图、试点数据、算法验证、商业模式、"
            "BOM、团队与知识产权；主讲 22 页、附录 4 页、可选答辩备份 6 页。"
        ),
        audience="竞赛评委、行业导师与学校实验室管理者",
        decision="认可项目进入省赛终审并批准下一阶段多校验证",
        facts=facts,
        asset_roles=(
            "campus-pilot-map",
            "device-cad-exploded-view",
            "prototype-photo",
            "editable-system-architecture",
            "pilot-dashboard",
        ),
        main=22,
        appendix=4,
        backup=6,
        presentation_minutes=7,
        qa_minutes=5,
        sections=4,
        tone="youth-technology-competition",
        prohibitions=(
            "不得将试点结果外推为规模化商业效果",
            "不得将 42 分钟提前量描述为对所有事件的保证",
            "不得虚构专利授权、学校采购或商业收入",
        ),
    )


def _academic_defense() -> dict[str, Any]:
    public = "dcrnn-paper"
    experiment = "synthetic-experiment-log"
    facts = [
        _metric("metr-sensors", "dataset-sensors", 207, "个", "metr-la", source_id=public),
        _metric("metr-observations", "dataset-observations", 34272, "步", "metr-la", source_id=public),
        _metric("pems-sensors", "dataset-sensors", 325, "个", "pems-bay", source_id=public),
        _metric("pems-observations", "dataset-observations", 52116, "步", "pems-bay", source_id=public),
        _metric("sample-minutes", "sampling-interval", 5, "分钟", "both", source_id=public),
        _metric("split-train", "data-split", 70, "%", "train", source_id=public),
        _metric("split-valid", "data-split", 10, "%", "validation", source_id=public),
        _metric("split-test", "data-split", 20, "%", "test", source_id=public),
    ]
    tables = {
        "metr-la": {
            "ha": (4.16, 4.96, 5.71),
            "dcrnn": (2.77, 3.15, 3.60),
            "gwn": (2.69, 3.07, 3.53),
            "stfgnn": (2.66, 3.02, 3.45),
            "mdgformer": (2.58, 2.92, 3.31),
        },
        "pems-bay": {
            "ha": (2.88, 3.47, 4.12),
            "dcrnn": (1.38, 1.74, 2.07),
            "gwn": (1.30, 1.63, 1.95),
            "stfgnn": (1.27, 1.59, 1.90),
            "mdgformer": (1.23, 1.52, 1.82),
        },
    }
    for dataset, models in tables.items():
        for model, values in models.items():
            for horizon, value in zip(("15min", "30min", "60min"), values):
                facts.append(
                    _metric(
                        f"mae-{model}-{dataset}-{horizon}",
                        f"mae-{model}-{dataset}",
                        value,
                        "MAE",
                        horizon,
                        source_id=experiment,
                        semantic="table",
                    )
                )
    facts.extend(
        [
            _metric("std-15", "std-mdgformer-metr-la", 0.03, "MAE", "15min", source_id=experiment),
            _metric("std-30", "std-mdgformer-metr-la", 0.04, "MAE", "30min", source_id=experiment),
            _metric("std-60", "std-mdgformer-metr-la", 0.05, "MAE", "60min", source_id=experiment),
            _metric("pems-std-15", "std-mdgformer-pems-bay", 0.02, "MAE", "15min", source_id=experiment),
            _metric("pems-std-30", "std-mdgformer-pems-bay", 0.03, "MAE", "30min", source_id=experiment),
            _metric("pems-std-60", "std-mdgformer-pems-bay", 0.04, "MAE", "60min", source_id=experiment),
            _metric("ablation-full", "ablation-full", 3.31, "MAE", "metr-la-60min", source_id=experiment),
            _metric("ablation-static", "ablation-static-graph", 3.46, "MAE", "metr-la-60min", source_id=experiment),
            _metric("ablation-scale", "ablation-no-multiscale", 3.42, "MAE", "metr-la-60min", source_id=experiment),
            _metric("ablation-curriculum", "ablation-no-curriculum", 3.39, "MAE", "metr-la-60min", source_id=experiment),
            _metric("missing-gwn-10", "missing-gwn", 3.86, "MAE", "10pct", source_id=experiment),
            _metric("missing-ours-10", "missing-ours", 3.59, "MAE", "10pct", source_id=experiment),
            _metric("missing-gwn-20", "missing-gwn", 4.28, "MAE", "20pct", source_id=experiment),
            _metric("missing-ours-20", "missing-ours", 3.91, "MAE", "20pct", source_id=experiment),
            _metric("params-gwn", "params-gwn", 3.06, "M", "experiment", source_id=experiment),
            _metric("latency-gwn", "inference-gwn", 9.4, "ms", "experiment", source_id=experiment),
            _metric("params-stfgnn", "params-stfgnn", 3.67, "M", "experiment", source_id=experiment),
            _metric("latency-stfgnn", "inference-stfgnn", 12.1, "ms", "experiment", source_id=experiment),
            _metric("params-ours", "params-ours", 3.18, "M", "experiment", source_id=experiment),
            _metric("latency-ours", "inference-ours", 10.6, "ms", "experiment", source_id=experiment),
            _claim(
                "academic-limit",
                "所有模型对比、消融、缺失数据和效率结果均为标准化合成实验日志，用于 PPT 工作流评测，不代表已发表论文结果。",
                source_id=experiment,
            ),
        ]
    )
    return _base_pack(
        scenario_id="academic-thesis-defense",
        title="MDGFormer：多尺度动态图交通速度预测方法硕士答辩",
        request=(
            "制作 15 分钟硕士论文答辩，覆盖研究问题、相关工作、方法架构、"
            "两个公开数据集、实验设置、完整对比表、消融、缺失数据鲁棒性、"
            "效率、局限性、结论和引用；主讲 26 页、附录 6 页。"
        ),
        audience="硕士答辩委员会与交通预测研究人员",
        decision="确认论文达到答辩要求并形成修改意见",
        facts=facts,
        asset_roles=(
            "method-architecture-diagram",
            "sensor-network-map",
            "editable-comparison-table",
            "ablation-chart",
            "citation-list",
        ),
        main=26,
        appendix=6,
        backup=0,
        presentation_minutes=15,
        qa_minutes=10,
        sections=5,
        tone="data-research-editorial",
        prohibitions=(
            "不得声称达到 SOTA",
            "不得把标准化合成实验写成已发表结果",
            "不得省略局限性、方差或来源边界",
        ),
        academic=True,
    )


SKELETON_SPECS: dict[str, dict[str, Any]] = {
    "business-operations-review": {
        "title": "连锁门店季度经营复盘",
        "audience": "事业部总经理、区域负责人、财务与供应链负责人",
        "decision": "确定低效门店整改、库存调拨与下季度促销优先级",
        "facts": (
            ("revenue", 86.4, "百万元", "2026-Q2"),
            ("revenue-growth", 12.8, "%", "同比"),
            ("gross-margin", 41.6, "%", "2026-Q2"),
            ("same-store-growth", 7.2, "%", "2026-Q2"),
            ("inventory-days", 48, "天", "2026-Q2"),
            ("stockout-rate", 3.1, "%", "2026-Q2"),
            ("low-efficiency-stores", 14, "家", "2026-Q2"),
            ("member-sales-share", 63, "%", "2026-Q2"),
        ),
        "assets": ("regional-map", "editable-waterfall-chart", "store-matrix"),
    },
    "project-proposal": {
        "title": "制造企业质量数据中台项目提案",
        "audience": "客户 CIO、质量负责人、采购与项目管理办公室",
        "decision": "批准 16 周一期范围、预算和联合项目组",
        "facts": (
            ("sites", 6, "座", "scope"),
            ("source-systems", 11, "套", "scope"),
            ("quality-records", 2400, "万条/年", "baseline"),
            ("manual-report-hours", 320, "小时/月", "baseline"),
            ("phase-one-weeks", 16, "周", "proposal"),
            ("budget", 3.6, "百万元", "proposal"),
            ("target-cycle-reduction", 45, "%", "target"),
            ("target-data-completeness", 98, "%", "target"),
        ),
        "assets": ("solution-architecture", "implementation-roadmap", "scope-table"),
    },
    "product-launch": {
        "title": "企业知识助手产品发布会",
        "audience": "客户、合作伙伴、媒体与内部销售团队",
        "decision": "推动目标客户申请试用并让渠道伙伴加入联合销售",
        "facts": (
            ("pilot-customers", 32, "家", "closed-beta"),
            ("documents-indexed", 860, "万份", "closed-beta"),
            ("answer-acceptance", 78, "%", "closed-beta"),
            ("median-response", 2.4, "秒", "closed-beta"),
            ("admin-hours-saved", 18, "小时/周", "median"),
            ("launch-price", 98000, "元/年", "standard"),
            ("trial-days", 30, "天", "launch"),
            ("launch-partners", 8, "家", "launch"),
        ),
        "assets": ("product-hero", "ui-mockup", "demo-journey"),
    },
    "market-analysis": {
        "title": "中国工业视觉质检软件市场分析",
        "audience": "公司战略委员会、产品与投资负责人",
        "decision": "选择汽车零部件和消费电子作为两条优先行业线",
        "facts": (
            ("tam", 68, "亿元", "2026"),
            ("sam", 21, "亿元", "2026"),
            ("som", 3.2, "亿元", "2028-target"),
            ("market-cagr", 19.4, "%", "2023-2028"),
            ("interviews", 46, "家", "research"),
            ("competitors", 17, "家", "research"),
            ("auto-willingness", 72, "%", "research"),
            ("electronics-willingness", 64, "%", "research"),
        ),
        "assets": ("market-funnel", "competitor-matrix", "industry-map"),
    },
    "sales-proposal": {
        "title": "区域银行智能营销销售提案",
        "audience": "零售银行负责人、数据平台主管与采购委员会",
        "decision": "批准三个月联合验证和 120 万元一期采购预算",
        "facts": (
            ("customers", 460, "万户", "client-baseline"),
            ("campaigns", 38, "场/月", "client-baseline"),
            ("response-rate", 1.8, "%", "client-baseline"),
            ("target-response", 2.5, "%", "pilot-target"),
            ("pilot-months", 3, "个月", "proposal"),
            ("pilot-segments", 6, "类", "proposal"),
            ("phase-one-budget", 1.2, "百万元", "proposal"),
            ("payback-months", 11, "个月", "estimate"),
        ),
        "assets": ("customer-journey", "roi-model", "solution-workflow"),
    },
    "investor-pitch": {
        "title": "工业能效 SaaS Pre-A 轮融资演示",
        "audience": "产业投资机构与财务投资人",
        "decision": "进入尽调并讨论 3000 万元 Pre-A 轮投资",
        "facts": (
            ("arr", 18.6, "百万元", "2026-Q2"),
            ("arr-growth", 146, "%", "同比"),
            ("customers", 74, "家", "2026-Q2"),
            ("net-retention", 118, "%", "2026-Q2"),
            ("gross-margin", 71, "%", "2026-Q2"),
            ("cac-payback", 13, "个月", "2026-Q2"),
            ("funding-ask", 30, "百万元", "round"),
            ("runway", 24, "个月", "post-round"),
        ),
        "assets": ("traction-chart", "business-model", "use-of-funds"),
    },
    "strategy-planning": {
        "title": "2027–2029 海外增长战略规划",
        "audience": "董事会、国际业务负责人和产品委员会",
        "decision": "批准东南亚优先、欧洲验证的三年资源配置方案",
        "facts": (
            ("overseas-revenue", 92, "百万元", "2026"),
            ("overseas-share", 18, "%", "2026"),
            ("sea-cagr", 24, "%", "2024-2029"),
            ("europe-cagr", 11, "%", "2024-2029"),
            ("priority-countries", 4, "个", "2027"),
            ("localized-products", 3, "款", "2027"),
            ("three-year-investment", 160, "百万元", "2027-2029"),
            ("target-share", 35, "%", "2029"),
        ),
        "assets": ("world-map", "strategy-choice-matrix", "three-year-roadmap"),
    },
    "data-analysis-report": {
        "title": "订阅产品流失驱动因素分析",
        "audience": "产品、增长、客服与财务管理层",
        "decision": "批准针对前三项流失驱动因素的 90 天实验计划",
        "facts": (
            ("accounts", 48200, "个", "analysis"),
            ("churn-rate", 6.8, "%/月", "baseline"),
            ("onboarding-churn", 11.2, "%/月", "segment"),
            ("support-churn", 9.6, "%/月", "segment"),
            ("low-usage-churn", 13.4, "%/月", "segment"),
            ("model-auc", 0.82, "AUC", "validation"),
            ("addressable-arr", 24, "百万元", "estimate"),
            ("experiment-days", 90, "天", "proposal"),
        ),
        "assets": ("cohort-heatmap", "driver-ranking", "experiment-roadmap"),
    },
    "training-course": {
        "title": "一线经理结构化复盘培训课件",
        "audience": "新任一线经理与业务 HR",
        "decision": "学员完成一次可观察、可行动的团队复盘",
        "facts": (
            ("learners", 36, "人/班", "design"),
            ("duration", 180, "分钟", "design"),
            ("modules", 4, "个", "design"),
            ("case-minutes", 45, "分钟", "design"),
            ("practice-minutes", 60, "分钟", "design"),
            ("assessment-items", 12, "题", "design"),
            ("pass-score", 80, "分", "assessment"),
            ("followup-days", 30, "天", "transfer"),
        ),
        "assets": ("learning-map", "case-canvas", "facilitator-timeline"),
    },
    "brand-company-introduction": {
        "title": "新能源材料公司品牌与能力介绍",
        "audience": "潜在客户、合作伙伴、政府园区与候选人才",
        "decision": "建立可信认知并进入客户验证或合作洽谈",
        "facts": (
            ("founded", 2018, "年", "company"),
            ("employees", 620, "人", "2026"),
            ("rd-share", 22, "%", "2026"),
            ("patents", 86, "项", "2026"),
            ("production-lines", 7, "条", "2026"),
            ("annual-capacity", 32000, "吨", "2026"),
            ("customers", 48, "家", "2026"),
            ("export-markets", 12, "个", "2026"),
        ),
        "assets": ("factory-photo", "capability-map", "milestone-timeline"),
    },
    "project-kickoff": {
        "title": "集团 ERP 云迁移项目启动会",
        "audience": "集团高管、业务负责人、IT 团队与实施伙伴",
        "decision": "确认范围、治理机制、关键里程碑和风险升级路径",
        "facts": (
            ("entities", 23, "家", "scope"),
            ("users", 6800, "人", "scope"),
            ("interfaces", 146, "个", "scope"),
            ("waves", 4, "批", "plan"),
            ("months", 14, "个月", "plan"),
            ("core-team", 42, "人", "plan"),
            ("critical-risks", 9, "项", "kickoff"),
            ("go-live-window", 72, "小时", "constraint"),
        ),
        "assets": ("governance-chart", "migration-roadmap", "risk-escalation-flow"),
    },
    "ecommerce-marketing-plan": {
        "title": "双十一全域电商增长方案",
        "audience": "品牌总经理、电商、媒介、内容与供应链团队",
        "decision": "批准 1800 万元预算分配、货品策略和战役节奏",
        "facts": (
            ("gmv-target", 120, "百万元", "campaign"),
            ("budget", 18, "百万元", "campaign"),
            ("roas-target", 6.7, "倍", "campaign"),
            ("new-customer-target", 180000, "人", "campaign"),
            ("member-sales-target", 58, "%", "campaign"),
            ("hero-skus", 8, "个", "campaign"),
            ("content-assets", 320, "条", "campaign"),
            ("campaign-days", 28, "天", "campaign"),
        ),
        "assets": ("campaign-calendar", "channel-budget-table", "funnel-dashboard"),
    },
}


def _skeleton(scenario_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    facts = [
        _metric(
            f"{claim_key}-{index}",
            claim_key,
            value,
            unit,
            time_scope,
        )
        for index, (claim_key, value, unit, time_scope) in enumerate(
            spec["facts"],
            start=1,
        )
    ]
    return _base_pack(
        scenario_id=scenario_id,
        title=spec["title"],
        request=(
            f"请制作一份可直接用于真实会议的《{spec['title']}》。"
            "必须给出结论先行的商业叙事、目录和章节页，使用 brief 中的详细"
            "数据与素材角色，结尾明确决定、负责人和下一步；不得用空洞占位文案。"
        ),
        audience=spec["audience"],
        decision=spec["decision"],
        facts=facts,
        asset_roles=spec["assets"],
        main=18,
        appendix=3,
        backup=0,
        presentation_minutes=20,
        qa_minutes=10,
        sections=4,
        tone="consulting-executive",
        prohibitions=(
            "不得虚构外部背书、客户证言或已实现收益",
            "不得省略假设、限制和待验证项",
        ),
    )


def load_project_brief_corpus() -> dict[str, dict[str, Any]]:
    """Build and lock all fifteen canonical realistic scenario packs."""

    corpus = {
        "annual-work-report": _work_report(),
        "campus-competition-defense": _campus_defense(),
        "academic-thesis-defense": _academic_defense(),
        **{
            scenario_id: _skeleton(scenario_id, spec)
            for scenario_id, spec in SKELETON_SPECS.items()
        },
    }
    if set(corpus) != REQUIRED_SCENARIO_IDS:
        missing = sorted(REQUIRED_SCENARIO_IDS - set(corpus))
        extra = sorted(set(corpus) - REQUIRED_SCENARIO_IDS)
        raise RuntimeError(f"CORPUS_INVENTORY_MISMATCH missing={missing} extra={extra}")
    return dict(sorted(corpus.items()))


__all__ = [
    "FLAGSHIP_SCENARIO_IDS",
    "REQUIRED_SCENARIO_IDS",
    "SKELETON_SPECS",
    "load_project_brief_corpus",
]
