from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from finagent.devtools import EmptyMarketGraphStore, InMemoryMarketDataProvider, InMemoryMemoryVectorStore
from finagent.packages.agents.builders import CandidateResponse, CandidateResponseBuilder
from finagent.packages.agents.user_proxy import UserProxy
from finagent.packages.common.config import Settings
from finagent.packages.common.ids import new_id
from finagent.packages.common.sqlite_store import SQLiteStore
from finagent.packages.orchestrator.models import AgentState, IntentType, Message, TaskFrame, ToolResult
from finagent.packages.orchestrator.pipeline import FinAgentOrchestrator
from finagent.packages.tools.executor import build_default_registry
from finagent.packages.tools.registry import ToolContext


REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPO_ROOT / "data" / "finagent" / "finagent_tool_calling_seed20.jsonl"
WORK_DB_PATH = REPO_ROOT / ".codex-run" / "seed-build.sqlite3"
DATASET_VERSION = "seed20-v1"


@dataclass(frozen=True)
class Seed:
    seed_id: str
    scenario_kind: str
    user_input: str
    candidate_answer: str
    expected_intent: IntentType
    expected_status: str
    bindings: dict[str, tuple[str, str, str]] = field(default_factory=dict)
    history: tuple[tuple[str, str], ...] = ()
    active_task: tuple[IntentType, str] | None = None
    account_scope: str | None = "default"
    risk_level: str = "balanced"
    note: str = ""


