import cv2
import numpy as np
import csv
import os
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
import face_recognition

class FaceRecognizer(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    attendance_signal = pyqtSignal(str, str, str, str)

    def __init__(self, dataset_path="dataset_khuon_mat"):
        super().__init__()
        self._run_flag = True
        self.trigger_check = False # CÔNG TẮC GHI NHẬN ĐIỂM DANH

        self.known_face_encodings = []
        self.known_face_names = []

        print("⏳ Đang nạp cơ sở dữ liệu khuôn mặt...")
        if not os.path.exists(dataset_path):
            os.makedirs(dataset_path)

        for filename in os.listdir(dataset_path):
            if filename.endswith((".jpg", ".png")):
                image_path = os.path.join(dataset_path, filename)
                image = face_recognition.load_image_file(image_path)
                try:
                    encoding = face_recognition.face_encodings(image)[0]
                    self.known_face_encodings.append(encoding)
                    self.known_face_names.append(os.path.splitext(filename)[0])
                except IndexError:
                    print(f"⚠️ Bỏ qua {filename}: Không tìm thấy khuôn mặt hợp lệ.")
                    
        print(f"✅ Đã nạp xong {len(self.known_face_names)} sinh viên vào bộ nhớ.")

    def manual_check(self):
        """Hàm này được gọi khi người dùng bấm nút trên Giao diện"""
        self.trigger_check = True

    def run(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        while self._run_flag:
            ret, frame = cap.read()
            if ret:
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                rgb_small_frame = np.ascontiguousarray(rgb_small_frame)

                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                face_detected_in_this_frame = False

                for face_encoding, face_location in zip(face_encodings, face_locations):
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.45)
                    name = "Unknown"

                    if True in matches:
                        first_match_index = matches.index(True)
                        name = self.known_face_names[first_match_index]

                    if name != "Unknown":
                        face_detected_in_this_frame = True
                        parts = name.split('_', 1)
                        student_id = parts[0]
                        student_name = parts[1] if len(parts) > 1 else "Unknown"

                        # NẾU CÓ NGƯỜI BẤM NÚT THÌ MỚI GHI VÀO EXCEL
                        if self.trigger_check:
                            action, action_time = self.process_attendance(student_id, student_name)
                            self.attendance_signal.emit(student_id, student_name, action, action_time)
                            self.trigger_check = False # Tắt công tắc ngay lập tức để không bị spam

                        top, right, bottom, left = face_location
                        top, right, bottom, left = top*4, right*4, bottom*4, left*4
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(frame, f"{student_id}", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                # Kiểm tra xem bấm nút mà không có ai trước camera không
                if self.trigger_check:
                    if not face_detected_in_this_frame:
                        print("⚠️ CẢNH BÁO: Bấm nút nhưng không nhận diện được khuôn mặt hợp lệ!")
                    self.trigger_check = False # Vẫn phải tắt công tắc đi

                self.change_pixmap_signal.emit(frame)
            else:
                break
        cap.release()

    def process_attendance(self, student_id, student_name):
        os.makedirs("database", exist_ok=True)
        filename = "database/bao_cao_diem_danh.csv"
        now = datetime.now()
        current_date = now.strftime("%d/%m/%Y")
        current_time_str = now.strftime("%H:%M:%S")

        rows = []
        if os.path.exists(filename):
            with open(filename, mode='r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=';')
                rows = list(reader)

        header = ["Ngày tháng", "Giờ", "Mã số sinh viên", "Họ tên", "Giờ Check-in", "Giờ Check-out"]
        if not rows:
            rows.append(header)

        target_row_index = -1
        for i in range(len(rows) - 1, 0, -1):
            if len(rows[i]) >= 6 and rows[i][0] == current_date and rows[i][2] == student_id:
                target_row_index = i
                break

        action = ""
        if target_row_index != -1 and rows[target_row_index][5] == "":
            rows[target_row_index][5] = current_time_str
            action = "CHECK-OUT"
        else:
            rows.append([current_date, current_time_str, student_id, student_name, current_time_str, ""])
            action = "CHECK-IN"

        with open(filename, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(rows)

        return action, current_time_str

    def stop(self):
        self._run_flag = False
        self.wait()