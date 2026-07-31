# Deterministic map renderer

- Thời gian: `2026-07-31 11:47:44` (Asia/Saigon)
- Branch: `minh/deterministic-map-renderer`
- Commit: chưa commit
- Role: RAG

## Mục tiêu

Nhánh chỉ đường trả hai output dùng chung một verified route plan:

1. Text hướng dẫn do LLM diễn đạt.
2. Ảnh PNG được Pillow hậu xử lý, vẽ line và marker lên bản đồ gốc.

Renderer không gọi LLM và không cho model sinh tọa độ.

## Logic cũ

- Vision LLM nhận toàn bộ ảnh base64 và tự suy luận tuyến.
- Output text và ảnh gốc không có line chỉ đường.
- Không có graph, shortest-path hoặc validation tọa độ.
- Khi model suy luận sai, không có contract deterministic để kiểm tra.

## Logic mới

- `campus_route_graph.json` lưu landmark, junction, alias và verified edge
  polyline trên ảnh `1254 x 1254`.
- `route_graph.py` validate bounds, alias, edge reference và connectivity; sau
  đó dùng Dijkstra bằng `heapq`.
- Unknown landmark fail closed. “Bể bơi” không bị suy diễn thành Tòa K vì bản
  đồ không ghi rõ nhãn đó.
- Cả text và renderer nhận cùng một immutable `RoutePlan`.
- `map_renderer.py` vẽ white outline, blue route, marker xanh `S`, marker đỏ
  `D`; cache theo hash route và map/renderer version.
- Direction LLM chỉ nhận verified steps dạng text; không nhận ảnh base64 và
  không được thêm địa điểm.
- Nếu LLM lỗi, verified steps được ghép thành text deterministic.
- Nếu renderer lỗi, hệ thống vẫn trả text và bản đồ gốc.
- Generated media có đường dẫn `_generated/route-<hash>.png`, tương thích bot
  hiện tại mà không sửa `bot/`.

## Tối ưu tốc độ

- Bỏ `PNG optimize=True`, vì bước nén lại ảnh làm cold render tăng lên gần
  hai giây.
- Benchmark trên máy hiện tại, 500 iterations:
  - Cached planner + renderer p50: `0.18 ms`.
  - Cached planner + renderer p95: `0.27 ms`.
  - Cold render: `229.90 ms`.
- Smoke test end-to-end dùng hai LLM calls: `9,182 ms`; local rendering không
  còn là bottleneck.

## Kiểm chứng

- Planner tests: alias, Dijkstra, bounds, disconnected graph, reverse edge
  instruction và noisy destination.
- Renderer tests: pixel route/markers, cache mtime và cold-render budget.
- Multimodal tests: grounded prompt, generated media, provider fallback và
  unknown landmark fallback.
- Pipeline regression: location branch không gọi text retriever.
- Visual QA:
  - Cổng Đại Lễ -> Tòa A.
  - Tòa E -> Tòa A.
  - Cổng San Hô -> Tòa J.
- Các line đã kiểm tra không xuyên khối tòa nhà trên sơ đồ.
- Verification cuối: `115 passed in 19.20s`.
- Smoke test thật:
  - Query: `Tôi xuất phát tại tòa E, hãy chỉ đường tới thư viện`.
  - Result: `intent=factual`, `has_evidence=true`.
  - Media: `_generated/route-12f6b881941814e1.png`.

## File của task

Tạo mới:

- `backend/rag/campus_route_graph.json`
- `backend/rag/route_graph.py`
- `backend/rag/map_renderer.py`
- `backend/tests/test_route_graph.py`
- `backend/tests/test_map_renderer.py`
- `backend/rag/DETERMINISTIC_MAP_RENDERER_DESIGN.md`
- `backend/rag/DETERMINISTIC_MAP_RENDERER_IMPLEMENTATION_PLAN.md`

Thay đổi:

- `backend/rag/multimodal.py`
- `backend/rag/prompt.py`
- `backend/tests/test_multimodal.py`
- `backend/tests/test_prompt.py`
- `backend/tests/test_pipeline.py`
- `requirements.txt`

Runtime, không commit:

- `backend/knowledge_base/raw/_generated/route-*.png`

## Rollback chính xác

1. Xóa các file tạo mới của task ở trên.
2. Revert riêng diff của task trong `multimodal.py`, `prompt.py`, ba test file
   tích hợp và `requirements.txt`.
3. Không revert `directions.py`, `router.py`, `source_registry.py`, `.gitignore`
   hoặc `bot/`; các file đó có thay đổi từ task/người khác.
4. Có thể xóa cache runtime `_generated/` mà không ảnh hưởng raw source.
5. Chạy lại `pytest backend/tests -q`.

