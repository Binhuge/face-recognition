import cv2
import os
import face_recognition
import numpy as np

def is_blurry(image, threshold=80.0):
    """
    Sử dụng thuật toán phương sai Laplacian của OpenCV để đo độ sắc nét.
    Nếu điểm số thấp hơn threshold -> Ảnh bị mờ.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    focus_measure = cv2.Laplacian(gray, cv2.CV_64F).var()
    return focus_measure < threshold

def main():
    os.makedirs("dataset_khuon_mat", exist_ok=True)

    print("="*50)
    print("📸 HỆ THỐNG ĐĂNG KÝ KHUÔN MẶT - TỰ ĐỘNG CẮT (AUTO-CROP)")
    print("="*50)
    
    ma_sv = input("👉 Nhập Mã Sinh Viên (VD: 20231122): ").strip()
    ten_sv = input("👉 Nhập Tên Sinh Viên (VD: Nguyen Van A): ").strip()
    
    if not ma_sv or not ten_sv:
        print("❌ Lỗi: Mã SV và Tên SV không được để trống!")
        return

    filename = f"dataset_khuon_mat/{ma_sv}_{ten_sv}.jpg"

    print("\n⏳ Đang khởi động Camera...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print("❌ Lỗi: Không thể kết nối với Webcam!")
        return

    print("🟢 Camera đã mở!")
    print("💡 HƯỚNG DẪN: Đưa mặt vào giữa khung hình, nhìn thẳng.")
    print("   - Bấm phím 'C' để CHỤP VÀ TỰ ĐỘNG CẮT.")
    print("   - Bấm phím 'Q' để HỦY BỎ.")

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        
        # Sao chép frame để vẽ chữ lên giao diện camera
        display_frame = frame.copy()
        
        cv2.putText(display_frame, "Nhan 'C' de CHUP | 'Q' de THOAT", (15, 35), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow("Dang ky Khuon mat - Auto Crop", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('c'):
            print("\n⚙️ Đang phân tích chất lượng hình ảnh...")
            
            # 1. Kiểm tra độ mờ
            if is_blurry(frame):
                print("⚠️ CẢNH BÁO: Ảnh quá mờ hoặc thiếu sáng! Vui lòng giữ chắc tay và chụp lại.")
                continue

            # 2. Xử lý ảnh cho dlib (Dùng công thức mảng chuẩn của face_recognition)
            # frame[:, :, ::-1] là cách đổi màu BGR sang RGB cực nhanh mà không làm hỏng cấu trúc bộ nhớ
            rgb_frame = frame[:, :, ::-1]

            # Tìm khuôn mặt
            face_locations = face_recognition.face_locations(rgb_frame)

            if not face_locations:
                print("⚠️ CẢNH BÁO: Không tìm thấy khuôn mặt nào! Hãy nhìn thẳng vào camera.")
                continue
            elif len(face_locations) > 1:
                print("⚠️ CẢNH BÁO: Có nhiều hơn 1 người trong khung hình. Vui lòng đứng một mình!")
                continue

            # 3. Cắt khuôn mặt (Crop) với khoảng đệm
            top, right, bottom, left = face_locations[0]
            
            h, w, _ = frame.shape
            pad_y = int((bottom - top) * 0.25)
            pad_x = int((right - left) * 0.2)

            top = max(0, top - pad_y)
            bottom = min(h, bottom + pad_y)
            left = max(0, left - pad_x)
            right = min(w, right + pad_x)

            face_image = frame[top:bottom, left:right]

            # 4. Lưu ảnh
            cv2.imwrite(filename, face_image)
            print(f"✅ THÀNH CÔNG! Đã cắt và lưu khuôn mặt của: {ten_sv}")
            print(f"📁 Đường dẫn: {filename}")
            break
            
        elif key == ord('q'):
            print("\n⚠️ Đã hủy quá trình chụp ảnh.")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()