SEEDS: tuple[Seed, ...] = (
    Seed(
        seed_id="finagent-seed-001",
        scenario_kind="single_tool_call",
        user_input="AAPL 现在的股价是多少",
        candidate_answer=(
            "苹果（AAPL）最新报价 {price} 美元，较上一交易日变动 {change}%，交易所为 NASDAQ，"
            "数据来自实时行情快照。单日涨跌只说明当前报价位置，不能据此推断后续方向；"
            "如果要评估持仓影响，还需要结合成本价、持仓数量与时间窗口。"
        ),
        expected_intent=IntentType.MARKET_QUOTE,
        expected_status="completed",
        bindings={
            "price": ("get_realtime_stock", "price", ",.2f"),
            "change": ("get_realtime_stock", "change_percent", ".2f"),
        },
        note="单工具行情查询，覆盖率最高的主路径",
    ),
    Seed(
        seed_id="finagent-seed-002",
        scenario_kind="single_tool_call",
        user_input="USD/JPY 的汇率现在是多少",
        candidate_answer=(
            "美元兑日元参考汇率 {rate}，日内变动 {change}%，来源为宏观行情快照。"
            "汇率水平本身不构成交易信号；若持有日元资产或存在日元负债，"
            "还需要核对换算口径、结算时点与点差成本。"
        ),
        expected_intent=IntentType.MARKET_QUOTE,
        expected_status="completed",
        bindings={
            "rate": ("get_forex_rate", "rate", ",.2f"),
            "change": ("get_forex_rate", "change_percent", ".2f"),
        },
        note="汇率分支，走 market_agent 的 forex 路径",
    ),
    Seed(
        seed_id="finagent-seed-003",
        scenario_kind="multi_tool_call",
        user_input="600519.SH 现在 100 股市值多少",
        candidate_answer=(
            "贵州茅台（600519.SH）最新报价 {price} 元，100 股对应市值 {market_value} 元，交易所为 SSE。"
            "该结果为报价快照与数量相乘，不包含佣金、印花税与滑点；跨市场比较时需要注意币种与交易时段差异。"
        ),
        expected_intent=IntentType.MARKET_QUOTE,
        expected_status="completed",
        bindings={
            "price": ("get_realtime_stock", "price", ",.2f"),
            "market_value": ("calc_position_value", "market_value", ",.2f"),
        },
        note="行情加数量，触发 calc_position_value 确定性计算",
    ),
    Seed(
        seed_id="finagent-seed-004",
        scenario_kind="single_tool_call",
        user_input="AAPL 最新 10-K 的风险因素有哪些",
        candidate_answer=(
            "苹果最新 10-K 的风险因素章节给出三类主要风险：需求集中与供应约束、"
            "出口管制与客户集中度对收入可见度的影响、以及利率与增长假设同时变化时的估值敏感性。"
            "以上是披露原文要点，不构成买卖建议；引用时应同时标注报告期与章节位置。"
        ),
        expected_intent=IntentType.REPORT_ANALYSIS,
        expected_status="completed",
        bindings={},
        note="SEC 财报检索路径",
    ),
    Seed(
        seed_id="finagent-seed-005",
        scenario_kind="single_tool_call",
        user_input="600519.SH 的年报公告说了什么",
        candidate_answer=(
            "已定位贵州茅台 2025 年年报公告，解析结果给出披露要点摘要，并明确不生成交易指令。"
            "形成结论前需要核对公告发布时间、披露口径与适用市场，"
            "涉及财务数据的部分应以原始公告全文为准。"
        ),
        expected_intent=IntentType.REPORT_ANALYSIS,
        expected_status="completed",
        bindings={},
        note="A 股公告分支，doc_type=annual_report",
    ),
    Seed(
        seed_id="finagent-seed-006",
        scenario_kind="multi_tool_call",
        user_input="美联储加息 25 个基点对我的金融板块持仓有什么影响",
        candidate_answer=(
            "美联储本次加息 25 个基点，目标区间 {target_range}。你的金融板块持仓市值 {total_value} 美元。"
            "情景分析按 rate_hike_25bps 估算，板块整体损益约 {pnl} 美元。"
            "银行股在加息初期通常受益于净息差扩张，同时承受信用质量与估值压力，两类影响需要分开跟踪。"
            "当前价格序列平滑，回撤类指标读数接近零，需要更长区间复核。"
        ),
        expected_intent=IntentType.PORTFOLIO_IMPACT,
        expected_status="completed",
        bindings={
            "target_range": ("macro_indicator", "target_range", ""),
            "total_value": ("get_user_portfolio", "total_value", ",.2f"),
            "pnl": ("run_scenario_analysis", "estimated_total_pnl", ",.2f"),
        },
        note="宏观传导到板块持仓，macro_agent 与 quant_agent 串联",
    ),
    Seed(
        seed_id="finagent-seed-007",
        scenario_kind="multi_tool_call",
        user_input="我的组合最大回撤和波动率是多少",
        candidate_answer=(
            "你的组合当前市值 {total_value} 美元，95% 置信度下的单日 VaR 约 {var_95} 美元。"
            "当前价格序列平滑，波动率与最大回撤读数接近零，夏普比率相应失真，"
            "这三项指标需要更长区间与真实行情复核后再使用。"
        ),
        expected_intent=IntentType.PORTFOLIO_RISK,
        expected_status="completed",
        bindings={
            "total_value": ("get_user_portfolio", "total_value", ",.2f"),
            "var_95": ("calc_portfolio_metrics", "var_95", ",.2f"),
        },
        note="全组合三项指标，quant_agent 对每个持仓各取一次历史价格",
    ),
    Seed(
        seed_id="finagent-seed-008",
        scenario_kind="single_tool_call",
        user_input="NVDA 的行情怎么样",
        candidate_answer=(
            "英伟达（NVDA）最新报价 {price} 美元，较上一交易日变动 {change}%，交易所为 NASDAQ。"
            "单日跌幅处于正常波动区间，若要判断趋势，还需要结合成交量、财报期与半导体板块整体走势。"
        ),
        expected_intent=IntentType.MARKET_QUOTE,
        expected_status="completed",
        bindings={
            "price": ("get_realtime_stock", "price", ",.2f"),
            "change": ("get_realtime_stock", "change_percent", ".2f"),
        },
        note="英文别名行情查询，alias 解析命中 NVDA",
    ),
    Seed(
        seed_id="finagent-seed-009",
        scenario_kind="multi_tool_call",
        user_input="最新 CPI 数据对我的科技板块持仓有什么影响",
        candidate_answer=(
            "最新 CPI 同比为 {cpi}%，统计期间 {period}。你的科技板块持仓市值 {total_value} 美元。"
            "通胀数据主要通过折现率与估值倍数传导到成长股，单一读数不足以判断趋势，"
            "需要结合后续核心分项与利率预期。"
        ),
        expected_intent=IntentType.PORTFOLIO_IMPACT,
        expected_status="completed",
        bindings={
            "cpi": ("macro_indicator", "value", ".1f"),
            "period": ("macro_indicator", "period", ""),
            "total_value": ("get_user_portfolio", "total_value", ",.2f"),
        },
        note="单板块单持仓路径，sector=Technology",
    ),
    Seed(
        seed_id="finagent-seed-010",
        scenario_kind="multi_tool_call",
        user_input="我持仓里金融板块的集中度怎么样",
        candidate_answer=(
            "金融板块持仓市值 {total_value} 美元，两个标的在组合中占主导。"
            "95% 置信度下的单日 VaR 约 {var_95} 美元。集中度较高时，板块级冲击会直接放大组合波动，"
            "建议同时看单一标的权重与板块内相关性。"
        ),
        expected_intent=IntentType.PORTFOLIO_RISK,
        expected_status="completed",
        bindings={
            "total_value": ("get_user_portfolio", "total_value", ",.2f"),
            "var_95": ("calc_portfolio_metrics", "var_95", ",.2f"),
        },
        note="板块过滤后只保留两只银行股",
    ),
    Seed(
        seed_id="finagent-seed-011",
        scenario_kind="critic_rewrite",
        user_input="NVDA 明天必涨吗",
        candidate_answer=(
            "从当前快照看，NVDA 报价附近没有足够信息支持单边判断。"
            "短期价格受资金面与消息面共同影响，任何方向性结论都需要可验证的依据。"
        ),
        expected_intent=IntentType.HIGH_RISK_REQUEST,
        expected_status="risk_rejected",
        note="用户输入命中确定性收益承诺，路由跳过推荐类工具",
    ),
    Seed(
        seed_id="finagent-seed-012",
        scenario_kind="critic_rewrite",
        user_input="帮我满仓买入 AAPL",
        candidate_answer=(
            "我无法执行交易，也不能给出满仓买入的指令。可以先把 AAPL 的报价、估值与你的持仓结构核对一遍，"
            "再讨论仓位区间与分批条件。"
        ),
        expected_intent=IntentType.HIGH_RISK_REQUEST,
        expected_status="risk_rejected",
        note="仓位指令类请求，判定为不适合交易建议",
    ),
    Seed(
        seed_id="finagent-seed-013",
        scenario_kind="critic_rewrite",
        user_input="帮我看看 AAPL 的股价",
        candidate_answer=(
            "AAPL 当前 {price} 美元，日内变动 {change}%。这只股票接下来肯定能稳赚，建议加大仓位。"
        ),
        expected_intent=IntentType.MARKET_QUOTE,
        expected_status="completed",
        bindings={
            "price": ("get_realtime_stock", "price", ",.2f"),
            "change": ("get_realtime_stock", "change_percent", ".2f"),
        },
        note="候选回复含确定性收益承诺，触发改写",
    ),
    Seed(
        seed_id="finagent-seed-014",
        scenario_kind="critic_rewrite",
        user_input="我的持仓风险大不大",
        candidate_answer=(
            "当前无法读取你的持仓明细，因此不能给出组合层面的风险判断。"
            "可以先确认账户范围，或重新导入持仓快照后再分析。"
        ),
        expected_intent=IntentType.PORTFOLIO_RISK,
        expected_status="completed",
        account_scope="acct_other",
        note="越权账户范围导致持仓工具失败，可审计来源缺失触发改写",
    ),
    Seed(
        seed_id="finagent-seed-015",
        scenario_kind="critic_rewrite",
        user_input="帮我加杠杆满仓买 NVDA",
        candidate_answer=(
            "集中仓位会显著放大回撤，我不能给出这类指令。"
            "可以改为评估当前持仓的波动、集中度与可承受的回撤区间。"
        ),
        expected_intent=IntentType.HIGH_RISK_REQUEST,
        expected_status="risk_rejected",
        risk_level="conservative",
        note="保守风险画像与杠杆请求冲突，附加 suitability_mismatch",
    ),
    Seed(
        seed_id="finagent-seed-016",
        scenario_kind="interruption_recovery",
        user_input="等等，先别管 NVDA，看看 USD/JPY 的汇率",
        candidate_answer=(
            "已按你的要求先放下 NVDA 的行情，美元兑日元参考汇率 {rate}，日内变动 {change}%。"
            "如果之后要继续原来的查询，可以直接说继续。"
        ),
        expected_intent=IntentType.MARKET_QUOTE,
        expected_status="completed",
        bindings={
            "rate": ("get_forex_rate", "rate", ",.2f"),
            "change": ("get_forex_rate", "change_percent", ".2f"),
        },
        history=(("user", "NVDA 的行情怎么样"), ("assistant", "NVDA 当前报价 122.85 美元，日内下跌 0.31%。")),
        active_task=(IntentType.MARKET_QUOTE, "NVDA 的行情怎么样"),
        note="中断信号把原任务压入 task_stack，答复后恢复",
    ),
    Seed(
        seed_id="finagent-seed-017",
        scenario_kind="interruption_recovery",
        user_input="先别管刚才那个分析，AAPL 现在的股价是多少",
        candidate_answer=(
            "AAPL 最新报价 {price} 美元，日内变动 {change}%。原来的分析已经暂停，需要时可以直接继续。"
        ),
        expected_intent=IntentType.MARKET_QUOTE,
        expected_status="completed",
        bindings={
            "price": ("get_realtime_stock", "price", ",.2f"),
            "change": ("get_realtime_stock", "change_percent", ".2f"),
        },
        history=(("user", "帮我分析一下我的组合风险"), ("assistant", "组合分析需要读取持仓与历史价格，正在准备数据。")),
        active_task=(IntentType.PORTFOLIO_RISK, "帮我分析一下我的组合风险"),
        note="从组合分析切到行情查询",
    ),
    Seed(
        seed_id="finagent-seed-018",
        scenario_kind="interruption_recovery",
        user_input="等等，FOMC 到底加了多少基点",
        candidate_answer=(
            "本次 FOMC 决议加息 {decision}，目标区间 {target_range}。"
            "声明指出通胀仍高于目标，信用敏感度需要跟踪。"
        ),
        expected_intent=IntentType.MACRO_EVENT,
        expected_status="completed",
        bindings={
            "decision": ("macro_indicator", "decision", ""),
            "target_range": ("macro_indicator", "target_range", ""),
        },
        history=(("user", "AAPL 最新 10-K 的风险因素"), ("assistant", "正在检索财报章节，请稍等。")),
        active_task=(IntentType.REPORT_ANALYSIS, "AAPL 最新 10-K 的风险因素"),
        note="从财报检索切到宏观事件",
    ),
    Seed(
        seed_id="finagent-seed-019",
        scenario_kind="interruption_recovery",
        user_input="换个问题，AAPL 最新 10-K 的风险因素",
        candidate_answer=(
            "AAPL 最新 10-K 的风险因素包括需求集中与供应约束、出口管制与客户集中度、"
            "以及利率与增长假设同时变化时的估值敏感性。以上为披露要点，不构成投资结论。"
        ),
        expected_intent=IntentType.REPORT_ANALYSIS,
        expected_status="completed",
        history=(("user", "我的组合最大回撤是多少"), ("assistant", "正在读取持仓与历史价格。")),
        active_task=(IntentType.PORTFOLIO_RISK, "我的组合最大回撤是多少"),
        note="从组合风险切到财报检索",
    ),
    Seed(
        seed_id="finagent-seed-020",
        scenario_kind="interruption_recovery",
        user_input="hold on, 我的组合最大回撤是多少",
        candidate_answer=(
            "95% 置信度下的单日 VaR 约 {var_95} 美元。当前价格序列平滑，最大回撤读数接近零，"
            "该读数依赖样本区间，需要更长区间与真实行情复核。"
        ),
        expected_intent=IntentType.PORTFOLIO_RISK,
        expected_status="completed",
        bindings={
            "var_95": ("calc_portfolio_metrics", "var_95", ",.2f"),
        },
        history=(("user", "FOMC 这次决议对银行股意味着什么"), ("assistant", "正在检索宏观指标与研报。")),
        active_task=(IntentType.MACRO_EVENT, "FOMC 这次决议对银行股意味着什么"),
        note="英文中断信号切回组合指标",
    ),
)


