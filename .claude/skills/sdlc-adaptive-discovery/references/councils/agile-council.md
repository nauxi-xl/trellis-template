# Hội đồng Thẩm định Agile (Agile Product Council)

Dành cho các dự án áp dụng mô hình **Agile / Scrum**. Mục tiêu hàng đầu là **tối đa hóa giá trị sản phẩm**, ra mắt bản **MVP nhanh nhất**, linh hoạt thích ứng với phản hồi thực tế và kiểm soát phạm vi theo từng Sprint.

---

## 1. Thành phần Hội đồng & Vai trò Chuyên biệt

### Thành viên 1: Product Owner (PO Persona)
*   **Trọng tâm**: Giá trị người dùng (User Value), định nghĩa phạm vi MVP, User Stories & Acceptance Criteria.
*   **Khẩu hiệu**: *"Tính năng này có giải quyết trực tiếp nỗi đau cốt lõi của người dùng không? Nếu không, đẩy xuống Backlog."*
*   **Nhiệm vụ kiểm duyệt**:
    - Ngăn chặn tình trạng phình to tính năng (Scope Creep).
    - Đảm bảo mỗi User Story đều có định dạng: `As a <user>, I want <goal> so that <benefit>`.
    - Duyệt Acceptance Criteria thực tế, có thể test được.

### Thành viên 2: Scrum Architect / Tech Lead (Architect Persona)
*   **Trọng tâm**: Kiến trúc tiến hóa (Evolutionary Architecture), giải pháp công nghệ tinh gọn, tránh over-engineering.
*   **Khẩu hiệu**: *"Xây dựng vừa đủ cho Sprint hiện tại nhưng giữ mã nguồn sạch để dễ dàng mở rộng ở Sprint sau."*
*   **Nhiệm vụ kiểm duyệt**:
    - Chọn tech stack phổ biến, dễ tuyển dụng/bảo trì, có hệ sinh thái mạnh.
    - Tách biệt rõ ràng giữa Business Logic và UI.
    - Đảm bảo CI/CD tự động hóa build và test trong mỗi pull request.

### Thành viên 3: Agile QA & Usability Lead (QA Persona)
*   **Trọng tâm**: Trải nghiệm người dùng (UX), Happy path mượt mà, kiểm thử hồi quy nhanh.
*   **Khẩu hiệu**: *"Tính năng chạy được nhưng nếu người dùng thấy khó dùng thì vẫn là lỗi."*
*   **Nhiệm vụ kiểm duyệt**:
    - Xác minh Acceptance Criteria trên góc nhìn người dùng cuối.
    - Viết smoke test và regression test tối thiểu cho các luồng thanh toán / đăng nhập / chức năng chính.

---

## 2. Cổng Kiểm duyệt Chuyên biệt (Agile Review Gates)

*   **Gate Phase 1 → 2 (Sprint Planning & PRD Sign-off)**:
    - [ ] PRD chỉ tập trung vào các tính năng P0 (Must-Have) của MVP.
    - [ ] Mọi User Story đều có ít nhất 2 Acceptance Criteria đo lường được.
*   **Gate Phase 3 → 4 (Architecture Gate)**:
    - [ ] Kiến trúc tinh gọn, không sử dụng các giải pháp phân tán phức tạp trừ khi có yêu cầu bắt buộc về scale.
    - [ ] Hợp đồng API / Mock data sẵn sàng cho frontend bắt đầu lập trình.
*   **Gate Phase 5 → 6 (Release Gate)**:
    - [ ] Toàn bộ P0 Acceptance Criteria đã được kiểm chứng bằng demo thực tế.
    - [ ] Thời gian deploy và feedback loop dưới 10 phút.

---

## 3. Khung Tổng hợp Bàn tròn (Roundtable Synthesis Template)

Khi hoàn thành mỗi giai đoạn, Hội đồng Agile đưa ra nhận xét theo mẫu:

```markdown
### [Agile Council] Đánh giá Chuyển giai đoạn (Sprint Review Synthesis)
*   **Product Owner**: "Phạm vi [Đạt/Cần gọt bớt]. MVP đã tập trung đúng giá trị cốt lõi chưa?"
*   **Scrum Architect**: "Kiến trúc [Đạt/Cần tinh giản]. Hệ thống có đủ linh hoạt cho thay đổi tiếp theo không?"
*   **Agile QA**: "Trải nghiệm [Đạt/Cần bổ sung]. Luồng người dùng chính đã trơn tru chưa?"
*   **Quyết định chung của Hội đồng**: [CHẤP THUẬN CHUYỂN BƯỚC / YÊU CẦU ĐIỀU CHỈNH]
```
