---
name: sdlc-adaptive-discovery
description: "Phân tích mô tả sản phẩm của người dùng, thực hiện chu trình phỏng vấn đào sâu 5 chiều để đồng thuận yêu cầu, lựa chọn mô hình phát triển phần mềm tối ưu (Agile, Waterfall, TDD, Spiral, Kanban), kích hoạt Hội đồng Thẩm định chuyên trách (Agent Council) và điều phối toàn diện 7 giai đoạn SDLC."
---

# SDLC Adaptive Discovery & Council Orchestration

Kỹ năng này điều phối toàn bộ quy trình từ ý tưởng sản phẩm ban đầu đến khi hoàn thiện sản phẩm thông qua **7 giai đoạn SDLC tiêu chuẩn**, kết hợp chu trình **phỏng vấn thích ứng 5 chiều** và **Hội đồng Thẩm định Chuyên trách (Specialized Councils)** theo cơ chế Hybrid.

---

## Khi nào nên sử dụng Kỹ năng này?

*   Người dùng đưa ra một mô tả sản phẩm mới, ý tưởng khởi nghiệp, hoặc dự án phần mềm mới nhưng chưa rõ nên áp dụng quy trình phát triển nào.
*   Cần một chu trình phỏng vấn chuyên sâu (Interactive Elicitation) từng câu hỏi một để đạt mức độ thấu hiểu lẫn nhau cao nhất trước khi bắt tay vào lập trình.
*   Muốn có một Hội đồng Thẩm định AI (Product Lead, System Architect, QA/Security Lead...) phản biện đa chiều và kiểm soát chất lượng qua từng cổng kiểm duyệt.
*   Khi người dùng chạy slash command `/sdlc-discovery` hoặc yêu cầu *"phân tích mô tả sản phẩm và chọn mô hình SDLC"*.

---

## Quy trình Thực hiện 4 Bước

### Bước 1: Tiếp nhận & Phân tích Sơ bộ Mô tả Sản phẩm
1. Đọc kỹ mô tả sản phẩm của người dùng (ý tưởng, tài liệu sơ bộ, tính năng mong muốn).
2. Tách bạch các thông tin đã rõ ràng và các giả định còn mơ hồ.
3. Tham chiếu tài liệu quy chuẩn [7 Giai đoạn SDLC](./references/sdlc-7-phases.md) để xác định điểm bắt đầu (thường là Giai đoạn 1: Khảo sát & Khám phá).

### Bước 2: Chu trình Phỏng vấn Thích ứng 5 Chiều (Elicitation Loop)
Vận hành theo nguyên tắc trong [Cẩm nang Phỏng vấn Thích ứng](./references/elicitation-interview.md):
*   **Chỉ hỏi đúng 1 câu hỏi trọng tâm mỗi lượt**: Không gửi danh sách dồn dập.
*   **Cấu trúc mỗi câu hỏi**:
    - *Vấn đề cần quyết định*: Bản chất câu hỏi.
    - *Vì sao cần trả lời*: Ảnh hưởng tới kiến trúc/quy trình.
    - *Khuyến nghị của AI*: Đề xuất phương án tối ưu.
    - *Đánh đổi (Trade-off)*: Rủi ro nếu chọn phương án khác.
*   **Đào sâu qua 5 trục toạ độ**:
    1. *Requirement Clarity* (Độ rõ ràng của yêu cầu: 1 - 5 điểm)
    2. *Requirement Volatility* (Độ biến động theo thị trường: 1 - 5 điểm)
    3. *Technical Complexity & Risk* (Độ phức tạp & rủi ro công nghệ: 1 - 5 điểm)
    4. *Time-to-Market Urgency* (Tính cấp thiết về thời gian ra mắt: 1 - 5 điểm)
    5. *Mission-Criticality & Compliance* (Mức độ an toàn & tuân thủ: 1 - 5 điểm)

### Bước 3: Đánh giá Điểm & Tư vấn Mô hình SDLC
1. Áp dụng thuật toán cây quyết định trong [Ma trận Quyết định Mô hình SDLC](./references/model-decision-matrix.md).
2. Xác định mô hình phát triển phần mềm tối ưu:
   *   **Agile / Scrum**: Thích ứng nhanh, làm MVP sớm theo Sprint.
   *   **Kanban / Flow**: Tối ưu luồng công việc liên tục, nâng cấp/bảo trì.
   *   **Waterfall / V-Model**: Hệ thống an toàn/tài chính, yêu cầu cố định, kiểm thử đối xứng chặt chẽ.
   *   **TDD / Extreme Programming (XP)**: Mã nguồn sạch, kiến trúc DDD, test automation 100%.
   *   **Spiral / Risk-Driven R&D**: Nghiên cứu công nghệ mới/AI, triệt tiêu rủi ro qua các vòng PoC.
3. Xuất báo cáo khuyến nghị và chờ người dùng đồng thuận lựa chọn.

### Bước 4: Kích hoạt Hội đồng Thẩm định & Vận hành 7 Giai đoạn SDLC
Sau khi người dùng đồng thuận mô hình, kích hoạt Hội đồng Thẩm định chuyên trách tương ứng:
*   [Hội đồng Agile](./references/councils/agile-council.md): Product Owner, Scrum Architect, QA Lead.
*   [Hội đồng Waterfall / V-Model](./references/councils/waterfall-council.md): Systems Architect, Compliance Officer, Safety QA Auditor.
*   [Hội đồng TDD / XP Craftsmanship](./references/councils/tdd-craft-council.md): Software Craftsperson, Test Architect, Refactoring Specialist.
*   [Hội đồng Spiral / Risk R&D](./references/councils/spiral-risk-council.md): R&D Lead, PoC Evaluator, Risk Manager.

**Cơ chế Vận hành Hybrid**:
*   *Review Gates*: Gắn các tiêu chí nghiệm thu chuyên biệt của hội đồng vào từng giai đoạn trong 7 quy trình SDLC.
*   *Roundtable Synthesis*: Tại các mốc chuyển tiếp (hoàn thành PRD, hoàn thành Architecture, trước khi Release), các chuyên gia trong hội đồng xuất báo cáo nhận xét đa chiều để người dùng xem xét và phê duyệt.

---

## Tài liệu Tham chiếu (References)

*   [7 Giai đoạn Phát triển Phần mềm Toàn diện](./references/sdlc-7-phases.md)
*   [Cẩm nang Phỏng vấn Khai phá Thích ứng](./references/elicitation-interview.md)
*   [Ma trận Quyết định Mô hình SDLC](./references/model-decision-matrix.md)
*   [Hội đồng Thẩm định Agile](./references/councils/agile-council.md)
*   [Hội đồng Thẩm định Waterfall / V-Model](./references/councils/waterfall-council.md)
*   [Hội đồng Thẩm định TDD / Craftsmanship](./references/councils/tdd-craft-council.md)
*   [Hội đồng Thẩm định Spiral / Risk R&D](./references/councils/spiral-risk-council.md)