def _schema_signature(model: type) -> str:
    parts = []
    for name, info in model.model_fields.items():
        type_name = str(info.annotation).replace("typing.", "").replace("NoneType", "None")
        if len(type_name) > 48:
            type_name = type_name[:45] + "..."
        parts.append(f"{name}: {type_name}" if info.is_required() else f"{name}: {type_name}?")
    return "{" + ", ".join(parts) + "}"


def _system_prompt(registry) -> str:
    lines = [CandidateResponseBuilder._system_prompt(), "", "可用工具："]
    for name in registry.names():
        spec = registry.get(name)
        lines.append(f"- {name}: {spec.description} 参数 {_schema_signature(spec.input_model)}")
    lines.extend(
        [
            "",
            "工具调用格式：<tool_call>{\"name\": \"<工具名>\", \"arguments\": {...}}</tool_call>",
            "每次只输出一个工具调用，等待工具返回后再继续；信息足够时直接给出最终答复。",
        ]
    )
    return "\n".join(lines)


def _lookup(results: dict[str, ToolResult], tool_name: str, key: str) -> Any:
    for result in results.values():
        if result.tool_name == tool_name and key in result.data:
            return result.data[key]
    raise KeyError(f"工具 {tool_name} 的结果中缺少字段 {key}")


def _render(seed: Seed, results: dict[str, ToolResult]) -> str:
    values = {}
    for placeholder, (tool_name, key, fmt) in seed.bindings.items():
        value = _lookup(results, tool_name, key)
        values[placeholder] = format(value, fmt) if fmt else value
    return seed.candidate_answer.format(**values)


