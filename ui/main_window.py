import cv2
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QPushButton)
from PyQt5.QtGui import QImage, QPixmap, QColor, QBrush, QFont, QCursor
from PyQt5.QtCore import Qt
from core.recognizer import FaceRecognizer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống Điểm danh Khuôn mặt AI - HUST")
        self.showMaximized() 

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        # --- CỘT TRÁI: CAMERA + NÚT BẤM ---
        self.left_container = QWidget()
        self.left_layout = QVBoxLayout(self.left_container)
        self.left_layout.setContentsMargins(0, 0, 0, 0)

        # Khung Camera
        self.video_label = QLabel("Đang khởi động Camera AI...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.video_label.setMinimumSize(1, 1) 
        self.video_label.setStyleSheet("background-color: #111726; border-radius: 12px; border: 2px solid #233554;")
        self.left_layout.addWidget(self.video_label, stretch=8) # Camera chiếm 8 phần

        # NÚT BẤM ĐIỂM DANH THỦ CÔNG
        self.check_btn = QPushButton("✅ THỰC HIỆN CHECK IN / OUT")
        self.check_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.check_btn.setStyleSheet("""
            QPushButton {
                background-color: #00ff99;
                color: #0a192f;
                font-size: 22px;
                font-weight: bold;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
            }
            QPushButton:hover { background-color: #00cc7a; }
            QPushButton:pressed { background-color: #00995c; }
        """)
        self.left_layout.addWidget(self.check_btn, stretch=1) # Nút bấm chiếm 1 phần

        self.main_layout.addWidget(self.left_container, stretch=2) 

        # --- CỘT PHẢI: BẢNG NHẬT KÝ ---
        self.right_container = QWidget()
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel("NHẬT KÝ ĐIỂM DANH HÔM NAY")
        self.title_label.setStyleSheet("font-size: 20px; color: #00ff99; font-weight: bold; padding: 5px;")
        self.right_layout.addWidget(self.title_label)

        self.table_widget = QTableWidget(0, 4)
        self.table_widget.setHorizontalHeaderLabels(["Mã SV", "Tên Sinh Viên", "Trạng Thái", "Thời Gian"])
        self.table_widget.setStyleSheet("""
            QTableWidget { background-color: #0a192f; color: #cbd5e1; gridline-color: #233554; font-size: 15px; border-radius: 8px; }
            QHeaderView::section { background-color: #172a45; color: #00ff99; font-weight: bold; border: 1px solid #233554; height: 40px; font-size: 15px; }
        """)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.right_layout.addWidget(self.table_widget)

        self.main_layout.addWidget(self.right_container, stretch=1) 

        # --- KẾT NỐI VỚI LÕI AI ---
        self.recognizer = FaceRecognizer()
        self.recognizer.change_pixmap_signal.connect(self.update_image)
        self.recognizer.attendance_signal.connect(self.add_log)
        
        # Kết nối sự kiện bấm nút với hàm manual_check() ở lõi AI
        self.check_btn.clicked.connect(self.recognizer.manual_check)

        self.recognizer.start() 

    def update_image(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_img).scaled(
            self.video_label.width(), self.video_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def add_log(self, student_id, student_name, action, action_time):
        self.table_widget.insertRow(0)

        item_id = QTableWidgetItem(student_id)
        item_name = QTableWidgetItem(student_name)
        item_action = QTableWidgetItem(action)
        item_time = QTableWidgetItem(action_time)

        font = QFont()
        font.setBold(True)
        item_action.setFont(font)

        if action == "CHECK-IN":
            item_action.setForeground(QBrush(QColor("#00ffff"))) 
        else:
            item_action.setForeground(QBrush(QColor("#ff9f43"))) 

        for item in (item_id, item_name, item_action, item_time):
            item.setTextAlignment(Qt.AlignCenter)

        self.table_widget.setItem(0, 0, item_id)
        self.table_widget.setItem(0, 1, item_name)
        self.table_widget.setItem(0, 2, item_action)
        self.table_widget.setItem(0, 3, item_time)

    def closeEvent(self, event):
        self.recognizer.stop()
        event.accept()