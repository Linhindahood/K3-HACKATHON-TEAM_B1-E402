"""End-to-end answer evaluation against eval/golden_set.jsonl.

Chạy: python eval/run_answer_eval.py

Gọi PIPELINE THẬT (retrieve + generate, kể cả lời gọi LLM thật theo LLM_PROVIDER
trong .env) cho từng case — đáp ứng rubric R5 "≥1 lời gọi AI thật ở quyết định
trung tâm". Tốn API quota thật của provider đang cấu hình; chạy 1 lượt hết
golden set là đủ cho yêu cầu R4 "bảng kết quả chạy trọn bộ ≥1 lượt".

Đo: answerability precision/recall, false-accept rate, citation source accuracy
(đúng trọng tâm được xấp xỉ tự động bằng so khớp chunk_id — xem giới hạn ở
docstring cuối file), scope-safety (không tự nhận đã đặt lịch / không link thật
cho case bị đánh dấu special_check), và latency p50/p95.
"""
from __future__ import annotations

import json
import re
import statistics
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CODEBASE_DIR = REPO_ROOT / "codebase"
EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_SET_PATH = EVAL_DIR / "golden_set.jsonl"
RESULTS_DIR = EVAL_DIR / "results"

sys.path.insert(0, str(CODEBASE_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(CODEBASE_DIR / ".env")

from backend import config  # noqa: E402
from backend.rag.pipeline import answer_question, warm_up  # noqa: E402

SELF_ACTION_PHRASES = [
    "đã đặt",
    "đã book",
    "đặt thành công",
    "đã giữ phòng",
    "đã hoàn tất đặt",
    "đã đăng ký giúp",
    "đã xác nhận đặt",
    "mình đã book",
]
_URL_RE = re.compile(r"https?://")


def load_golden_set() -> list[dict]:
    with GOLDEN_SET_PATH.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def check_scope_safety(answer: str, special_check: str | None) -> bool | None:
    if not special_check:
        return None
    lowered = answer.casefold()
    no_self_action = not any(phrase in lowered for phrase in SELF_ACTION_PHRASES)
    if special_check == "no_self_action":
        return no_self_action
    if special_check == "no_self_action_no_real_url":
        return no_self_action and not _URL_RE.search(answer)
    return None


def check_citation_accuracy(sources: list[str], expected_chunk_ids: list[str]) -> bool | None:
    if not expected_chunk_ids:
        return None
    expected = set(expected_chunk_ids)
    cited_chunk_ids = {source.split("#", 1)[-1] for source in sources}
    return bool(cited_chunk_ids & expected)


def evaluate_case(case: dict) -> dict:
    question = case["question"]
    start = time.perf_counter()
    try:
        result = answer_question(question) if question.strip() else {
            "answer": "",
            "sources": [],
            "has_evidence": False,
        }
        error = None
    except Exception as exc:  # noqa: BLE001 — record and continue, don't abort the run
        result = {"answer": "", "sources": [], "has_evidence": False}
        error = f"{type(exc).__name__}: {exc}"
    latency_ms = (time.perf_counter() - start) * 1000.0

    golden_answerable = bool(case.get("answerable"))
    has_evidence = bool(result.get("has_evidence"))

    return {
        "id": case["id"],
        "category": case.get("category"),
        "golden_answerable": golden_answerable,
        "has_evidence": has_evidence,
        "confusion": (
            "TP" if golden_answerable and has_evidence else
            "FN" if golden_answerable and not has_evidence else
            "FP" if not golden_answerable and has_evidence else
            "TN"
        ),
        "citation_ok": check_citation_accuracy(result.get("sources", []), case.get("expected_chunk_ids") or []),
        "scope_safety_ok": check_scope_safety(result.get("answer", ""), case.get("special_check")),
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "latency_ms": round(latency_ms, 2),
        "error": error,
    }


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round(pct / 100 * (len(ordered) - 1))))
    return ordered[index]


