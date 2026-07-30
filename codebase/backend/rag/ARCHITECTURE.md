# Kiến trúc RAG baseline — VinAI Discord Bot

> Trạng thái: chốt để triển khai benchmark, chưa phải cấu hình production cuối cùng
> Phạm vi: chỉ pipeline RAG trong `codebase/backend/rag/`
> Cập nhật: 30/07/2026

## 1. Mục tiêu và ràng buộc

Hệ thống trả lời câu hỏi tiếng Việt về nội quy, tiện ích và vị trí cơ sở vật chất dựa trên knowledge base chính thức. Ưu tiên theo thứ tự:

1. Không trả lời sai khi thiếu căn cứ.
2. Retrieve đúng đoạn và đúng nguồn.
3. Phản hồi nhanh trên CPU/máy cá nhân.
4. Ít dependency, dễ giải thích và debug trong thời gian hackathon.

Corpus hiện nhỏ, gồm một handbook, tài liệu thư viện/phòng, URL, ảnh bản đồ và một số file trùng lặp. Dữ liệu có cấu trúc riêng nên chunking phải theo đơn vị ngữ nghĩa của từng loại tài liệu, không dùng một text splitter cố định cho mọi file.

## 2. Quyết định về framework

### 2.1. Baseline dùng orchestration Python trực tiếp

Baseline không dùng LangChain, LlamaIndex hoặc Haystack làm lớp điều phối. Đây không phải quyết định rằng các framework này chậm; chưa có benchmark nội bộ để khẳng định điều đó. Lý do là chúng chưa tạo ra lợi ích đủ lớn cho pipeline hiện tại:

- Pipeline runtime chỉ có các bước cố định: normalize → dense/BM25 retrieve → fusion → gate → generate.
- Parser theo handbook, FAQ, room record và policy block vẫn phải viết riêng dù dùng framework.
- Corpus không cần connector, distributed vector database, agent graph hoặc document store server.
- API contract hiện đã chốt bằng dictionary đơn giản; thêm `Document`, `Node`, `Pipeline` hoặc `Runnable` abstraction sẽ tạo thêm mapping và dependency.
- Tracing cần thiết có thể ghi trực tiếp từ score/candidate; chưa cần platform tracing riêng.
- Direct pipeline giúp benchmark từng bước và giữ quyền kiểm soát confidence gate.

Ta vẫn dùng thư viện tối ưu cho từng primitive; “direct” chỉ áp dụng cho orchestration:

| Chức năng | Công cụ baseline |
|---|---|
| Gọi embedding/LLM | SDK chính thức của provider |
| Dense vector search | FAISS `IndexFlatIP` |
| Lexical search | BM25S |
| Numeric processing | NumPy |
| API | FastAPI hiện có |
| Test/eval | pytest + script benchmark nội bộ |

### 2.2. Khi nào nên dùng framework

LangChain phù hợp khi cần nhiều integrations, retriever/vector store có thể hoán đổi thường xuyên, agentic retrieval hoặc ecosystem tracing. LangChain mô tả RAG 2-step là kiến trúc đơn giản, predictable; framework cung cấp interface retriever và chain để tổ hợp các thành phần.

LlamaIndex phù hợp nhất trong ba framework nếu dự án phát triển thành hệ thống ingestion lớn, nhiều data connector, node transformation, recursive/hierarchical retrieval hoặc nhiều index.

Haystack phù hợp khi cần pipeline production dạng component graph, document store server, router, loop hoặc pipeline serialization/deployment.

Framework chỉ được đưa vào baseline nếu candidate framework đạt đồng thời:

- Không làm giảm quality so với direct pipeline.
- Warm retrieval p95 tăng không quá 10%.
- Cold start và RAM nằm trong giới hạn môi trường demo.
- Giảm rõ ràng lượng code hoặc độ khó vận hành.

## 3. Kiến trúc tổng đã chốt

