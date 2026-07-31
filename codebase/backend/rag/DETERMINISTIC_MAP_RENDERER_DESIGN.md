# Deterministic Campus Map Renderer

## Mục tiêu

Nhánh chỉ đường trả đồng thời:

1. Hướng dẫn tiếng Việt do LLM diễn đạt.
2. Ảnh bản đồ tĩnh có line chỉ đường được hậu xử lý bằng Pillow.

Hai output phải dùng chung một route plan. LLM không được sinh pixel, tọa độ,
edge hoặc tự chọn một tuyến khác.

## Kiến trúc

```text
question
  -> router
  -> parse origin/destination
  -> resolve aliases against verified graph
  -> Dijkstra shortest path
  -> RoutePlan
       -> text-only LLM -> answer
       -> Pillow renderer -> cached PNG
  -> answer + media
```

Một request chỉ đường có hai LLM calls tổng cộng: router hiện tại và text
generator. Renderer hoàn toàn deterministic.

## Route graph

Graph được lưu tại `backend/rag/campus_route_graph.json`, tách khỏi code để
tọa độ và tuyến có thể review.

- Landmark node: cổng, tòa nhà hoặc địa điểm có nhãn trên bản đồ.
- Junction node: điểm giao trên lối đi.
- Mỗi node có tọa độ pixel trên ảnh gốc `1254 x 1254`.
- Mỗi edge chứa polyline đã kiểm tra trên bản đồ và hướng dẫn ngắn.
- Cost được tính từ tổng độ dài các đoạn polyline.
- Alias chỉ map tới landmark có thật trên bản đồ. Không suy diễn “bể bơi” thành
  “Tòa K” vì ảnh không ghi rõ bể bơi.

## Contract nội bộ

```python
@dataclass(frozen=True)
class RoutePlan:
    origin_id: str
    origin_label: str
    destination_id: str
    destination_label: str
    node_ids: tuple[str, ...]
    points: tuple[tuple[int, int], ...]
    steps: tuple[str, ...]
```

`plan_route(origin, destination)` trả `RoutePlan`. Nếu không resolve được một
địa điểm hoặc graph không có đường, hàm raise lỗi domain rõ ràng; coordinator
trả lời yêu cầu người dùng làm rõ và không render line giả.

## Renderer

Pillow mở bản đồ gốc, vẽ:

- line màu xanh, viền trắng để nổi trên nền;
- marker xanh lá tại điểm xuất phát;
- marker đỏ tại điểm đến;
- nhãn `Bắt đầu` và `Điểm đến`.

Tên file là hash của `map version + node_ids`, ví dụ
`_generated/route-43b2c8c17a.png`. Nếu file đã tồn tại thì dùng lại, không
render lại.

## LLM grounding

Direction prompt chỉ nhận `RoutePlan` gồm tên điểm, danh sách bước và landmark.
Prompt cấm thêm địa điểm hoặc thao tác không có trong plan. Không cần gửi ảnh
base64 sang Vision API, giảm payload và latency.

Nếu provider lỗi, hệ thống ghép các `steps` deterministic thành hướng dẫn thay
vì quay về câu fallback chung.

## Output

Giữ nguyên API contract:

```json
{
  "answer": "Từ Tòa E, bạn...",
  "sources": ["1_map.png#route-graph-v1"],
  "has_evidence": true,
  "intent": "factual",
  "media": [
    {
      "asset_id": "route-...",
      "title": "Đường đi từ Tòa E tới Tòa A",
      "local_path": "_generated/route-....png",
      "url": "https://vinuni.edu.vn/vi/visit-2/",
      "alt_text": "Tuyến đường từ Tòa E tới Tòa A"
    }
  ]
}
```

## Failure policy

- Không rõ origin/destination: hỏi lại, đính kèm bản đồ gốc.
- Không có path: nói chưa xác định được tuyến, đính kèm bản đồ gốc.
- Renderer lỗi: trả text route và bản đồ gốc.
- LLM lỗi: trả text deterministic và ảnh route.
- Map gốc thiếu: không tạo ảnh giả; trả link bản đồ chính thức.

## Giới hạn baseline

- Chỉ hỗ trợ landmark có nhãn rõ trên ảnh.
- Không có GPS, zoom, pan hoặc sơ đồ động.
- Không hỗ trợ accessibility routing hay trạng thái lối đi theo thời gian.
- Không chỉnh sửa `bot/`, frontend hoặc nội dung raw đã được verify.

