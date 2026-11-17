---
name: sdlc-discovery
description: Khởi động quy trình phỏng vấn thích ứng 5 chiều từ mô tả sản phẩm, lựa chọn mô hình SDLC tối ưu và kích hoạt Hội đồng Thẩm định chuyên trách
---

# SDLC Adaptive Discovery & Council Activation

Quy trình này hướng dẫn AI và người dùng khám phá toàn diện bài toán sản phẩm, lựa chọn mô hình phát triển phần mềm và thiết lập hội đồng thẩm định chuyên biệt.

---

## Bước 1: Tiếp nhận Mô tả Sản phẩm
Yêu cầu người dùng cung cấp mô tả sơ bộ về sản phẩm/dự án mong muốn (hoặc tài liệu đính kèm nếu có).
Nếu người dùng đã cung cấp mô tả trong lời nhắc ban đầu, tóm tắt lại các điểm chính.

## Bước 2: Nạp Kỹ năng Chuyên trách
Kích hoạt skill `sdlc-adaptive-discovery`.
Mở và tuân thủ các chỉ dẫn trong:
- `.agents/skills/sdlc-adaptive-discovery/SKILL.md`
- `.agents/skills/sdlc-adaptive-discovery/references/elicitation-interview.md`

## Bước 3: Vận hành Vòng Phỏng vấn 5 Chiều
Thực hiện phỏng vấn từng câu hỏi một (Single-question loop) xoay quanh 5 chiều:
1. Requirement Clarity (1 - 5)
2. Requirement Volatility (1 - 5)
3. Technical Complexity & Risk (1 - 5)
4. Time-to-Market Urgency (1 - 5)
5. Mission-Criticality & Compliance (1 - 5)

Mỗi câu hỏi phải có: Vấn đề cần chốt, Lý do, Khuyến nghị và Đánh đổi.

## Bước 4: Đánh giá & Khuyến nghị Mô hình SDLC
Sử dụng `.agents/skills/sdlc-adaptive-discovery/references/model-decision-matrix.md` để xuất báo cáo lựa chọn mô hình:
- Agile / Scrum
- Waterfall / V-Model
- TDD / Extreme Programming
- Spiral / Risk-Driven R&D
- Kanban

## Bước 5: Kích hoạt Hội đồng Thẩm định (Hybrid Council)
Sau khi người dùng đồng thuận mô hình:
- Kích hoạt bộ quy tắc và nhân sự của Hội đồng tương ứng trong `.agents/skills/sdlc-adaptive-discovery/references/councils/`.
- Áp dụng cổng kiểm duyệt chuyên biệt vào luồng 7 giai đoạn SDLC của dự án.
- Thiết lập báo cáo phản biện bàn tròn (Roundtable Synthesis) tại các mốc chuyển giao.