```text
OFFLINE INGESTION

raw/
  │
  ├─ source registry + scope allowlist
  ├─ document-type parser
  ├─ structure-aware chunking
  ├─ metadata enrichment
  ├─ normalized-content deduplication
  ├─ validation
  │
  ├─ dense embedding ───────────────→ dense.index
  ├─ lexical tokenization ──────────→ bm25s index
  └─ chunks + model/config/hash ────→ chunks.jsonl + manifest.json


ONLINE QUERY

question
  │
  ├─ original Vietnamese query ─────→ embedding provider
  ├─ normalized lexical query ──────→ BM25S
  └─ accentless lexical variant ────→ BM25S
                  │
       dense top-8 + lexical top-8
                  │
       score normalization + weighted fusion
                  │
       deduplicate by canonical chunk_id
                  │
       confidence / ambiguity gate
            ┌─────┴─────┐
       insufficient   sufficient
            │             │
       fallback /       top 2–4 chunks
       ask again           │
                    grounded generation
                           │
               answer + sources + has_evidence
```

## 4. Công cụ baseline và lý do chọn

### 4.1. Dense search: FAISS `IndexFlatIP`

FAISS `IndexFlatIP` thực hiện exact inner-product search. Khi vector được L2-normalize, inner product tương đương cosine similarity. Với corpus nhỏ, exact search giữ recall và không cần train/tune index.

Không dùng HNSW, IVF hoặc PQ trong baseline vì:

- Corpus chưa đủ lớn để ANN tạo lợi ích.
- ANN thêm hyperparameter và có thể mất nearest neighbor thật.
- Thời gian query hiện chủ yếu nằm ở embedding API/local model và LLM, không nằm ở việc so vài chục hoặc vài trăm vector.

Candidate NumPy matrix multiplication được benchmark song song vì với corpus rất nhỏ, `embeddings @ query` có thể đơn giản và nhanh hơn chi phí wrapper/index. Chỉ giữ FAISS nếu nó nhanh tương đương hoặc tốt hơn và serialization ổn định.

### 4.2. Lexical search: BM25S

Baseline dùng `bm25s`, không dùng Elasticsearch/Pyserini:

- Chạy trong process Python.
- Dùng NumPy/SciPy sparse matrices và eager scoring.
- Có save/load và memory mapping.
- Không yêu cầu Java hoặc search server.
- Corpus nhỏ nhưng BM25 vẫn quan trọng cho tên phòng, số phòng, thời gian, con số và wording chính sách.

Tokenizer baseline:

1. Unicode NFC.
2. Lowercase.
3. Chuẩn hóa whitespace/punctuation.
4. Lập chỉ mục cho token nguyên dấu.
5. Thêm token biến thể không dấu cho lexical matching.

Word segmentation bằng `underthesea`/VnCoreNLP là candidate, không phải baseline. Nó chỉ được thêm nếu Recall/MRR tăng đủ bù latency và dependency.

### 4.3. Embedding runtime

Baseline dùng local `intfloat/multilingual-e5-small` qua Sentence Transformers
ONNX. Quyết định local-first tránh gửi toàn bộ corpus ra provider ngoài, dùng
vector 384 chiều và giữ query latency thấp sau warm-up. Document phải có prefix
`passage:`, query phải có prefix `query:`; thiếu prefix làm giảm retrieval
quality theo model card.

Model revision được pin trong config. Model và ONNX session chỉ load một lần;
backend phải gọi warm-up khi khởi động, không load model trong request. Kết quả
đo trên máy phát triển với 100 query runs:

- Cold load + query đầu: khoảng 19,2 giây.
- Warm query embedding p50: 5,17 ms.
- Warm query embedding p95: 6,00 ms.

Giữ ONNX FP32 portable trong baseline. Quantized ONNX chỉ là candidate nếu đo
trên máy demo chứng minh nhanh hơn mà không làm giảm quality. BGE-M3 chỉ
benchmark khi E5-small không đạt quality bar và máy có đủ RAM/CPU/GPU.

`text-embedding-3-small` là remote control candidate, chỉ được dùng nếu có phê
duyệt gửi chunk ra provider ngoài.

### 4.4. Fusion

Candidate mặc định:

```text
fused_score = alpha * normalized_dense_score
            + (1 - alpha) * normalized_bm25_score
```

Benchmark `alpha ∈ {0.6, 0.7, 0.8}`. Không dùng một threshold cố định cho fused score trước khi calibration.

