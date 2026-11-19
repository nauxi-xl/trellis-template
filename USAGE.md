# Cẩm Nang Hướng Dẫn Sử Dụng Toàn Bộ Skill Trong Trellis Template

> Tài liệu hướng dẫn chi tiết cách sử dụng 15 kỹ năng (skills), quy trình kích hoạt, công cụ tích hợp và kịch bản thực tế cho các trợ lý lập trình AI (Google Antigravity, Claude Code, GitHub Copilot, OpenAI Codex, Cursor).

---

## Mục lục

1. [Tổng Quan Kiến Trúc Skill](#1-tổng-quan-kiến-trúc-skill)
2. [Bảng Tra Cứu Nhanh 15 Skills](#2-bảng-tra-cứu-nhanh-15-skills)
3. [Chi Tiết Từng Skill](#3-chi-tiết-từng-skill)
   - **Nhóm 1: Khởi Tạo, Khám Phá & Nghiên Cứu (Discovery & Planning)**
     - [1. sdlc-adaptive-discovery](#1-sdlc-adaptive-discovery)
     - [2. trellis-start](#2-trellis-start)
     - [3. trellis-brainstorm](#3-trellis-brainstorm)
     - [4. research](#4-research)
   - **Nhóm 2: Chuẩn Bị & Trí Tuệ Lập Trình (Pre-Dev & Code Intelligence)**
     - [5. trellis-before-dev](#5-trellis-before-dev)
     - [6. lsp](#6-lsp)
     - [7. trellis-continue](#7-trellis-continue)
   - **Nhóm 3: Kiểm Định Chất Lượng & Tự Phục Hồi (Verification & Self-Healing)**
     - [8. trellis-check](#8-trellis-check)
     - [9. trellis-break-loop](#9-trellis-break-loop)
   - **Nhóm 4: Đóng Gói, Đồng Bộ & Tiến Hóa Tri Thức (Wrap-up & Knowledge)**
     - [10. trellis-finish-work](#10-trellis-finish-work)
     - [11. trellis-update-spec](#11-trellis-update-spec)
     - [12. trellis-session-insight](#12-trellis-session-insight)
     - [13. trellis-spec-bootstrap](#13-trellis-spec-bootstrap)
   - **Nhóm 5: Đa Tác Tử & Quản Trị Hệ Thống (Multi-Agent & Meta)**
     - [14. trellis-channel](#14-trellis-channel)
     - [15. trellis-meta](#15-trellis-meta)
4. [Tích Hợp Công Cụ Nền Tảng (Worktree, Dynamic Context, CI/CD, LSP)](#4-tích-hợp-công-cụ-nền-tảng)

---

## 1. Tổng Quan Kiến Trúc Skill

Framework `trellis-template` chuẩn hóa toàn bộ kỹ năng dưới định dạng **Portable Agent Skill Standard**:
- Thư mục chuẩn: [.agents/skills/](.agents/skills/) (Google Antigravity và chuẩn dùng chung).
- Liên kết đồng bộ (symlink): [.claude/skills/](.claude/skills/) (Claude Code) và [.github/skills/](.github/skills/) (GitHub Copilot) được trỏ symlink trực tiếp về `../.agents/skills` để đảm bảo không lệch phiên bản.
- Cấu trúc tệp tiêu chuẩn: Mỗi skill bắt buộc chứa tệp `SKILL.md` với YAML frontmatter (`name`, `description`, `user-invocable`), đi kèm thư mục phụ trợ `scripts/`, `references/` nếu có.

```
.agents/skills/
├── <skill-name>/
│   ├── SKILL.md                 # Hướng dẫn quy trình chính cho Agent
│   ├── references/              # Hợp đồng kiến trúc, CLI cheet-sheet, checklist
│   └── scripts/                 # Công cụ tự động hóa bổ trợ
```

---

## 2. Bảng Tra Cứu Nhanh 15 Skills

| # | Tên Skill | Lệnh / Kích hoạt | Mục đích cốt lõi | Giai đoạn SDLC |
|---|-----------|-------------------|------------------|----------------|
| 1 | **`sdlc-adaptive-discovery`** | `/sdlc-discovery` | Phỏng vấn 5D, ma trận chọn mô hình SDLC, kích hoạt Hội đồng Thẩm định | Giai đoạn 0: Khởi tạo dự án |
| 2 | **`trellis-start`** | `/trellis-start` | Nạp trạng thái session, kiểm tra git, phân loại intent và định tuyến luồng | Giai đoạn 1: Mở đầu session |
| 3 | **`trellis-brainstorm`** | `/trellis-brainstorm` | Đào sâu yêu cầu 1 câu hỏi/lần, tạo task, lập PRD & MVP scope | Giai đoạn 1: Lập kế hoạch |
| 4 | **`research`** | `/research <topic>` | Nghiên cứu tài liệu chính thống (Context7) và lưu trữ NotebookLM bền vững | Xuyên suốt: Nghiên cứu kỹ thuật |
| 5 | **`trellis-before-dev`** | `/trellis-before-dev` | Khám phá & nạp spec coding conventions từ `.trellis/spec/` trước khi viết code | Giai đoạn 2: Trước khi sửa code |
| 6 | **`lsp`** | `/lsp`, `/lsp-refactor` | Trí tuệ code ngữ nghĩa qua `agent-lsp`: blast radius, inspect type, safe edit | Giai đoạn 2: Lập trình & Refactor |
| 7 | **`trellis-continue`** | `/trellis-continue` | Nối lại task dở dang, tự động nạp vị trí bước trong `workflow.md` | Giai đoạn 2: Tiếp tục công việc |
| 8 | **`trellis-check`** | `/trellis-check` | Kiểm tra spec, chạy lint/typecheck/test qua vòng lặp verify tự phục hồi | Giai đoạn 2: Kiểm định chất lượng |
| 9 | **`trellis-break-loop`** | `/trellis-break-loop` | Phân tích hồi quy sâu khi bug lặp lại, chặn chu kỳ sửa-quên-lại sửa | Giai đoạn 2 & 3: Xử lý bug lặp |
| 10 | **`trellis-finish-work`** | `/trellis-finish-work` | Lưu nhật ký session, kiểm tra branch isolation và lưu trữ (archive) task | Giai đoạn 3: Kết thúc session |
| 11 | **`trellis-update-spec`** | `/trellis-update-spec` | Ghi nhận hợp đồng kiến trúc, patterns và conventions vào `.trellis/spec/` | Giai đoạn 3: Cập nhật spec |
| 12 | **`trellis-session-insight`**| `/trellis-session-insight`| Tra cứu lịch sử đối thoại quá khứ qua CLI `trellis mem` | Hỗ trợ: Truy vết quyết định |
| 13 | **`trellis-spec-bootstrap`** | `/trellis-spec-bootstrap` | Khởi tạo bộ spec ban đầu dựa trên quét mã thực tế của dự án | Khởi tạo: Thiết lập dự án |
| 14 | **`trellis-channel`** | `/trellis-channel` | Điều phối nhiều sub-agent song song, chia sẻ message board và forum | Nâng cao: Đa Agent |
| 15 | **`trellis-meta`** | `/trellis-meta` | Tùy biến kiến trúc nội bộ `.trellis/`, hooks, workflows và agent runtime | Quản trị: Framework Meta |

---

## 3. Chi Tiết Từng Skill

### 1. `sdlc-adaptive-discovery`
* **Vị trí**: [.agents/skills/sdlc-adaptive-discovery/SKILL.md](.agents/skills/sdlc-adaptive-discovery/SKILL.md)
* **Kích hoạt**: Gõ `/sdlc-discovery` hoặc khi bắt đầu một dự án mới từ ý tưởng thô của người dùng.
* **Mục đích**:
  - Thực hiện chu trình vấn đáp sâu 5 chiều: Nghiệp vụ (Business), Kỹ thuật (Technical), Rủi ro (Risk), Vận hành (Operational), và Trải nghiệm người dùng (UX).
  - Tự động đánh giá ma trận 5 mô hình phát triển: **Agile/Scrum**, **Waterfall**, **TDD**, **Spiral**, hoặc **Kanban**.
  - Kích hoạt Hội đồng Thẩm định chuyên trách (Agent Council: Architect, Security Specialist, Tech Lead, QA Lead).
* **Đầu ra**: Tài liệu kế hoạch SDLC, bảng ma trận quyết định và khởi tạo task PRD nền tảng.

### 2. `trellis-start`
* **Vị trí**: [.agents/skills/trellis-start/SKILL.md](.agents/skills/trellis-start/SKILL.md)
* **Kích hoạt**: Gõ `/trellis-start` khi bắt đầu một phiên làm việc mới hoặc chuyển đổi ngữ cảnh.
* **Mục đích**:
  - Đọc danh tính lập trình viên (`init_developer.py`), trạng thái git (`git status`).
  - Kiểm tra các task đang hoạt động trong `.trellis/tasks/`.
  - Phân loại yêu cầu của người dùng: Task đơn giản $\rightarrow$ Direct edit; Task phức tạp $\rightarrow$ Lập kế hoạch theo `workflow.md`.
* **Đầu ra**: Báo cáo trạng thái phiên làm việc và hướng dẫn hành động tiếp theo.

### 3. `trellis-brainstorm`
* **Vị trí**: [.agents/skills/trellis-brainstorm/SKILL.md](.agents/skills/trellis-brainstorm/SKILL.md)
* **Kích hoạt**: Gõ `/trellis-brainstorm` hoặc khi yêu cầu chưa rõ ràng, có nhiều hướng tiếp cận hợp lệ.
* **Mục đích**:
  - Đặt từng câu hỏi giá trị cao (High-value questions) một lần một, tránh làm người dùng choáng ngợp.
  - Tạo thư mục task `.trellis/tasks/<date>-<name>/` và khởi tạo `prd.md`.
  - Giúp hội tụ phạm vi MVP khả thi trước khi bước vào viết code.
* **Đầu ra**: Bản `prd.md` đầy đủ yêu cầu, ràng buộc kỹ thuật và tiêu chí nghiệm thu (acceptance criteria).

### 4. `research`
* **Vị trí**: [.agents/skills/research/SKILL.md](.agents/skills/research/SKILL.md)
* **Kích hoạt**: Gõ `/research <chủ đề>` (ví dụ: `/research nextjs 15 app router`, `/research vulkan compute shaders`).
* **Mục đích**:
  - Kết hợp **Context7 MCP** để truy xuất tài liệu phiên bản mới nhất từ trang chủ thư viện / SDK / API.
  - Sử dụng **Google NotebookLM MCP** (`gemini-notebook-mcp` hoặc CLI `nlm`) để tự động tạo sổ tay, nạp tài liệu và ghi chú tri thức bền vững xuyên session.
* **Đầu ra**: Sổ tay NotebookLM, bản tóm tắt kỹ thuật chuyên sâu kèm code snippet và liên kết tham chiếu.

### 5. `trellis-before-dev`
* **Vị trí**: [.agents/skills/trellis-before-dev/SKILL.md](.agents/skills/trellis-before-dev/SKILL.md)
* **Kích hoạt**: Gõ `/trellis-before-dev` trước khi bắt đầu chỉnh sửa hoặc thêm mới code trong một package/layer.
* **Mục đích**:
  - Nạp các quy chuẩn kiến trúc hiện có từ `.trellis/spec/` (Frontend, Backend, Database, Error Handling).
  - Đọc các cẩm nang tư duy chung: `cross-layer-thinking-guide.md` và `code-reuse-thinking-guide.md`.
  - Ngăn ngừa tình trạng AI code tự do phá vỡ cấu trúc và phong cách hiện có của dự án.
* **Đầu ra**: Danh sách checklist và ràng buộc kiến trúc cần tuân thủ trong lần sửa đổi này.

### 6. `lsp`
* **Vị trí**: [.agents/skills/lsp/SKILL.md](.agents/skills/lsp/SKILL.md)
* **Kích hoạt**: Gõ `/lsp`, `/lsp-refactor`, `/lsp-safe-edit` hoặc khi cần phân tích cấu trúc code, đổi tên symbol hay refactor.
* **Mục đích**:
  - Sử dụng công cụ **`agent-lsp`** (hỗ trợ hơn 32 ngôn ngữ) thay vì grep mù quáng:
    - `blast_radius`: Phân tích bán kính ảnh hưởng của thay đổi (chia tách caller môi trường thực tế vs caller trong test).
    - `inspect_symbol`: Đọc docstring, type signature chuẩn xác.
    - `preview_edit` & `safe_apply_edit`: Mô phỏng sửa code trong bộ nhớ, kiểm tra sai số compiler trước khi ghi xuống đĩa.
    - `rename_symbol`: Đổi tên đồng bộ trên toàn bộ dự án mà không sợ sót biến.
* **Đầu ra**: Báo cáo phạm vi ảnh hưởng, bản sửa đổi speculatively verified và mã nguồn an toàn.

### 7. `trellis-continue`
* **Vị trí**: [.agents/skills/trellis-continue/SKILL.md](.agents/skills/trellis-continue/SKILL.md)
* **Kích hoạt**: Gõ `/trellis-continue` khi quay lại làm việc sau giờ nghỉ hoặc trong phiên làm việc mới.
* **Mục đích**:
  - Định vị chính xác giai đoạn hiện tại (Phase 1: Plan, Phase 2: Execute, Phase 3: Finish) dựa trên trạng thái của task active.
  - Tự động nạp context từ `prd.md`, `design.md`, `implement.md`.
* **Đầu ra**: Hướng dẫn bước tiếp theo cần thực thi theo đúng `workflow.md`.

### 8. `trellis-check`
* **Vị trí**: [.agents/skills/trellis-check/SKILL.md](.agents/skills/trellis-check/SKILL.md)
* **Kích hoạt**: Gõ `/trellis-check` sau khi viết code xong hoặc trước khi commit.
* **Mục đích**:
  - Chạy bộ kiểm thử tự phục hồi thông qua `python3 .trellis/scripts/verify.py`.
  - Kiểm tra tính tuân thủ quy chuẩn spec, chạy typecheck (`tsc`, `pyright`, `mypy`), linting (`ruff`, `eslint`) và test suite.
  - Đóng gói lỗi vào cấu trúc `<self-healing-feedback>` để tự sửa lỗi trong vòng lặp lặp lại có giới hạn (bounded iterations).
* **Đầu ra**: Báo cáo kiểm định chất lượng: PASS (xanh) hoặc mã envelope lỗi chi tiết.

### 9. `trellis-break-loop`
* **Vị trí**: [.agents/skills/trellis-break-loop/SKILL.md](.agents/skills/trellis-break-loop/SKILL.md)
* **Kích hoạt**: Gõ `/trellis-break-loop` khi phát hiện một bug đã sửa nhưng tiếp tục phát sinh lại hoặc các bài test liên tục fail.
* **Mục đích**:
  - Phân loại nguyên nhân gốc rễ (Root Cause Category).
  - Phân tích vì sao các lần vá trước thất bại (Why fixes failed).
  - Thiết lập cơ chế phòng ngừa vĩnh viễn (Prevention mechanism) và cập nhật vào `.trellis/spec/`.
* **Đầu ra**: Báo cáo phân tích hồi quy chuyên sâu và bài test mới chống tái phát bug.

### 10. `trellis-finish-work`
* **Vị trí**: [.agents/skills/trellis-finish-work/SKILL.md](.agents/skills/trellis-finish-work/SKILL.md)
* **Kích hoạt**: Gõ `/trellis-finish-work` sau khi đã commit code hoàn tất ở Phase 3.
* **Mục đích**:
  - Ghi nhật ký tóm tắt phiên làm việc vào `.trellis/workspace/<Developer>/journal-1.md`.
  - Di chuyển task đã hoàn thành từ `.trellis/tasks/<task>/` vào thư mục lưu trữ `.trellis/tasks/archive/<YYYY-MM>/`.
  - Xác nhận nhánh git sạch sẽ và an toàn.
* **Đầu ra**: Cập nhật tệp journal và dọn sạch danh sách active task.

### 11. `trellis-update-spec`
* **Vị trí**: [.agents/skills/trellis-update-spec/SKILL.md](.agents/skills/trellis-update-spec/SKILL.md)
* **Kích hoạt**: Gõ `/trellis-update-spec` khi vừa rút ra một bài học kinh nghiệm, thiết kế một hợp đồng API mới hoặc sau khi sửa lỗi phức tạp.
* **Mục đích**:
  - Cập nhật các quy ước code sống (living specifications) trong `.trellis/spec/`.
  - Đảm bảo các phiên làm việc trong tương lai của các lập trình viên/agent khác không lặp lại sai lầm cũ.
* **Đầu ra**: Tệp đặc tả được bổ sung quy định mới kèm ví dụ thực tế.

### 12. `trellis-session-insight`
* **Vị trí**: [.agents/skills/trellis-session-insight/SKILL.md](.agents/skills/trellis-session-insight/SKILL.md)
* **Kích hoạt**: Gõ `/trellis-session-insight` hoặc hỏi trợ lý: *"Trước đây chúng ta đã giải quyết vấn đề X như thế nào?"*.
* **Mục đích**:
  - Sử dụng lệnh `trellis mem` để tìm kiếm ngược lại lịch sử trò chuyện qua các nền tảng (Claude Code, Codex, OpenCode, Antigravity).
  - Trích xuất quyết định kiến trúc, đoạn mã thảo luận hoặc lý do chọn công nghệ trong quá khứ.
* **Đầu ra**: Trích dẫn hội thoại gốc và bối cảnh giải pháp trước đây.

### 13. `trellis-spec-bootstrap`
* **Vị trí**: [.agents/skills/trellis-spec-bootstrap/SKILL.md](.agents/skills/trellis-spec-bootstrap/SKILL.md)
* **Kích hoạt**: Gõ `/trellis-spec-bootstrap` khi áp dụng Trellis vào một repository code có sẵn nhưng chưa có thư mục `.trellis/spec/`.
* **Mục đích**:
  - Quét mã nguồn hiện tại, phân tích layer (frontend, backend, infra, shared).
  - Khởi tạo các tài liệu spec chuẩn hóa (`directory-structure.md`, `error-handling.md`, `quality-guidelines.md`) dựa trên phong cách code thực tế của dự án (không dùng văn bản mẫu placeholder).
* **Đầu ra**: Bộ khung đặc tả hoàn chỉnh và sẵn sàng sử dụng trong `.trellis/spec/`.

### 14. `trellis-channel`
* **Vị trí**: [.agents/skills/trellis-channel/SKILL.md](.agents/skills/trellis-channel/SKILL.md)
* **Kích hoạt**: Gõ `/trellis-channel` khi cần phối hợp nhiều agent song song (Multi-Agent Swarm / Workers).
* **Mục đích**:
  - Quản lý message board sự kiện dùng chung cho các sub-agent thông qua `trellis channel`.
  - Phân công nhiệm vụ (spawn worker), kiểm tra tiến độ chéo (cross-agent review) và theo dõi log thực thi.
* **Đầu ra**: Hệ thống kênh liên lạc thời gian thực giữa các tác tử AI.

### 15. `trellis-meta`
* **Vị trí**: [.agents/skills/trellis-meta/SKILL.md](.agents/skills/trellis-meta/SKILL.md)
* **Kích hoạt**: Gõ `/trellis-meta` khi người dùng muốn tùy biến kiến trúc của chính framework Trellis bên trong repository.
* **Mục đích**:
  - Hướng dẫn chỉnh sửa hooks, chuyển đổi workflow template (native, tdd, channel-driven), cấu hình sub-agent definitions trong `.trellis/agents/`.
* **Đầu ra**: Cấu hình Trellis đã được cá nhân hóa theo đặc thù dự án.

---

## 4. Tích Hợp Công Cụ Nền Tảng

### A. Git Worktrees Cách Ly (`worktree.py`)
Mọi task phức tạp đều nên chạy trên một worktree độc lập:
```bash
# Tạo worktree cho task:
python3 .trellis/scripts/worktree.py create <task-id>

# Xem danh sách worktree:
python3 .trellis/scripts/worktree.py list

# Gộp task vào main sau khi verify:
python3 .trellis/scripts/worktree.py merge <task-id> --remove
```

### B. Dynamic Context Engine (`dynamic_context.py`)
Lắp ráp ngữ cảnh động theo thời gian thực:
```bash
# Xem tóm tắt ngắn:
python3 .trellis/scripts/dynamic_context.py --format text

# Xuất định dạng prompt cho Agent:
python3 .trellis/scripts/dynamic_context.py --format prompt
```

### C. Self-Healing Verification Runner (`verify.py`)
Kiểm định mã nguồn và chẩn đoán tự sửa lỗi:
```bash
# Chạy dry-run kiểm tra công cụ:
python3 .trellis/scripts/verify.py --dry-run

# Chạy toàn bộ các stage (typecheck, lint, test):
python3 .trellis/scripts/verify.py --stage all --format text
```

### D. Trí Tuệ Ngôn Ngữ LSP (`agent-lsp`)
Kiểm tra tình trạng sẵn sàng của các Language Server:
```bash
agent-lsp doctor
```
Sau đó kích hoạt skill `/lsp` để thực hiện refactor hoặc phân tích bán kính ảnh hưởng (`blast_radius`).

### E. Kiến Trúc CI/CD Tự Động (`.github/workflows/`)
Mọi commit và PR đều được thẩm định tự động qua:
- [ci.yml](.github/workflows/ci.yml): Kiểm tra ma trận kiểm thử, `verify.py` và Trellis task.
- [pr-verify.yml](.github/workflows/pr-verify.yml): Chặn PR từ nhánh `main` và kiểm soát tính toàn vẹn của nhánh cách ly.
- [nightly-health.yml](.github/workflows/nightly-health.yml): Định kỳ kiểm tra toolchain.

### F. Cập Nhật Framework Từ Remote (`update_framework.py`)
Kiểm tra và đồng bộ phiên bản mới của framework từ remote Git (giữ nguyên `.trellis/tasks/`, `.trellis/workspace/`, `.trellis/config.yaml` và các file tùy biến cục bộ):
```bash
# Kiểm tra xem có bản cập nhật mới hay không:
python3 .trellis/scripts/update_framework.py --check

# Xem trước danh sách file sẽ thêm/cập nhật/bỏ qua:
python3 .trellis/scripts/update_framework.py --dry-run

# Cập nhật từ remote tùy chỉnh (hoặc URL Git):
python3 .trellis/scripts/update_framework.py --remote upstream --branch main

# Ghi đè cả file framework đã chỉnh sửa cục bộ (vẫn tự động sao lưu trước):
python3 .trellis/scripts/update_framework.py --force

# Khôi phục lại bản sao lưu gần nhất trong .trellis/.backup-*:
python3 .trellis/scripts/update_framework.py --rollback
```
> Khi bắt đầu phiên làm việc (`SessionStart`), hook tự động chạy `update_framework.py --session-start-prompt` để kiểm tra xem framework hiện tại có cũ hơn remote hay không; nếu có bản mới, trợ lý AI sẽ thông báo và hỏi bạn có muốn cập nhật trước khi bắt đầu công việc hay không (tắt kiểm tra tự động bằng `check_on_session_start: false` trong `.trellis/config.yaml` hoặc `TRELLIS_CHECK_REMOTE_ON_START=0`).

### G. Cài Đặt Nhanh Công Cụ Trên Máy Mới (`scripts/install-tools.sh`)
Khi clone template sang một máy mới, chạy script cài đặt để chuẩn bị đầy đủ toolchain (`trellis`, `graphify`, `notebooklm-mcp`/`nlm`, `context7`, `agent-lsp`, và các Language Server):
```bash
# Linux / macOS / WSL / Git Bash:
./scripts/install-tools.sh --init-mcp

# Hoặc chỉ kiểm tra trạng thái công cụ đã cài:
./scripts/install-tools.sh --check

# Windows PowerShell:
.\scripts\install-tools.ps1 -InitMcp
```
