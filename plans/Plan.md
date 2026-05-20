# Kế hoạch xây dựng web tối ưu lộ trình cho shipper

## 1. Mục tiêu
Xây dựng một web đơn giản theo đúng ý trong slide:
- Người dùng mở web và nhìn thấy bản đồ
- Người dùng click để chọn các điểm trên bản đồ
- Người dùng bấm nút để gửi các điểm đã chọn lên backend
- Backend chạy thuật toán tối ưu lộ trình
- Frontend hiển thị lại tuyến đường tối ưu trên bản đồ

Mục tiêu ưu tiên là **dễ làm, dễ hiểu, phù hợp cho sinh viên mới bắt đầu**.

## 2. Phạm vi tối thiểu cần làm
### Làm trước những phần quan trọng nhất
- Hiển thị bản đồ OpenStreetMap
- Cho phép click để chọn nhiều điểm
- Hiển thị marker cho các điểm đã chọn
- Có nút để gửi dữ liệu lên backend
- Backend nhận danh sách điểm và trả về lộ trình tối ưu
- Vẽ lộ trình tối ưu lên bản đồ

### Chưa làm ở giai đoạn đầu
- Đăng nhập, đăng ký
- Lưu lịch sử người dùng
- Phân quyền
- Giao diện quá phức tạp
- Tính năng nâng cao như gợi ý thời gian giao hàng, tối ưu theo nhiều ràng buộc

## 3. Tech stack đề xuất
Mình chọn stack đơn giản và phổ biến nhất theo slide:

### Frontend
- **ReactJS**: dễ tách component, dễ học, dễ làm giao diện
- **Vite**: tạo project nhanh, chạy nhẹ
- **Leaflet**: thư viện bản đồ đơn giản, dễ dùng với OpenStreetMap
- **OpenStreetMap**: nền bản đồ miễn phí
- **Axios**: gọi API từ frontend sang backend

### Backend
- **Java Spring Boot**: đúng với gợi ý trong slide, phổ biến cho web backend
- **REST API**: kiểu API đơn giản, dễ kết nối với frontend
- **Spring Web**: tạo các endpoint nhận và trả dữ liệu JSON

### Thuật toán
- Bắt đầu bằng cách làm **thuật toán tối ưu tuyến đơn giản nhất**
- Nếu muốn dễ hơn cho bản đầu tiên: dùng **nearest neighbor** hoặc một cách xấp xỉ đơn giản
- Nếu thầy yêu cầu đúng bài toán TSP: có thể nâng cấp sau sang **backtracking / branch and bound** tùy số điểm

### Công cụ hỗ trợ
- **VS Code**: viết code
- **Git**: lưu phiên bản code
- **Postman**: test API backend trước khi nối frontend

## 4. Kiến trúc hệ thống
```mermaid
flowchart LR
    User[Người dùng] --> FE[Frontend React + Leaflet]
    FE --> API[Backend Spring Boot REST API]
    API --> Algo[Thuật toán tối ưu tuyến]
    Algo --> API
    API --> FE
    FE --> Map[Hiển thị tuyến trên bản đồ]
```

## 5. Luồng hoạt động của web
1. Người dùng mở trang web
2. Bản đồ hiện ra
3. Người dùng click để chọn các điểm cần đi qua
4. Frontend lưu danh sách tọa độ các điểm
5. Người dùng bấm nút **Tối ưu lộ trình**
6. Frontend gửi danh sách điểm lên backend qua API
7. Backend xử lý thuật toán tối ưu tuyến
8. Backend trả về thứ tự các điểm và đường đi tối ưu
9. Frontend vẽ lại đường đi trên bản đồ
10. Hiển thị thêm tổng quãng đường nếu có

## 6. Danh sách API dự kiến
### API chính
- `POST /api/route/optimize`

### Dữ liệu gửi lên
- Danh sách các điểm đã chọn
- Mỗi điểm gồm latitude và longitude

### Dữ liệu trả về
- Thứ tự các điểm cần đi qua
- Tổng quãng đường
- Dữ liệu để vẽ đường polyline

## 7. Các bước triển khai
### Bước 1: Tạo giao diện bản đồ
- Tạo trang web cơ bản
- Hiển thị bản đồ OpenStreetMap bằng Leaflet
- Cho click để thêm marker

### Bước 2: Tạo backend API mẫu
- Tạo Spring Boot project
- Viết API `POST /api/route/optimize`
- Ban đầu trả dữ liệu mẫu để kiểm tra frontend

### Bước 3: Làm thuật toán tối ưu tuyến
- Nhận danh sách điểm
- Tính thứ tự đi qua các điểm
- Trả về kết quả đơn giản, dễ hiểu

### Bước 4: Nối frontend với backend
- Frontend gửi điểm đã chọn lên backend
- Backend trả kết quả thật
- Frontend vẽ đường tối ưu lên bản đồ

### Bước 5: Hoàn thiện giao diện
- Thêm nút xóa điểm
- Thêm nút làm lại
- Hiển thị tổng quãng đường
- Kiểm tra lại trải nghiệm người dùng

## 8. Cấu trúc thư mục gợi ý
```text
project/
├── frontend/
│   ├── src/
│   └── package.json
├── backend/
│   ├── src/main/java/
│   └── pom.xml
└── plans/
    └── Plan.md
```

## 9. Nguyên tắc làm cho người mới bắt đầu
- Làm từng phần nhỏ, không làm tất cả cùng lúc
- Ưu tiên chạy được trước, đẹp sau
- Mỗi bước xong mới sang bước tiếp theo
- Giữ code đơn giản, dễ đọc, dễ sửa
- Nếu chưa hiểu thuật toán phức tạp thì bắt đầu bằng bản đơn giản trước

## 10. Kết quả mong đợi
Sau khi hoàn thành, web sẽ có thể:
- Cho người dùng chọn điểm trên bản đồ
- Gửi dữ liệu lên backend
- Tính tuyến đường tối ưu
- Hiển thị kết quả trực quan trên bản đồ

