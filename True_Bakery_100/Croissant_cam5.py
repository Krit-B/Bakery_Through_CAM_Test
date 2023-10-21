import cv2
import sys
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QWidget,
    QFileDialog,
)
from ultralytics import YOLO

class VideoCaptureThread(QThread):
    new_frame = Signal(QImage)

    def __init__(self):
        super().__init__()
        self.capture = cv2.VideoCapture(0)
        self.running = True
        self.model = YOLO('bakery_100.pt')  # Initialize your YOLO model here
        self.bakery_prices = {
            'cookie': 5,
            'croissant': 30,
            'donut': 25,
        }
        self.obj_lists_count = None
        self.total_price = None
        
    def run(self):
        while self.running:
            ret, frame = self.capture.read()
            frame = cv2.resize(frame, None, fx = 1.5, fy = 1.5)
            if not ret:
                continue

            # Perform object detection on the frame
            frame_with_objects = self.detect_objects(frame)

            # Convert OpenCV BGR image to QImage
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame_with_objects[0].data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()


            self.new_frame.emit(q_image)


    def detect_objects(self, frame):

        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 1
        color = (255, 0, 0)
        thickness = 3
        coor_x = coor_y = 50
        frame_with_objects = frame.copy()
        total_price = 0  # Initialize total price


        # Perform object detection using your YOLO model here
        results = self.model.predict(frame, conf=0.6, show=False)

        obj_lists = self.model.names  # Model Classes {0: 'cookie', 1: 'croissant', 2: 'donut'}
        total_bakery = {
            'cookie':0,
            'crossiant':0,
            'donut':0
            }


        objs = results[0].boxes.numpy()  # Arrays of Predicted result
        obj_count = {value: key for key, value in obj_lists.items()}
        obj_lists_count = dict.fromkeys({value: key for key, value in obj_lists.items()}, 0)

        if objs.shape[0] != 0:  # Check if object > 0 piece.
            for obj in objs:
                detected_obj = obj_lists[int(obj.cls[0])]  # Change Object index to name.
                if detected_obj == 'cookie' or 'croissant' or 'donut':

                    x0,y0,x1,y1 = obj.xyxy[0].astype(int)
                    frame = cv2.rectangle(frame_with_objects, (int(x0), int(y0)), (int(x1), int(y1)), (255, 255, 255),  3)

                    image = cv2.putText(frame_with_objects, detected_obj, (x0,y0-10), font, fontScale, color, thickness, cv2.LINE_AA)
                    

                obj_lists_count[detected_obj] += 1

        # Draw bounding boxes and labels on the frame
        
        #TO RETURN BAKERY PIECES AND PRICES......

        for bread, quantity in obj_lists_count.items():
            if quantity > 0:
                price_per_piece = self.bakery_prices.get(bread, 0)
                if price_per_piece > 0:
                    # print(obj_lists_count)
                    text = f'{bread.title()} = {quantity} >> {quantity * price_per_piece} Bath'
                    total_price += quantity * price_per_piece
                else:
                    text = f'{quantity} {bread.title()}s (Price not available)'

                coordinates = (coor_x, coor_y)
                frame_with_objects = cv2.putText(frame_with_objects, text, coordinates, font, fontScale, color, thickness, cv2.LINE_AA)
                coor_y += 75

        # Display the total price
        total_text = f'Total Price: {total_price} Bath'
        frame_with_objects = cv2.putText(frame_with_objects, total_text, (50, coor_y + 75), font, fontScale, color, thickness, cv2.LINE_AA)

        self.obj_lists_count = obj_lists_count
        self.total_price = total_price
        
        return frame_with_objects
    

    def stop(self):
        self.running = False
        self.wait()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Capture and Save")
        self.setGeometry(25, 25, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # Align the video to the left and top
        self.layout.addWidget(self.video_label)

        self.capture_button = QPushButton("Capture Image", self)
        self.save_button = QPushButton("Save Image", self)

        self.layout.addWidget(self.capture_button, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.save_button, alignment=Qt.AlignLeft)

        self.capture_button.clicked.connect(self.capture_image)
        self.save_button.clicked.connect(self.save_image)

        self.video_thread = VideoCaptureThread()
        self.video_thread.new_frame.connect(self.update_video_label)
        self.video_thread.start()

        #set Attribute
        self.obj_lists_count = None
        self.total_price = None
 

        # # Secode QLabel for second frame        
        self.captured_frame = QLabel(self.obj_lists_count)
        self.captured_frame.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.captured_frame, alignment=Qt.AlignRight)

        # self.latest_frame = None
        # self.captured_frame = None  # Initialize captured_frame
        # self.obj_lists_count = None
    
        self.pause_button = QPushButton("Pause", self)
        self.layout.addWidget(self.pause_button, alignment=Qt.AlignLeft)
        self.pause_button.clicked.connect(self.the_button_was_clicked)

        self.resume_button = QPushButton("Resume", self)
        self.layout.addWidget(self.resume_button, alignment=Qt.AlignLeft)
        self.resume_button.clicked.connect(self.resume_video_capture)

    def the_button_was_clicked(self):
        self.video_thread.running = False
        # Wait for the thread to finish
        print(self.obj_lists_count)
        self.video_thread.wait()

    def resume_video_capture(self):
        # Set the running flag back to True
        self.video_thread.running = True

        # Start the video capture thread again
        self.video_thread.start()

    @Slot(QImage)
    def update_video_label(self, frame):
        self.latest_frame = frame
        pixmap = QPixmap.fromImage(frame)

        # Calculate the size for displaying the video with the desired width
        desired_width = 700  # Change this to your desired width
        scaled_pixmap = pixmap.scaledToWidth(desired_width, Qt.SmoothTransformation)

        self.video_label.setPixmap(scaled_pixmap)

    @Slot()
    def capture_image(self):
        if self.latest_frame is not None:
            self.captured_frame = self.latest_frame
            # pixmap = QPixmap.fromImage(self.captured_frame).scaled(920, 920, Qt.KeepAspectRatio)
            # self.captured_frame.setPixmap(pixmap)
            self.obj_lists_count = self.video_thread.obj_lists_count
            self.total_price = self.video_thread.total_price
            # print(self.obj_lists_count, self.total_price)
            
    # @Slot(QImage)
    # def update_captured_frame(self, frame):
    #     self.latest_frame = frame
    #     pixmap = QPixmap.fromImage(frame)

    #     # Calculate the size for displaying the video with the desired width
    #     desired_width = 700  # Change this to your desired width
    #     scaled_pixmap = pixmap.scaledToWidth(desired_width, Qt.SmoothTransformation)

    #     self.captured_frame.setPixmap(scaled_pixmap)

    @Slot()
    def save_image(self):
        if self.captured_frame is not None:
            options = QFileDialog.Options()
            options |= QFileDialog.ReadOnly
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "Images (*.png *.jpg);;All Files (*)", options=options)
            if file_path:
                if self.captured_frame.save(file_path):
                    print(f"Image saved as {file_path}")
                else:
                    print("Failed to save image.")

    def closeEvent(self, event):
        self.video_thread.stop()
        self.video_thread.capture.release()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())