RRF là candidate score-free để kiểm tra tính ổn định, nhưng nghiên cứu Vietnamese IR EACL 2026 cho thấy BM25 linear interpolation thường đáng tin cậy hơn RRF trên nhiều domain tiếng Việt.

### 4.5. Generator

Generator dùng SDK chính thức của provider, không dùng framework chain:

- Input chỉ gồm question, strict system prompt và top context.
- Temperature thấp hoặc 0.
- Source trả ra phải là subset của retrieved chunk IDs.
- Không đủ evidence thì không gọi generator.
- Không tự thao tác đặt lịch; chỉ hướng dẫn quy trình.

### 4.6. Link trong câu trả lời

Hệ thống có thể trả link chính thức khi chunk đã có `source_url` được lấy từ raw document hoặc source registry. Link không được để LLM tự tạo hoặc suy đoán.

Quy tắc:

- `source_url` được thu thập và kiểm tra từ ingestion.
- Generator chỉ được dùng URL nằm trong retrieved chunks.
- Link được thêm ở cuối câu trả lời dưới mục `Nguồn tham khảo`.
- Nhiều chunk cùng URL chỉ hiển thị URL một lần.
- Chunk không có URL vẫn được cite bằng `source#heading`.
- Không thay đổi API contract trong baseline: link có thể nằm trong `answer`, còn `sources` tiếp tục trả source identifiers.

Nếu sau benchmark cần UI render link riêng, có thể mở rộng response bằng trường `source_links`, nhưng đây là thay đổi API và phải được role build đồng thuận trước.

### 4.7. Reject và routing

Routing không được dùng như hard domain filter trong baseline đầu tiên. Corpus hiện nhỏ nên tìm trên toàn bộ exact index rất nhanh; query thực tế lại ngắn, không dấu và mơ hồ, khiến hard routing có nguy cơ loại nhầm passage đúng.

Triển khai theo hai tầng:

1. **Fast reject/rule route — nên triển khai sớm sau khi retriever hoạt động**
   - Input rỗng hoặc chỉ punctuation.
   - Greeting không chứa câu hỏi.
   - Yêu cầu hành động ngoài thẩm quyền như tự đặt phòng.
   - Nội dung vi phạm boundary đã chốt.
   - Các case này không cần gọi embedding/generator hoặc được route thẳng tới câu trả lời deterministic.
2. **Evidence routing — baseline chính**
   - Chạy hybrid retrieval trên toàn corpus.
   - Confidence gate quyết định trả lời, hỏi lại hoặc từ chối.
   - Domain signal chỉ được dùng làm soft score boost, không xóa candidate.

Hard domain routing chỉ được bật nếu benchmark chứng minh đồng thời:

- Không giảm Recall@3.
- False reject không tăng.
- Retrieval p95 giảm có ý nghĩa so với exact full-corpus search.

Vì embedding/generation mới là phần chiếm latency chính, routing theo domain ở corpus hiện tại không được kỳ vọng tạo cải thiện tốc độ đáng kể.

## 5. Chunking theo dữ liệu

Kích thước chỉ là safety limit:

```text
target: 500–900 ký tự
max: 1200 ký tự
overlap: 0 cho atomic unit
fallback overlap: 80–120 ký tự nếu một atomic unit bắt buộc phải cắt
```

Ranh giới ưu tiên:

1. FAQ question + full answer = một chunk.
2. Một room record = một chunk, có parent heading.
3. Giờ thư viện theo từng giai đoạn/tháng = một chunk.
4. Chính sách đặt phòng chia theo điều kiện, thời điểm, hủy/sử dụng.
5. Handbook chia theo mục La Mã → mục số → tiểu mục.
6. Hướng dẫn Outlook giữ đủ các bước trong một chunk.

Metadata bắt buộc:

```json
{
  "chunk_id": "library::rooms::a102",
  "source": "4_gio_mo_cua_library.txt",
  "title": "Thư viện VinUniversity",
  "heading_path": ["Danh sách phòng", "Phòng A102"],
  "text": "...",
  "embedding_text": "Thư viện VinUniversity > Danh sách phòng > Phòng A102\n...",
  "content_hash": "...",
  "source_url": "..."
}
```

