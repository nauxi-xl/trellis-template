# Trellis AI Template — Hướng Dẫn Sử Dụng Nhanh (Plug & Play)

> **Biến trợ lý AI lập trình của bạn (Google Antigravity, Claude Code, GitHub Copilot, OpenAI Codex) thành một đội ngũ làm việc có quy trình**: tự hỏi rõ yêu cầu trước khi làm, tự kiểm tra lỗi trước khi trả kết quả, và tự ghi nhớ kiến thức dự án qua **Google NotebookLM**.

Bạn **không cần hiểu sâu về kỹ thuật** bên dưới. Chỉ cần làm theo **3 bước cài đặt** dưới đây là có thể dùng ngay cho mọi dự án.

---

## Mục lục

- [1. Cài đặt trong 3 bước](#1-cài-đặt-trong-3-bước)
- [2. Áp dụng vào dự án bất kỳ](#2-áp-dụng-vào-dự-án-bất-kỳ)
- [3. Cách sử dụng hằng ngày](#3-cách-sử-dụng-hằng-ngày)
- [4. Kết nối & tương tác với NotebookLM](#4-kết-nối--tương-tác-với-notebooklm)
- [5. Các câu hỏi thường gặp](#5-các-câu-hỏi-thường-gặp)

---

## 1. Cài đặt trong 3 bước

### Yêu cầu tối thiểu trên máy
- **Git**, **Python 3**, và **Node.js** đã cài sẵn.

### Bước 1: Tải template và cài công cụ tự động

Mở terminal tại thư mục `trellis-template` và chạy **1 lệnh duy nhất**:

- **Linux / macOS / WSL:**
  ```bash
  ./scripts/install-tools.sh --init-mcp
  ```
- **Windows (PowerShell):**
  ```powershell
  .\scripts\install-tools.ps1 -InitMcp
  ```

Lệnh này sẽ tự động cài các công cụ giúp AI đọc code chính xác (`agent-lsp`), tra tài liệu mới nhất (`context7`), vẽ bản đồ dự án (`graphify`), quản lý quy trình (`trellis`) và kết nối NotebookLM (`nlm`).

### Bước 2: Đăng nhập NotebookLM (khuyên dùng)

Để AI có thể đọc và ghi chú vào Google NotebookLM của bạn, chạy:

```bash
nlm login
```

Trình duyệt sẽ mở ra để bạn đăng nhập tài khoản Google. Sau khi đăng nhập xong, kiểm tra lại tình trạng toàn bộ công cụ:

```bash
./scripts/install-tools.sh --check
```

### Bước 3: Mở bằng công cụ AI bạn đang dùng

Mở thư mục dự án bằng **Google Antigravity**, **Claude Code**, **VS Code (GitHub Copilot)** hoặc **Codex** — mọi quy tắc, hooks và kỹ năng (skills) đã được cấu hình sẵn để tự chạy.

---

## 2. Áp dụng vào dự án bất kỳ

Bạn không cần copy thủ công từng file. Hãy dùng script có sẵn để gắn toàn bộ framework vào bất kỳ thư mục nào (dự án mới tinh hoặc dự án đang làm dở):

```bash
python3 scripts/apply-template.py /duong/dan/toi/du-an-cua-ban --dev ten_cua_ban
```

**Script này tự động làm giúp bạn:**
1. Tạo thư mục nếu chưa có và copy toàn bộ khung AI sạch sẽ (bỏ qua lịch sử cũ của template).
2. Tự chạy `git init` (nếu thư mục chưa có Git).
3. Tự thêm hồ sơ developer cho bạn (`.trellis/.developer` và `.trellis/workspace/<ten_cua_ban>/`).
4. Nếu dự án đã có sẵn `AGENTS.md`, `.gitignore` hoặc `.mcp.json`, script sẽ **gộp (merge) an toàn** mà không xóa cấu hình cũ của bạn.

**Một số tùy chọn hay dùng:**

```bash
# Xem trước những gì sẽ được tạo/thay đổi mà chưa ghi ra đĩa
python3 scripts/apply-template.py ../my-app --dev alice --dry-run

# Áp dụng + tự tạo commit Git đầu tiên
python3 scripts/apply-template.py ../my-app --dev alice --commit

# Gắn thêm địa chỉ repo template để sau này dễ cập nhật framework
python3 scripts/apply-template.py ../my-app --dev alice --upstream https://github.com/<owner>/trellis-template.git
```

> Sau khi chạy xong, vào thư mục dự án (`cd /duong/dan/toi/du-an-cua-ban`) và bắt đầu chat với AI ngay.

---

## 3. Cách sử dụng hằng ngày

Bạn chỉ cần **chat tự nhiên** với AI, hoặc gõ các lệnh ngắn (slash commands) sau khi muốn AI đi đúng quy trình:

| Khi bạn muốn... | Gõ lệnh hoặc nhắn AI | Kết quả nhận được |
|---|---|---|
| **Bắt đầu làm việc / làm quen dự án** | `/trellis-start` hoặc nhắn *"Kiểm tra trạng thái dự án giúp tôi"* | AI tự đọc trạng thái Git, task đang làm, và notebook dự án |
| **Có ý tưởng mới, chưa rõ làm thế nào** | `/sdlc-discovery` hoặc `/trellis-brainstorm` | AI hỏi từng câu ngắn gọn để chốt phạm vi, kiến trúc và bản thiết kế |
| **Tìm hiểu công nghệ / thư viện mới** | `/research <chủ đề>` | AI tra tài liệu chính chủ (Context7) + lưu tóm tắt vào NotebookLM |
| **Nhờ AI viết code / sửa tính năng** | Chat yêu cầu bình thường | AI tự kiểm tra quy chuẩn dự án, dùng LSP sửa code an toàn và tự chạy test |
| **Kiểm tra lỗi toàn bộ dự án** | `/trellis-check` | AI tự chạy kiểm tra kiểu, lint, unit test và tự sửa nếu có lỗi |
| **Xong việc trong ngày, lưu nhật ký** | `/trellis-finish-work` | AI đóng task, ghi nhật ký làm việc và lưu bài học vào NotebookLM |

### Một ngày làm việc mẫu (không cần nhớ lệnh)
1. Mở AI lên và nhắn: *"Tôi muốn làm tính năng đăng nhập bằng Google cho app này."*
2. AI sẽ chủ động hỏi lại từng câu để chốt yêu cầu (không code bừa), đồng thời tra NotebookLM xem trước đây có ghi chú gì liên quan chưa.
3. Khi bạn duyệt phương án, AI tự viết code, tự kiểm tra lỗi bằng `verify.py` / `agent-lsp` rồi mới báo hoàn thành.
4. Khi xong việc, bạn nhắn *"Chốt công việc hôm nay giúp tôi"* — AI tự lưu nhật ký và tóm tắt quyết định quan trọng vào NotebookLM.

---

## 4. Kết nối & tương tác với NotebookLM (Bộ não dự án) & Graphify

Framework phân tách rõ hai vai trò để AI vừa nhớ lâu vừa chạy nhanh:
- **NotebookLM = Bộ não ghi nhớ mọi thông tin về dự án**: Lưu quyết định kiến trúc, thiết kế tính năng, tài liệu nghiên cứu và bài học sửa lỗi xuyên suốt nhiều phiên làm việc.
- **Graphify = Bản đồ định vị code trực tiếp**: Giúp AI nhảy thẳng tới đúng file, hàm và luồng phụ thuộc cần sửa ngay lập tức mà **không phải hỏi vòng qua NotebookLM**.

### AI tự động tương tác với NotebookLM thế nào?
- **Khi chưa có notebook phù hợp**: Lúc tìm kiếm trên NotebookLM mà chưa thấy notebook nào của dự án, AI sẽ **chủ động hỏi bạn** xem có muốn tạo mới hoặc gắn một notebook sẵn có vào dự án không.
- **Tự động cập nhật khi có thay đổi liên quan**: Sau khi bạn đã gắn notebook cho dự án, mỗi thay đổi về tài liệu, quy chuẩn (`.trellis/spec/`), bản thiết kế (`prd.md`, `design.md`) hoặc module code liên quan sẽ được AI và hook tự động đồng bộ ghi chú lên notebook.
- **Trước khi thiết kế hoặc sửa lỗi khó**: AI tự tra cứu `notebook_list` và `notebook_query` để kế thừa các quyết định trước đó.

### Gắn notebook cho dự án (tùy chọn thủ công)
1. Nếu muốn tạo/gắn sẵn notebook ngay từ đầu:
   ```bash
   nlm list notebooks
   nlm create notebook "Ten Du An Cua Toi"
   nlm alias set project <notebook-id-vua-tao>
   python3 .trellis/scripts/notebook_sync.py --bind project
   ```
2. Trong chat, bạn cũng có thể nhắc trực tiếp bất cứ lúc nào:
   - *"Kiểm tra xem NotebookLM của mình đang có những thông tin gì về phần X?"*
   - *"Lưu tóm tắt phương án này vào NotebookLM giúp tôi."*

---

## 5. Các câu hỏi thường gặp

### Tôi dùng Antigravity, Claude Code hay GitHub Copilot có khác nhau không?
Không cần chỉnh tay. Template đã đồng bộ sẵn cấu hình cho cả **Google Antigravity** (`.agents/`), **Claude Code** (`.claude/`), **GitHub Copilot** (`.github/`) và chuẩn chung [`AGENTS.md`](AGENTS.md).

### Khi AI báo NotebookLM chưa đăng nhập thì làm sao?
Mở terminal và chạy `nlm login` để đăng nhập lại Google. Nếu muốn kiểm tra chi tiết, chạy `nlm doctor`.

### Làm sao cập nhật template lên phiên bản mới mà không mất dữ liệu dự án?
Trong thư mục dự án, chạy:
```bash
python3 .trellis/scripts/update_framework.py --check
python3 .trellis/scripts/update_framework.py
```
Lệnh này chỉ cập nhật phần framework và **tự động giữ nguyên** code, tasks, cấu hình `.trellis/config.yaml` và nhật ký của bạn.

### Muốn xem tài liệu kỹ thuật chi tiết cho từng skill và công cụ?
- Cẩm nang chi tiết 15 skills & quy trình: [USAGE.md](USAGE.md)
- Quy tắc tổng hợp cho AI agents: [AGENTS.md](AGENTS.md)
- Hướng dẫn NotebookLM nâng cao: [.trellis/spec/guides/notebooklm-knowledge-base.md](.trellis/spec/guides/notebooklm-knowledge-base.md)