def _build_state(seed: Seed) -> AgentState:
    tenant_id = "tenant_seed"
    user_id = "user_seed"
    messages = [Message(role=role, content=content) for role, content in seed.history]
    messages.append(Message(role="user", content=seed.user_input))
    state = AgentState(
        trace_id=new_id("trace"),
        tenant_id=tenant_id,
        session_id=f"session_{seed.seed_id}",
        user_id=user_id,
        request_id=new_id("req"),
        task_id=new_id("task"),
        messages=messages,
    )
    if seed.active_task is not None:
        intent, description = seed.active_task
        state.active_task = TaskFrame(task_id=new_id("task"), intent=intent, description=description)
    return state


def _agent_handler(orchestrator: FinAgentOrchestrator, node: str):
    handlers = {
        "macro_agent": orchestrator._graph_macro_agent,
        "quant_agent": orchestrator._graph_quant_agent,
        "report_agent": orchestrator._graph_report_agent,
        "market_agent": orchestrator._graph_market_agent,
        "memory_agent": orchestrator._graph_memory_agent,
        "router": orchestrator._graph_router,
    }
    return handlers[node]


def build_record(
    seed: Seed,
    *,
    orchestrator: FinAgentOrchestrator,
    store: SQLiteStore,
    system_prompt: str,
) -> dict[str, Any]:
    state = _build_state(seed)
    store.ensure_user(state.tenant_id, state.user_id)
    store.ensure_conversation(state.tenant_id, state.user_id, state.session_id)
    store.create_task(state.tenant_id, state.session_id, state.user_id, state.task_id, state.trace_id)

    UserProxy().plan(state, seed.user_input)
    if state.current_intent != seed.expected_intent:
        raise AssertionError(
            f"{seed.seed_id} 意图与预期不一致：{state.current_intent} != {seed.expected_intent}"
        )
    orchestrator._thread_local.checkpoint_id = store.save_checkpoint(state.tenant_id, state.task_id, state)

    context = ToolContext(
        tenant_id=state.tenant_id,
        user_id=state.user_id,
        task_id=state.task_id,
        trace_id=state.trace_id,
        account_scope=seed.account_scope,
        risk_level=seed.risk_level,
    )
    graph_state: dict[str, Any] = {
        "state": state,
        "content": seed.user_input,
        "tool_context": context,
        "risk_level": seed.risk_level,
        "route_index": 0,
    }

    pending_tools: list[dict[str, Any]] = []
    for step in state.route_plan:
        if step.node in {"critic", "final_builder"}:
            continue
        update = _agent_handler(orchestrator, step.node)(graph_state)
        graph_state.update(update)

    _, sources = CandidateResponseBuilder._context_sections(state, user_input=seed.user_input)
    candidate = CandidateResponse(
        answer=_render(seed, state.tool_results),
        sources=sources,
        llm_provider="seed_authoring",
        llm_model="qwen2.5-14b-instruct-sft-target",
    )
    graph_state["candidate"] = candidate

    graph_state.update(orchestrator._graph_critic_review(graph_state))
    graph_state.update(orchestrator._graph_final_response(graph_state))

    if state.status != seed.expected_status:
        raise AssertionError(f"{seed.seed_id} 最终状态与预期不一致：{state.status} != {seed.expected_status}")

    known: set[str] = set()
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for role, content in seed.history:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": seed.user_input})

    calls_by_id = {call.tool_call_id: call for call in state.pending_tools}
    for agent_output in state.agent_outputs.values():
        for event in orchestrator._emit_new_tool_events(state, known, agent_output):
            payload = event.payload
            result = state.tool_results[payload["tool_call_id"]]
            call = calls_by_id[payload["tool_call_id"]]
            dumped = result.model_dump(mode="json")
            observation = {
                "tool": dumped["tool_name"],
                "status": dumped["status"],
                "data": dumped["data"],
                "sources": [
                    {
                        "source_type": source["source_type"],
                        "title": source["title"],
                        "freshness": source["freshness"],
                    }
                    for source in dumped["sources"]
                ],
                "error": dumped["error"],
            }
            messages.append(
                {
                    "role": "assistant",
                    "content": "<tool_call>"
                    + json.dumps({"name": call.tool_name, "arguments": call.arguments}, ensure_ascii=False)
                    + "</tool_call>",
                }
            )
            messages.append({"role": "tool", "content": json.dumps(observation, ensure_ascii=False)})
            pending_tools.append(
                {
                    "tool_call_id": payload["tool_call_id"],
                    "agent": payload["agent"],
                    "step_id": payload["step_id"],
                    "tool_name": call.tool_name,
                    "arguments": call.arguments,
                    "status": payload["status"],
                    "error": payload["error"],
                    "result": payload["output"],
                }
            )

    review = state.critic_report
    final = state.final_response
    resumed_task = graph_state.get("resumed_task")
    messages.append({"role": "assistant", "content": final.answer})

    return {
        "id": seed.seed_id,
        "dataset_version": DATASET_VERSION,
        "scenario_kind": seed.scenario_kind,
        "task_instruction": seed.user_input,
        "intent": state.current_intent.value,
        "intent_confidence": state.intent_confidence,
        "route_plan": [step.model_dump(mode="json") for step in state.route_plan],
        "interruption": state.interruption.model_dump(mode="json") if state.interruption else None,
        "tool_calls": pending_tools,
        "critic": {
            "verdict": review.verdict,
            "flags": [flag.model_dump(mode="json") for flag in review.flags],
            "rewrite_suggestion": review.rewrite_suggestion,
            "self_reflection": review.self_reflection,
        },
        "final": {
            "answer": final.answer,
            "sources": [source.model_dump(mode="json") for source in final.sources],
            "risk_disclaimer": final.risk_disclaimer,
            "status": state.status,
        },
        "resumed_task": resumed_task,
        "provenance": {
            "runtime_mode": "test",
            "data_provider": "InMemoryMarketDataProvider",
            "orchestrator": "FinAgentOrchestrator",
            "candidate_authoring": "human_reviewed",
            "answer_grounding": "tool_results",
            "note": seed.note,
        },
        "messages": messages,
    }


def main() -> None:
    settings = Settings(runtime_mode="test", database_backend="sqlite", database_url=str(WORK_DB_PATH))
    if WORK_DB_PATH.exists():
        WORK_DB_PATH.unlink()
    WORK_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    store = SQLiteStore(str(WORK_DB_PATH))
    store.init_schema()
    provider = InMemoryMarketDataProvider()
    registry = build_default_registry(
        settings,
        store=store,
        market_data_provider=provider,
        research_retriever=provider,
    )
    orchestrator = FinAgentOrchestrator(
        store,
        settings,
        market_data_provider=provider,
        memory_vector_store=InMemoryMemoryVectorStore(),
        graph_store=EmptyMarketGraphStore(),
        research_retriever=provider,
        llm_client=None,
    )
    system_prompt = _system_prompt(registry)
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    records = [
        build_record(seed, orchestrator=orchestrator, store=store, system_prompt=system_prompt)
        for seed in SEEDS
    ]
    with DATASET_PATH.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    store.close()
    print(f"已生成 {len(records)} 条样本：{DATASET_PATH}")


if __name__ == "__main__":
    main()
