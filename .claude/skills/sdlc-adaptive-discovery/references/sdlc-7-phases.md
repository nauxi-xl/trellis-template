# 7 Giai đoạn Phát triển Phần mềm Toàn diện (SDLC Framework)

Tài liệu này định nghĩa chuẩn mực 7 giai đoạn trong Vòng đời Phát triển Phần mềm (Software Development Life Cycle - SDLC). Mỗi giai đoạn đều quy định rõ **Mục tiêu**, **Đầu vào**, **Sản phẩm bàn giao (Deliverables)** và **Cổng kiểm duyệt (Quality Gate)** trước khi chuyển tiếp.

---

## Giai đoạn 1: Khảo sát & Khám phá (Discovery & Feasibility)

*   **Mục tiêu**: Bóc tách bài toán thực tế, xác định mục đích kinh doanh, chân dung người dùng (User Persona), giá trị cốt lõi và đánh giá tính khả thi về công nghệ / tài nguyên.
*   **Đầu vào**: Ý tưởng ban đầu, mô tả nghiệp vụ của khách hàng, tài liệu khảo sát thị trường hoặc yêu cầu bài toán.
*   **Sản phẩm bàn giao (Deliverables)**:
    *   Bản tóm tắt định vị sản phẩm (Product Brief / Vision Statement).
    *   Phân tích tính khả thi kỹ thuật (Technical Feasibility Report) & danh mục rủi ro sơ bộ.
    *   Mô hình SDLC đề xuất phù hợp với dự án.
*   **Cổng kiểm duyệt (Gate 1 Exit)**:
    *   Mục tiêu và bài toán cốt lõi được định nghĩa rõ ràng trong 1-2 câu.
    *   Không còn giả định kỹ thuật bị mơ hồ làm ảnh hưởng đến khả năng thực thi.
    *   Người dùng / Product Owner phê duyệt định hướng sản phẩm.

---

## Giai đoạn 2: Phân tích & Đặc tả Yêu cầu (Analysis & Requirements Spec)

*   **Mục tiêu**: Chuyển đổi định hướng sơ bộ thành hệ thống yêu cầu chức năng (Functional Requirements) và phi chức năng (Non-Functional Requirements) rõ ràng, có thể đo lường và kiểm thử được.
*   **Đầu vào**: Product Brief từ Giai đoạn 1.
*   **Sản phẩm bàn giao (Deliverables)**:
    *   Tài liệu Yêu cầu Sản phẩm (PRD - Product Requirements Document).
    *   Danh sách User Stories kèm Tiêu chí chấp nhận (Acceptance Criteria - Gherkin / Given-When-Then hoặc Checklist).
    *   Phạm vi rõ ràng: Những gì nằm trong phạm vi (In-Scope) và ngoài phạm vi (Out-of-Scope) của phiên bản mục tiêu (MVP / V1).
*   **Cổng kiểm duyệt (Gate 2 Exit)**:
    *   Toàn bộ Acceptance Criteria có thể kiểm chứng được bằng kiểm thử tự động hoặc kiểm thử thủ công cụ thể.
    *   Hội đồng thẩm định ký duyệt PRD (Sign-off).

---

## Giai đoạn 3: Thiết kế Hệ thống & Giao diện (Architecture & UI/UX Design)

*   **Mục tiêu**: Kiến trúc hóa giải pháp kỹ thuật, thiết kế luồng dữ liệu, hợp đồng giao tiếp (API Contracts), cấu trúc cơ sở dữ liệu và trải nghiệm người dùng trực quan.
*   **Đầu vào**: PRD và Acceptance Criteria từ Giai đoạn 2.
*   **Sản phẩm bàn giao (Deliverables)**:
    *   Tài liệu Thiết kế Kỹ thuật (Technical Design Document - `design.md`): Sơ đồ kiến trúc (C4 model / High-level architecture).
    *   Mô hình dữ liệu (Data Schema / ERD / Migrations draft).
    *   Hợp đồng API (OpenAPI spec / GraphQL schema / RPC contracts).
    *   Wireframe hoặc Thiết kế giao diện (UI/UX Mockups / Component specs).
*   **Cổng kiểm duyệt (Gate 3 Exit)**:
    *   Kiến trúc module độc lập, phân tách ranh giới rõ ràng (Separation of Concerns).
    *   Đã xác định các điểm nghẽn hiệu năng, bảo mật và kế hoạch rollback nếu có sự cố.
    *   Hội đồng kỹ thuật (Architect & Tech Lead) phê duyệt thiết kế.

---

## Giai đoạn 4: Lập trình & Hiện thực hóa (Implementation & Coding)

