# Cẩm nang Phỏng vấn Khai phá Thích ứng (Adaptive Elicitation Guide)

Tài liệu này cung cấp phương pháp luận và bộ câu hỏi phỏng vấn đào sâu nhằm đạt được mức độ hiểu biết lẫn nhau cao nhất (Highest Mutual Understanding) giữa AI và người dùng, trước khi quyết định mô hình phát triển phần mềm và triển khai kỹ thuật.

---

## 1. Nguyên tắc Phỏng vấn Cốt lõi (Core Principles)

1. **Một câu hỏi mỗi lượt (Single-Question Focus)**:
   Không gửi danh sách dồn dập 5-10 câu hỏi khiến người dùng quá tải. Mỗi lượt phản hồi chỉ hỏi đúng **1 quyết định quan trọng nhất** đang cản trở tiến trình.
2. **Kèm theo Khuyến nghị & Đánh đổi (Recommendation & Trade-off)**:
   Mỗi câu hỏi luôn phải bao gồm:
   - *Vấn đề cần quyết định*: Bản chất câu hỏi là gì?
   - *Vì sao cần trả lời*: Câu trả lời ảnh hưởng thế nào đến kiến trúc hoặc quy trình?
   - *Đề xuất khuyến nghị của AI*: Phương án tối ưu dựa trên thực tế dự án.
   - *Đánh đổi (Trade-off)*: Hậu quả hoặc rủi ro nếu người dùng chọn phương án khác.
3. **Lắng nghe tích cực (Active Synthesis)**:
   Trước khi hỏi câu tiếp theo, AI phải tóm tắt ngắn gọn 1 dòng về điều vừa được chốt để xác nhận sự đồng thuận đôi bên.
4. **First-Principles Thinking**:
   Khi người dùng đưa ra một giải pháp công nghệ cụ thể ("Tôi muốn dùng Redis và Microservices"), AI phải truy nguyên về bài toán gốc ("Vấn đề độ trễ hay lưu lượng tải đang gặp phải là gì?") để tránh giải pháp thừa thãi.

---

## 2. Khung Phỏng vấn 5 Chiều Đánh giá (5-Dimensional Rubric)

Quá trình phỏng vấn xoay quanh 5 trục toạ độ xác định bản chất dự án:

### Chiều 1: Độ rõ ràng của Yêu cầu (Requirement Clarity)
*   *Mục đích*: Đo lường xem phạm vi bài toán đã được xác định cụ thể đến đâu.
*   *Thang điểm 1 - 5*:
    *   **1 điểm**: Ý tưởng trừu tượng ("Tôi muốn làm một app AI kết nối mọi người").
    *   **3 điểm**: Đã có danh sách tính năng chính nhưng chưa rõ luồng dữ liệu và trường hợp ngoại lệ (Edge cases).
    *   **5 điểm**: Đã có PRD chi tiết, sơ đồ màn hình, API specs và tiêu chí nghiệm thu rõ ràng.
*   *Câu hỏi mẫu*:
    > "Sản phẩm hiện tại đã có tài liệu đặc tả hoặc giao diện chi tiết chưa, hay chúng ta sẽ cùng định hình các luồng tính năng từ ý tưởng cốt lõi trước?"

### Chiều 2: Độ biến động của Yêu cầu (Requirement Volatility)
*   *Mục đích*: Đo lường khả năng và tần suất thay đổi định hướng do thị trường hoặc phản hồi người dùng.
*   *Thang điểm 1 - 5*:
    *   **1 điểm**: Cố định 100%, có quy định pháp lý hoặc tài liệu đấu thầu không được phép thay đổi.
    *   **3 điểm**: Các module nền tảng cố định, giao diện và logic người dùng có thể điều chỉnh.
    *   **5 điểm**: Thử nghiệm thị trường mới (Product-Market Fit), tính năng thay đổi theo tuần/ngày dựa trên metrics.
*   *Câu hỏi mẫu*:
    > "Trong quá trình xây dựng, bạn dự kiến các tính năng có thay đổi liên tục theo phản hồi người dùng không, hay phạm vi đã được cố định hoàn toàn ngay từ đầu?"

