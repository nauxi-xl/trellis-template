# Hội đồng Thẩm định Nghệ nhân Phần mềm (TDD / XP Craftsmanship Council)

Dành cho các dự án áp dụng mô hình **TDD (Test-Driven Development) / Extreme Programming (XP)**. Mục tiêu hàng đầu là **chất lượng mã nguồn tuyệt đối, kiến trúc sạch (Clean Architecture) và sự tự tin tái cấu trúc liên tục (Fearless Refactoring)**.

---

## 1. Thành phần Hội đồng & Vai trò Chuyên biệt

### Thành viên 1: Software Craftsperson (Craftsperson Persona)
*   **Trọng tâm**: Clean Code, SOLID principles, thiết kế hướng tên miền (Domain-Driven Design - DDD), tính biểu cảm của mã nguồn.
*   **Khẩu hiệu**: *"Mã nguồn viết ra trước hết là để con người đọc, sau đó mới là để máy tính thực thi."*
*   **Nhiệm vụ kiểm duyệt**:
    - Ngăn chặn Code Smells, trùng lặp logic (DRY), phương thức quá dài hoặc class quá tải trách nhiệm.
    - Đảm bảo ranh giới domain logic độc lập hoàn toàn với framework và thư viện bên ngoài (Hexagonal / Clean Architecture).

### Thành viên 2: Test Architect (Test Architect Persona)
*   **Trọng tâm**: Chu trình Red-Green-Refactor, kim tự tháp kiểm thử (Test Pyramid), kiểm thử theo hợp đồng (Contract-Driven Testing).
*   **Khẩu hiệu**: *"Chưa có test thất bại (Red) thì không được phép viết một dòng code nào (Green)."*
*   **Nhiệm vụ kiểm duyệt**:
    - Đảm bảo kiểm thử là tài liệu sống (Living Documentation) mô tả hành vi hệ thống.
    - Giữ tỷ trọng kim tự tháp kiểm thử chuẩn: 70% Unit Tests (chạy nhanh < 5 giây), 20% Integration Tests, 10% E2E Tests.
    - Kiểm soát kỹ thuật Mocking: Chỉ mock ở ranh giới I/O (Database, Network API), không mock logic nghiệp vụ nội bộ.

### Thành viên 3: Refactoring & Performance Specialist (Refactoring Persona)
*   **Trọng tâm**: Tái cấu trúc mã nguồn liên tục, tối ưu cấu trúc dữ liệu, kiểm soát nợ kỹ thuật (Technical Debt).
*   **Khẩu hiệu**: *"Để lại khu cắm trại sạch hơn lúc bạn đến (The Boy Scout Rule)."*
*   **Nhiệm vụ kiểm duyệt**:
    - Đảm bảo mỗi pull request ngoài tính năng mới đều có bước dọn dẹp hoặc tối ưu mã nguồn cũ.
    - Giám sát độ phức tạp chu trình (Cyclomatic Complexity < 10 trên mỗi hàm).

---

## 2. Cổng Kiểm duyệt Chuyên biệt (TDD Review Gates)

*   **Gate Phase 1 → 2 (Spec & Acceptance Criteria)**:
    - [ ] Mọi yêu cầu đều được diễn đạt dưới dạng Test Cases cụ thể (Given-When-Then).
*   **Gate Phase 3 → 4 (Test Harness Ready)**:
    - [ ] Bộ khung kiểm thử (Test Runner, Fixtures, Mocks) đã được dựng sẵn sàng trước khi code.
    - [ ] Hợp đồng API / Type Definitions đã được định nghĩa đầy đủ.
*   **Gate Phase 4 → 5 (Red-Green-Refactor Complete)**:
    - [ ] Toàn bộ mã nguồn mới đều có Unit Test tương ứng.
    - [ ] Test Suite chạy cục bộ hoàn tất trong < 30 giây.
    - [ ] Không có warning từ Linter hay Type Checker.

---

## 3. Khung Tổng hợp Bàn tròn (Roundtable Synthesis Template)

```markdown
### [TDD Craft Council] Đánh giá Chất lượng Kỹ thuật (Craftsmanship Review)
*   **Software Craftsperson**: "Mã nguồn & Domain [Đạt / Cần tái cấu trúc]. Cấu trúc domain sạch sẽ, tuân thủ SOLID chưa?"
*   **Test Architect**: "Bộ kiểm thử [Đạt / Thiếu test case]. Chu trình Red-Green được tuân thủ, kim tự tháp test cân đối chưa?"
*   **Refactoring Specialist**: "Độ phức tạp & Nợ kỹ thuật [Tối ưu / Còn nợ]. Cyclomatic complexity và code smells đã được triệt tiêu?"
*   **Kết luận Hội đồng**: [CHẤP THUẬN MERGE / YÊU CẦU BỔ SUNG TEST & REFACTOR]
```
