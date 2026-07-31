# Deterministic Map Renderer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trả hướng dẫn text và ảnh PNG có tuyến đường deterministic từ cùng một verified route plan.

**Architecture:** Alias resolver và Dijkstra chạy local trên graph JSON đã kiểm tra. RoutePlan được dùng đồng thời bởi text-only LLM và Pillow renderer; ảnh được cache theo hash tuyến đường.

**Tech Stack:** Python 3.11, stdlib `json`, `heapq`, `hashlib`, Pillow 12.x, pytest.

**Execution status:** Hoàn thành ngày `2026-07-31`; verification cuối
`115 passed`. Chưa commit theo yêu cầu kiểm soát thay đổi của người dùng.

## Global Constraints

- Chỉ sửa role RAG và tests liên quan.
- Không sửa `bot/`, frontend hoặc raw source files.
- Không thêm Vision LLM call cho renderer.
- Giữ nguyên keys `answer`, `sources`, `has_evidence`, `intent`, `media`.
- Mọi production behavior phải có failing test trước.
- Không commit cho tới khi người dùng yêu cầu; change history dùng format task-time.

---

### Task 1: Verified route graph and shortest-path planner

**Files:**
- Create: `backend/rag/campus_route_graph.json`
- Create: `backend/rag/route_graph.py`
- Create: `backend/tests/test_route_graph.py`

**Interfaces:**
- Produces: `RoutePlan`, `UnknownLandmarkError`, `RouteNotFoundError`,
  `load_route_graph()`, `plan_route(origin: str, destination: str) -> RoutePlan`.

- [ ] Viết test fail cho alias `tòa E`, `toa e`, `cổng đại lễ`.
- [ ] Viết test fail cho tuyến `Tòa E -> Tòa A`, yêu cầu origin/destination đúng,
  có ít nhất hai points và steps.
- [ ] Viết test fail cho landmark không tồn tại; phải raise
  `UnknownLandmarkError`, không fallback sang landmark gần giống.
- [ ] Viết test fail cho validator: node ngoài bounds, edge tham chiếu node sai
  và graph landmark bị cô lập.
- [ ] Chạy `pytest backend/tests/test_route_graph.py -q`; expected RED do module
  chưa tồn tại.
- [ ] Tạo graph JSON cho các landmark có nhãn rõ: Cổng Đại Lễ, Cổng San Hô,
  Tòa A, B, C, E, F, G, H, I, J, K, L, bãi gửi xe, sân vận động.
- [ ] Implement dataclasses, cached graph loader, normalized alias lookup,
  polyline cost và Dijkstra bằng `heapq`.
- [ ] Chạy test file; expected GREEN.

### Task 2: Deterministic Pillow renderer and cache

**Files:**
- Create: `backend/rag/map_renderer.py`
- Create: `backend/tests/test_map_renderer.py`
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: `RoutePlan`.
- Produces:
  `render_route_map(plan: RoutePlan, map_path: Path | None = None,
  output_dir: Path | None = None) -> Path`.

- [ ] Viết test fail dùng map fixture trắng `200 x 200`, route có ba points.
- [ ] Assert output là PNG, khác ảnh gốc, pixel trên route có màu line, marker
  đầu và cuối khác nhau.
- [ ] Viết test fail gọi cùng route hai lần; đường dẫn cache phải giống nhau và
  mtime không đổi.
- [ ] Chạy `pytest backend/tests/test_map_renderer.py -q`; expected RED.
- [ ] Ghi `Pillow>=12.0,<13.0` thành dependency trực tiếp.
- [ ] Implement render với white outline, blue route, green/red markers và
  atomic cache file dưới `raw/_generated/`.
- [ ] Chạy test file; expected GREEN.

### Task 3: Grounded direction text from RoutePlan

**Files:**
- Modify: `backend/rag/prompt.py`
- Modify: `backend/rag/multimodal.py`
- Modify: `backend/tests/test_multimodal.py`

**Interfaces:**
- Consumes: `RoutePlan`, `render_route_map`.
- Produces: response dict giữ API contract hiện tại.

- [ ] Viết test fail: prompt chứa origin, destination và toàn bộ verified
  steps; không yêu cầu model đọc ảnh.
- [ ] Viết test fail: output `media.local_path` bắt đầu bằng `_generated/` và
  file tồn tại.
- [ ] Viết test fail: LLM provider lỗi vẫn trả deterministic steps,
  `has_evidence=true` và rendered media.
- [ ] Viết test fail: unknown landmark trả clarify response,
  `has_evidence=false` và original map media.
- [ ] Chạy `pytest backend/tests/test_multimodal.py -q`; expected RED.
- [ ] Thay vision prompt bằng route-plan prompt; gọi `generate_text`, không gọi
  `generate_vision_text`.
- [ ] Điều phối planner, renderer, text generation và fallback.
- [ ] Chạy test file; expected GREEN.

### Task 4: Pipeline integration and regression

**Files:**
- Modify: `backend/rag/pipeline.py`
- Modify: `backend/tests/test_pipeline.py`
- Modify: `backend/tests/test_directions.py`

**Interfaces:**
- Pipeline tiếp tục gọi một public coordinator cho location branch và trả cùng
  response schema.

- [ ] Viết test fail cho location request `Tòa E -> Tòa A`: không gọi text
  retriever, trả answer và generated media.
- [ ] Viết regression test origin từ câu gốc vẫn thắng query rewrite.
- [ ] Implement thay đổi chữ ký coordinator tối thiểu nếu Task 3 yêu cầu.
- [ ] Chạy các test direction, pipeline, multimodal, planner và renderer.
- [ ] Chạy toàn bộ `pytest backend/tests -q`.

### Task 5: Visual QA, benchmark and change history

**Files:**
- Create: `backend/rag/change_history/deterministic-map-renderer_<time>.md`

- [ ] Render các tuyến Cổng Đại Lễ -> Tòa A, Tòa E -> Tòa A,
  Cổng San Hô -> Tòa J và mở ảnh để kiểm tra line không xuyên building.
- [ ] Chỉnh duy nhất graph coordinates/edge polyline nếu visual QA phát hiện
  tuyến sai; chạy lại graph và renderer tests.
- [ ] Benchmark planner + cached renderer độc lập; mục tiêu local p95 dưới
  `50 ms` sau warm-up trên máy hiện tại.
- [ ] Smoke test location branch bằng API key thật một lần.
- [ ] Ghi thời gian, branch, commit trạng thái, logic cũ/mới, test evidence và
  hướng rollback trong change history.
- [ ] Chạy `git diff --check` trên các file của task.