### Chiều 3: Độ phức tạp & Rủi ro Kỹ thuật (Technical Complexity & Risk)
*   *Mục đích*: Đo lường mức độ bất định về công nghệ, thuật toán hoặc tích hợp bên thứ ba.
*   *Thang điểm 1 - 5*:
    *   **1 điểm**: Ứng dụng web/mobile tiêu chuẩn (CRUD, Authentication, REST API, Database phổ thông).
    *   **3 điểm**: Hệ thống phân tán, xử lý bất đồng bộ, streaming real-time hoặc tích hợp nhiều hệ thống legacy.
    *   **5 điểm**: Nghiên cứu R&D, thuật toán đồ họa/AI độc quyền, hệ thống phần cứng/nhúng hoặc giao thức mạng tùy biến.
*   *Câu hỏi mẫu*:
    > "Công nghệ lõi của dự án là các công nghệ phổ biến đã có thư viện chuẩn, hay có phần nào thuộc diện R&D nghiên cứu thuật toán mới chưa chắc chắn khả thi?"

### Chiều 4: Tính cấp thiết về Thời gian (Time-to-Market Urgency)
*   *Mục đích*: Xác định áp lực về deadline ra mắt bản thử nghiệm đầu tiên.
*   *Thang điểm 1 - 5*:
    *   **1 điểm**: Không gấp, chất lượng và tài liệu hoàn hảo quan trọng hơn thời gian.
    *   **3 điểm**: Có hạn mốc cụ thể nhưng đủ thời gian để thiết kế bài bản (2 - 4 tháng).
    *   **5 điểm**: Cực kỳ cấp bách, cần bản chạy được (MVP) trong vài tuần/ngày để gọi vốn hoặc thử thị trường.
*   *Câu hỏi mẫu*:
    > "Mục tiêu ưu tiên số 1 của bạn hiện tại là ra mắt một bản MVP tinh gọn nhanh nhất có thể, hay xây dựng một hệ thống hoàn chỉnh, chuẩn chỉ kiến trúc ngay từ ngày đầu?"

### Chiều 5: Mức độ Nghiêm ngặt & An toàn (Mission-Criticality & Compliance)
*   *Mục đích*: Đánh giá hậu quả nếu phần mềm phát sinh lỗi trên môi trường thực tế.
*   *Thang điểm 1 - 5*:
    *   **1 điểm**: Sản phẩm nội bộ thử nghiệm, ứng dụng giải trí thông thường, lỗi có thể vá sau.
    *   **3 điểm**: Ứng dụng thương mại B2B/B2C, lỗi gây ảnh hưởng trải nghiệm người dùng nhưng không mất dữ liệu tiền bạc.
    *   **5 điểm**: Hệ thống giao dịch tài chính, thanh toán, hồ sơ y tế, điều khiển phần cứng hoặc hạ tầng quan trọng (lỗi có thể dẫn đến kiện tụng pháp lý hoặc mất mát tài sản lớn).
*   *Câu hỏi mẫu*:
    > "Sản phẩm có yêu cầu tuân thủ các quy chuẩn bảo mật nghiêm ngặt (như GDPR, PCI-DSS, HIPAA) hoặc xử lý tiền bạc, dữ liệu nhạy cảm không?"

---

## 3. Quy trình Hội tụ (Convergence Protocol)

Sau khi hoàn tất phỏng vấn (thường từ 2 - 4 lượt hỏi đáp), AI tiến hành:
1. **Lập Bảng Điểm 5 Chiều (Spider / Radar Score)**.
2. **Chiếu vào Ma trận Lựa chọn Mô hình (Model Decision Matrix)**.
3. **Xuất Báo cáo Khuyến nghị (Recommendation Brief)** gồm:
   - Mô hình phát triển được chọn và lý do định lượng.
   - Hội đồng Thẩm định Chuyên trách được kích hoạt.
   - Cổng kiểm duyệt đầu tiên cần vượt qua.