def summarize(results: list[dict]) -> dict:
    tp = sum(1 for r in results if r["confusion"] == "TP")
    fn = sum(1 for r in results if r["confusion"] == "FN")
    fp = sum(1 for r in results if r["confusion"] == "FP")
    tn = sum(1 for r in results if r["confusion"] == "TN")
    citation_checked = [r for r in results if r["citation_ok"] is not None]
    scope_checked = [r for r in results if r["scope_safety_ok"] is not None]
    latencies = [r["latency_ms"] for r in results]
    errors = [r for r in results if r["error"]]

    return {
        "total_cases": len(results),
        "confusion_matrix": {"TP": tp, "FN": fn, "FP": fp, "TN": tn},
        "answerability_precision_pct": round(100 * tp / (tp + fp), 1) if (tp + fp) else None,
        "answerability_recall_pct": round(100 * tp / (tp + fn), 1) if (tp + fn) else None,
        "false_accept_rate_pct": round(100 * fp / (fp + tn), 1) if (fp + tn) else None,
        "citation_accuracy_pct": (
            round(100 * sum(1 for r in citation_checked if r["citation_ok"]) / len(citation_checked), 1)
            if citation_checked else None
        ),
        "citation_checked_n": len(citation_checked),
        "scope_safety_pass_pct": (
            round(100 * sum(1 for r in scope_checked if r["scope_safety_ok"]) / len(scope_checked), 1)
            if scope_checked else None
        ),
        "scope_safety_failed_cases": [r["id"] for r in scope_checked if not r["scope_safety_ok"]],
        "latency_p50_ms": round(percentile(latencies, 50), 2),
        "latency_p95_ms": round(percentile(latencies, 95), 2),
        "runtime_errors": [{"id": r["id"], "error": r["error"]} for r in errors],
        "llm_provider": config.LLM_PROVIDER,
        "llm_model": config.LLM_MODEL,
    }


def print_report(summary: dict) -> None:
    cm = summary["confusion_matrix"]
    print("\n=== Answerability (has_evidence vs golden answerable) ===")
    print(f"  TP={cm['TP']}  FN={cm['FN']}  FP={cm['FP']}  TN={cm['TN']}")
    print(f"  Precision: {summary['answerability_precision_pct']}%")
    print(f"  Recall   : {summary['answerability_recall_pct']}%")
    print(f"  False-accept rate: {summary['false_accept_rate_pct']}%  (quality bar ARCHITECTURE.md §7.4: ≤5%)")

    print("\n=== Citation source accuracy (đúng trọng tâm ~ đúng nguồn, tự động hoá) ===")
    print(f"  {summary['citation_accuracy_pct']}%  trên {summary['citation_checked_n']} case có expected_chunk_ids")
    print("  (quality bar ARCHITECTURE.md §7.4: 100% — giới hạn: chỉ bắt lỗi sai nguồn, không bắt lỗi lạc đề dùng đúng nguồn)")

    print("\n=== Scope-safety (không tự nhận đã đặt lịch / không link thật) ===")
    print(f"  Pass rate: {summary['scope_safety_pass_pct']}%")
    if summary["scope_safety_failed_cases"]:
        print(f"  FAIL: {summary['scope_safety_failed_cases']}")

    print(f"\n=== Latency (LLM_PROVIDER={summary['llm_provider']}, LLM_MODEL={summary['llm_model']}) ===")
    print(f"  p50/p95: {summary['latency_p50_ms']}ms / {summary['latency_p95_ms']}ms  (quality bar: p95 ≤ 3000ms)")

    if summary["runtime_errors"]:
        print("\n=== Lỗi runtime (không phải fail metric, cần fix trước khi tin kết quả) ===")
        for item in summary["runtime_errors"]:
            print(f"  {item['id']}: {item['error']}")


def main() -> None:
    print("Warm-up pipeline (load model + FAISS + BM25S)...")
    warm_up()

    cases = load_golden_set()
    print(f"Chạy {len(cases)} case qua pipeline thật (LLM_PROVIDER={config.LLM_PROVIDER})...")
    results = [evaluate_case(case) for case in cases]
    summary = summarize(results)
    print_report(summary)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"answer_{timestamp}.json"
    output_path.write_text(
        json.dumps({"summary": summary, "cases": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nĐã ghi kết quả vào {output_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
