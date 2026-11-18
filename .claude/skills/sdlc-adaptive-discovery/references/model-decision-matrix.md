# Ma trận Quyết định Mô hình SDLC (Model Decision Matrix)

Tài liệu này cung cấp công thức tính điểm định lượng và cây quyết định (Decision Tree) giúp lựa chọn mô hình phát triển phần mềm tối ưu dựa trên kết quả phỏng vấn 5 chiều.

---

## 1. Bảng Trọng số & Tiêu chí Lựa chọn Mô hình

| Mô hình SDLC | Clarity | Volatility | Complexity | Time-to-Market | Criticality | Động lực Cốt lõi |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Agile / Scrum** | 1 - 3 | 4 - 5 | 1 - 3 | 4 - 5 | 1 - 3 | Thích ứng nhanh, ra mắt MVP sớm, nhận phản hồi thực tế liên tục theo Sprint. |
| **Kanban / Flow** | 2 - 4 | 3 - 5 | 1 - 3 | 3 - 5 | 1 - 3 | Luồng công việc liên tục, bảo trì sản phẩm có sẵn, tối ưu hóa thời gian hoàn thành task. |
| **Waterfall / V-Model** | 4 - 5 | 1 - 2 | 2 - 4 | 1 - 2 | 4 - 5 | Rủi ro pháp lý/tài chính cao, yêu cầu cố định, kiểm thử xác minh đối xứng chặt chẽ. |
| **TDD / Extreme Programming** | 3 - 5 | 2 - 4 | 3 - 4 | 2 - 3 | 4 - 5 | Chất lượng mã nguồn tuyệt đối, hệ thống lõi phức tạp, kiểm thử tự động 100%. |
| **Spiral / Risk-Driven R&D** | 1 - 2 | 3 - 5 | 4 - 5 | 1 - 3 | 3 - 5 | Bất định công nghệ lớn, thuật toán mới, cần làm nhiều prototype giải quyết rủi ro trước. |

---

## 2. Cây Quyết định (Decision Tree Algorithm)

```
                            [Đánh giá Điểm 5 Chiều]
                                       │
                  ┌────────────────────┴────────────────────┐
     Criticality >= 4?                          Criticality <= 3?
           │                                          │
    ┌──────┴──────┐                            ┌──────┴──────┐
Volatility <= 2? Volatility >= 3?       Complexity >= 4? Complexity <= 3?
    │             │                            │             │
[Waterfall]  [TDD / XP]                   [Spiral / R&D]   Time-to-Market >= 4?
                                                                 │
                                                       ┌─────────┴─────────┐
                                                  Clarity <= 3?      Clarity >= 4?
                                                       │                   │
                                                  [Agile/Scrum]        [Kanban]
```

### Chi tiết các Quy tắc Logic:

1. **Quy tắc 1 (Hệ thống Trọng yếu - Mission-Critical Core)**:
   - Nếu `Criticality >= 4` VÀ `Volatility <= 2`: Chọn **Waterfall / V-Model**.
   - *Lý do*: Lỗi gây hậu quả lớn và yêu cầu không đổi, cần đầu tư đặc tả kỹ thuật và kiến trúc đối xứng trước khi viết dòng code đầu tiên.

2. **Quy tắc 2 (Chất lượng Tuyệt đối & Module Lõi - Software Craftsmanship)**:
   - Nếu `Criticality >= 4` VÀ `Volatility >= 3`: Chọn **TDD / Extreme Programming (XP)**.
   - *Lý do*: Yêu cầu có sự biến động nhưng không được phép có bug; TDD đảm bảo test harness an toàn cho việc refactor liên tục.

3. **Quy tắc 3 (Nghiên cứu Công nghệ & Đổi mới - R&D Innovation)**:
   - Nếu `Complexity >= 4` VÀ `Clarity <= 2`: Chọn **Spiral / Risk-Driven R&D**.
   - *Lý do*: Dự án nhiều rủi ro kỹ thuật chưa rõ khả thi; chia nhỏ thành các vòng lặp thử nghiệm (Proof-of-Concept) để triệt tiêu rủi ro lớn nhất trước.

4. **Quy tắc 4 (Sản phẩm Khởi nghiệp & Ra mắt Nhanh - Speed to Market)**:
   - Nếu `Time-to-Market >= 4` VÀ `Clarity <= 3`: Chọn **Agile / Scrum**.
   - *Lý do*: Cần đưa MVP ra thị trường nhanh nhất, chia nhỏ backlog thành các sprint 1-2 tuần để người dùng trải nghiệm thực tế.

5. **Quy tắc 5 (Tối ưu Luồng Vận hành & Cải tiến - Continuous Flow)**:
   - Nếu dự án là nâng cấp hệ thống đã có, task nhỏ lẻ liên tục hoặc đội ngũ bảo trì: Chọn **Kanban**.

---

## 3. Bản Mẫu Báo cáo Kết quả (Output Format)

Khi AI hoàn thành phân tích, báo cáo đề xuất phải được định dạng như sau:

```markdown
### Kết quả Phân tích Dự án & Lựa chọn Mô hình SDLC

*   **Bảng điểm Đánh giá**:
    - Requirement Clarity: [X]/5
    - Requirement Volatility: [X]/5
    - Technical Complexity: [X]/5
    - Time-to-Market Urgency: [X]/5
    - Mission-Criticality: [X]/5

*   **Mô hình Phát triển Được chọn**: **[Tên Mô hình, ví dụ: Agile / Scrum]**
*   **Lý do lựa chọn**: [Phân tích ngắn gọn dựa trên bảng điểm]
*   **Hội đồng Chuyên trách Được kích hoạt**: **[Tên Hội đồng, ví dụ: Agile Product Council]**
*   **Quy tắc Cổng Kiểm duyệt (First Review Gate)**: [Yêu cầu cần hoàn thành để vượt qua Phase tiếp theo]
```