Deduplicate theo normalized-content hash trước khi embedding. `4_gio_mo_cua_library.txt` là canonical source cho nội dung trùng với `6_loai_phong_va_huong_dan_dat_phong.txt`.

Không index:

- Placeholder `.md`.
- URL-only document như một semantic chunk.
- Chatlog và transcript vào production KB.
- `5_ket_qua_khoa_1.txt` khi scope vẫn chỉ là nội quy/tiện ích/vị trí.
- `1_map.jpg` cho đến khi role data cung cấp sidecar text đã kiểm chứng.

## 6. Candidate matrix

Mỗi benchmark chỉ thay một trục, giữ nguyên các trục còn lại.

### 6.1. Orchestration/framework

| ID | Candidate | Mục đích |
|---|---|---|
| F0 | Direct Python functions | Baseline |
| F1 | LangChain 2-step RAG/retriever | Đo overhead và ergonomics |
| F2 | LlamaIndex ingestion + retriever | Kiểm tra lợi ích node/index abstraction |
| F3 | Haystack component pipeline | Chỉ thử nếu cần pipeline serialization/deployment |

### 6.2. Embedding

| ID | Candidate | Runtime | Kỳ vọng |
|---|---|---|---|
| E0 | `intfloat/multilingual-e5-small` | Sentence Transformers ONNX | Local baseline |
| E1 | `text-embedding-3-small` | OpenAI API | Remote control, cần duyệt data |
| E2 | `text-embedding-3-large` | OpenAI API | Remote quality control, cần duyệt data |
| E3 | `intfloat/multilingual-e5-large` | FastEmbed ONNX | Local quality candidate, model lớn |
| E4 | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | FastEmbed | Local lightweight control |
| E5 | `BAAI/bge-m3` | FlagEmbedding | Multilingual quality candidate, nặng |

Với E0/E3, phải dùng đúng prefix `query:` và `passage:`.

### 6.3. Dense vector engine

| ID | Candidate | Ghi chú |
|---|---|---|
| V0 | FAISS `IndexFlatIP` | Exact cosine qua normalized vectors |
| V1 | NumPy matrix dot product | Có thể thắng ở corpus cực nhỏ |
| V2 | FAISS HNSW | Chỉ benchmark khi số chunk tăng lớn; không baseline |

### 6.4. Lexical/tokenizer

| ID | Candidate |
|---|---|
| L0 | BM25S + whitespace/punctuation tokenizer + accentless tokens |
| L1 | BM25S + Vietnamese word segmentation |
| L2 | Dense-only control |
| L3 | BM25-only control |

### 6.5. Fusion/reranking

| ID | Candidate |
|---|---|
| R0 | Linear fusion, alpha 0.6/0.7/0.8 |
| R1 | Reciprocal Rank Fusion |
| R2 | No reranker |
| R3 | `bge-reranker-v2-m3` trên top-8 |
| R4 | FastEmbed multilingual cross-encoder trên top-8, nếu license phù hợp |

Reranker chỉ được chọn nếu Recall@5 đã cao nhưng MRR/Precision@1 còn thấp và p95 vẫn đạt bar.

### 6.6. Chunking

| ID | Candidate |
|---|---|
| C0 | Structure-aware/atomic chunking đã mô tả |
| C1 | Structure-aware nhưng gộp toàn subsection |
| C2 | Fixed 600 chars, overlap 100 — control |

## 7. Benchmark protocol

### 7.1. Golden set

Tối thiểu 30 câu, bao gồm:

- FAQ/nội quy.
- Giờ thư viện theo tháng/ngày.
- Quyền truy cập.
- Chính sách đặt phòng.
- Phòng cụ thể và câu hỏi liệt kê phòng.
- Câu ngắn, không dấu, viết tắt, lỗi chính tả nhẹ.
- Câu mơ hồ.
- Câu ngoài scope/không có evidence.
- Câu hỏi vị trí đang bị block bởi map chưa có sidecar.

Mỗi case có:

```json
{
  "id": "Q001",
  "question": "...",
  "answerable": true,
  "expected_chunk_ids": ["library::hours::sep"],
  "category": "short_query"
}
```

### 7.2. Quality metrics

