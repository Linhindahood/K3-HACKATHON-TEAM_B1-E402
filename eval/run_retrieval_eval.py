"""Retrieval-only evaluation against eval/golden_set.jsonl.

Chạy: python eval/run_retrieval_eval.py   (từ bất kỳ đâu, path tự resolve)

Đo: Recall@1/3/5, MRR@10, duplicate rate trong top-k, và một chỉ số riêng
"dense-gate blind spot rate" — đo đúng hiện tượng "câu hỏi có căn cứ trong
tài liệu (retrieval tìm đúng top-1) nhưng evidence_gate vẫn từ chối vì gate
chỉ nhìn dense_score của passage top-1, không nhìn điểm đã fusion".

Không gọi LLM — chạy hoàn toàn local/miễn phí (FAISS + BM25S + E5 ONNX).
"""
from __future__ import annotations

import json
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

from backend.rag import retriever  # noqa: E402
from backend.rag.evidence_gate import has_sufficient_evidence  # noqa: E402

TOP_K_EVAL = 10


def load_golden_set() -> list[dict]:
    with GOLDEN_SET_PATH.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def evaluate_case(case: dict) -> dict:
    question = case["question"]
    start = time.perf_counter()
    passages = retriever.retrieve(question, top_k=TOP_K_EVAL) if question.strip() else []
    latency_ms = (time.perf_counter() - start) * 1000.0

    retrieved_ids = [p.get("chunk_id") for p in passages]
    expected = set(case.get("expected_chunk_ids") or [])

    hit_rank = None
    for index, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in expected:
            hit_rank = index
            break

    gate_pass = has_sufficient_evidence(passages) if passages else False
    top1_dense_score = passages[0].get("dense_score") if passages else None

    return {
        "id": case["id"],
        "category": case.get("category"),
        "answerable": case.get("answerable"),
        "has_expected": bool(expected),
        "hit_rank": hit_rank,
        "recall_1": hit_rank == 1,
        "recall_3": hit_rank is not None and hit_rank <= 3,
        "recall_5": hit_rank is not None and hit_rank <= 5,
        "reciprocal_rank": (1.0 / hit_rank) if hit_rank else 0.0,
        "duplicate_in_topk": len(retrieved_ids) != len(set(retrieved_ids)),
        "gate_pass": gate_pass,
        "dense_gate_blind_spot": hit_rank == 1 and not gate_pass,
        "top1_dense_score": top1_dense_score,
        "retrieved_ids": retrieved_ids,
        "latency_ms": round(latency_ms, 2),
    }


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round(pct / 100 * (len(ordered) - 1))))
    return ordered[index]


def summarize(results: list[dict]) -> dict:
    scored = [r for r in results if r["has_expected"]]
    latencies = [r["latency_ms"] for r in results]

    def rate(key: str, rows: list[dict]) -> float:
        return round(100 * sum(1 for r in rows if r[key]) / len(rows), 1) if rows else 0.0

    return {
        "total_cases": len(results),
        "scored_cases": len(scored),
        "recall_at_1_pct": rate("recall_1", scored),
        "recall_at_3_pct": rate("recall_3", scored),
        "recall_at_5_pct": rate("recall_5", scored),
        "mrr_at_10": round(statistics.mean(r["reciprocal_rank"] for r in scored), 4) if scored else 0.0,
        "duplicate_rate_pct": rate("duplicate_in_topk", results),
        "dense_gate_blind_spot_rate_pct": rate("dense_gate_blind_spot", scored),
        "dense_gate_blind_spot_cases": [r["id"] for r in scored if r["dense_gate_blind_spot"]],
        "latency_p50_ms": round(percentile(latencies, 50), 2),
        "latency_p95_ms": round(percentile(latencies, 95), 2),
    }


def print_report(results: list[dict], summary: dict) -> None:
    print("\n=== Retrieval eval — theo category ===")
    categories = sorted({r["category"] for r in results})
    for category in categories:
        rows = [r for r in results if r["category"] == category and r["has_expected"]]
        if not rows:
            continue
        r1 = sum(1 for r in rows if r["recall_1"])
        print(f"  {category:<24} Recall@1 {r1}/{len(rows)}")

    print("\n=== Case bị dense-gate blind spot (retrieval đúng top-1, gate vẫn từ chối) ===")
    if summary["dense_gate_blind_spot_cases"]:
        for case_id in summary["dense_gate_blind_spot_cases"]:
            row = next(r for r in results if r["id"] == case_id)
            print(f"  {case_id}: top1_dense_score={row['top1_dense_score']:.4f} (ngưỡng 0.82)")
    else:
        print("  (không có)")

    print("\n=== Tổng hợp ===")
    print(f"  Recall@1  : {summary['recall_at_1_pct']}%")
    print(f"  Recall@3  : {summary['recall_at_3_pct']}%  (quality bar ARCHITECTURE.md §7.4: ≥90%)")
    print(f"  Recall@5  : {summary['recall_at_5_pct']}%")
    print(f"  MRR@10    : {summary['mrr_at_10']}  (quality bar: ≥0.85)")
    print(f"  Duplicate : {summary['duplicate_rate_pct']}%  (quality bar: 0%)")
    print(f"  Dense-gate blind spot rate: {summary['dense_gate_blind_spot_rate_pct']}%  (metric mới, chưa có bar — đề xuất 0%)")
    print(f"  Latency p50/p95: {summary['latency_p50_ms']}ms / {summary['latency_p95_ms']}ms")


def main() -> None:
    print("Warm-up retriever (load model + FAISS + BM25S)...")
    warm_start = time.perf_counter()
    retriever.warm_up()
    print(f"  xong sau {time.perf_counter() - warm_start:.2f}s")

    cases = load_golden_set()
    results = [evaluate_case(case) for case in cases]
    summary = summarize(results)
    print_report(results, summary)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"retrieval_{timestamp}.json"
    output_path.write_text(
        json.dumps({"summary": summary, "cases": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nĐã ghi kết quả vào {output_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