*   **Mục tiêu**: Hiện thực hóa thiết kế thành mã nguồn có thể thực thi, tuân thủ nghiêm ngặt các quy chuẩn viết code (Coding Guidelines) và kiến trúc đã thống nhất.
*   **Đầu vào**: `design.md`, API contracts, specs và checklist thực hiện (`implement.md`).
*   **Sản phẩm bàn giao (Deliverables)**:
    *   Mã nguồn hoàn chỉnh chia theo các commit nguyên tử (Atomic commits).
    *   Unit Tests đi kèm mã nguồn (đạt ngưỡng coverage quy định).
    *   Tài liệu hướng dẫn cài đặt và cấu hình cục bộ.
*   **Cổng kiểm duyệt (Gate 4 Exit)**:
    *   Mã nguồn vượt qua toàn bộ linter và type checker (Static analysis: 0 errors).
    *   100% Unit Tests vượt qua thành công.
    *   Code review hoàn tất bởi ít nhất một thành viên trong Hội đồng kỹ thuật.

---

## Giai đoạn 5: Kiểm thử & Đảm bảo Chất lượng (Quality Verification & Testing)

*   **Mục tiêu**: Xác minh toàn diện độ tin cậy, tính tương thích, độ an toàn và việc đáp ứng đúng các tiêu chí nghiệm thu đã cam kết trong PRD.
*   **Đầu vào**: Mã nguồn đã qua Unit Test, môi trường Staging/Testbed.
*   **Sản phẩm bàn giao (Deliverables)**:
    *   Bộ kiểm thử tích hợp (Integration Tests) và kiểm thử đầu cuối (E2E Tests).
    *   Báo cáo kiểm thử bảo mật & quét lỗ hổng (Security & Vulnerability scan).
    *   Báo cáo kiểm thử hiệu năng / tải (nếu hệ thống yêu cầu).
    *   Biên bản nghiệm thu chất lượng (QA Sign-off Report).
*   **Cổng kiểm duyệt (Gate 5 Exit)**:
    *   Không còn lỗi nghiêm trọng (Blocker/Critical bugs = 0).
    *   Toàn bộ Acceptance Criteria trong PRD được verify thành công.

---

## Giai đoạn 6: Đóng gói & Triển khai Phát hành (Deployment & Release)

*   **Mục tiêu**: Đóng gói phần mềm an toàn, tự động hóa quy trình phát hành lên môi trường Staging/Production và đảm bảo khả năng khôi phục nhanh nếu xảy ra sự cố.
*   **Đầu vào**: Mã nguồn đã được QA nghiệm thu, artifact build.
*   **Sản phẩm bàn giao (Deliverables)**:
    *   Cấu hình đóng gói (Dockerfile, Container images, Helm charts hoặc Build distribution).
    *   CI/CD pipeline scripts (GitHub Actions, GitLab CI, v.v.).
    *   Kế hoạch phát hành & Kế hoạch Rollback (Release & Rollback Playbook).
    *   Release Notes / Changelog ghi nhận các thay đổi.
*   **Cổng kiểm duyệt (Gate 6 Exit)**:
    *   Triển khai thử nghiệm thành công trên môi trường Staging.
    *   Quy trình Rollback đã được kiểm tra (Dry-run) và sẵn sàng kích hoạt trong < 5 phút.
    *   Hội đồng phát hành đồng thuận mở cổng Production.

---

## Giai đoạn 7: Vận hành, Giám sát & Tiến hóa (Operations, Monitoring & Evolution)

*   **Mục tiêu**: Đảm bảo hệ thống hoạt động ổn định, liên tục trên môi trường thực tế; thu thập dữ liệu vận hành để phát hiện sớm sự cố và nuôi dưỡng vòng lặp cải tiến tiếp theo.
*   **Đầu vào**: Hệ thống đang chạy trên Production.
*   **Sản phẩm bàn giao (Deliverables)**:
    *   Hệ thống Dashboard giám sát (Monitoring metrics: CPU, Memory, Latency, Error Rate).
    *   Quy trình cảnh báo (Alerting rules) và xử lý sự cố (Incident Response Runbook).
    *   Nhật ký phiên & Báo cáo hồi cứu (Session Journal / Retrospective log).
*   **Cổng kiểm duyệt (Gate 7 Exit / Vòng lặp mới)**:
    *   SLA / SLO hệ thống đạt chỉ tiêu cam kết.
    *   Các phản hồi hoặc phát hiện mới được phân loại và đưa vào Backlog cho Giai đoạn 1 của chu kỳ tiếp theo.