- Recall@1, Recall@3, Recall@5.
- MRR@10.
- nDCG@10 khi có nhiều passage đúng.
- Answerability precision/recall.
- False-accept rate trên câu không có căn cứ.
- Duplicate rate trong final top-k.
- Citation source accuracy.

### 7.3. Performance metrics

Đo riêng từng stage:

- Process import/cold start.
- Model/index load time.
- Peak RSS.
- Index build time và artifact size.
- Query normalization.
- Query embedding.
- Dense search.
- BM25 search.
- Fusion/gating.
- Retrieval p50/p95/p99.
- End-to-end `/ask` p50/p95, tách riêng generation.

Local candidates:

- Warm-up trước khi đo.
- Tối thiểu 100 query runs.
- Giữ cùng thread count và cùng máy.

Remote API candidates:

- Ghi model, region/thời điểm và network.
- Đo tối thiểu 20–30 runs.
- Báo latency riêng cho API và local retrieval.

Framework benchmark F0–F3 phải giữ cùng embedding vectors, chunks, index và generator mock để chỉ đo orchestration overhead.

### 7.4. Quality bar tạm thời

- Recall@3 ≥ 90%.
- MRR@10 ≥ 0.85.
- False-accept rate ≤ 5%.
- Citation source accuracy = 100%.
- Duplicate chunks trong final top-k = 0.
- Local search + fusion p95 ≤ 50 ms với corpus hiện tại.
- Retrieval trước generation p95 ≤ 800 ms khi dùng remote embedding.
- End-to-end `/ask` p95 ≤ 3 giây trong môi trường demo.

Quality bar chỉ được chốt sau lượt benchmark đầu và không được thay đổi để che kết quả kém.

## 8. Thứ tự thử nghiệm

Không chạy full Cartesian product. Thử theo funnel:

1. C0 + E0 + V0 + L0 + R0 + F0.
2. Chọn chunking bằng C0/C1/C2, giữ các trục khác.
3. Đo E0; chỉ thêm E3/E5 nếu thiếu accuracy và E1/E2 khi data được phép gửi ra ngoài.
4. So V0/V1.
5. Tune alpha và threshold bằng answerable + unanswerable cases.
6. Chỉ thử reranker nếu retrieval recall tốt nhưng rank đầu chưa tốt.
7. So F0/F1/F2 sau khi pipeline đúng; F3 chỉ khi xuất hiện nhu cầu deployment graph.

Candidate thắng phải nằm trên Pareto frontier quality–latency–memory. Không chọn model/framework chỉ vì benchmark công khai cao hơn nếu thua trên dữ liệu thật của dự án.

## 9. Baseline được duyệt để bắt đầu coding

```text
Orchestration: direct Python
Chunking: C0 structure-aware
Embedding: E0 intfloat/multilingual-e5-small, local ONNX FP32
Dense index: V0 FAISS IndexFlatIP
Lexical: L0 BM25S + accentless tokens
Fusion: R0 weighted linear, alpha benchmark 0.6/0.7/0.8
Reranker: none
Gate: calibrated trên golden set
Generator: provider SDK, grounded prompt, source whitelist
```

## 10. Tài liệu tham khảo

- LangChain retrieval: https://docs.langchain.com/oss/python/langchain/retrieval
- LlamaIndex query pipeline: https://docs.llamaindex.ai/en/stable/module_guides/querying/pipeline/
- Haystack pipelines: https://docs.haystack.deepset.ai/docs/pipelines
- FastEmbed: https://qdrant.github.io/fastembed/
- FastEmbed supported models: https://qdrant.github.io/fastembed/examples/Supported_Models/
- Sentence Transformers inference optimization: https://www.sbert.net/docs/sentence_transformer/usage/efficiency.html
- BM25S paper: https://arxiv.org/abs/2407.03618
- BM25S repository: https://github.com/xhluca/bm25s
- FAISS index selection: https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index
- FAISS index types: https://github.com/facebookresearch/faiss/wiki/Faiss-indexes
- FlagEmbedding/BGE-M3: https://github.com/FlagOpen/FlagEmbedding
- OpenAI `text-embedding-3-small`: https://developers.openai.com/api/docs/models/text-embedding-3-small
- Vietnamese IR benchmark: https://aclanthology.org/2026.findings-eacl.110/
