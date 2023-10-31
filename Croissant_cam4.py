import cv2
import sys
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QStackedLayout,
    QGridLayout,
    QGroupBox,
    QPushButton,
    QLabel,
    QWidget,
    QFileDialog,
)

from ultralytics import YOLO
import numpy as np
from PIL import Image

# ลงvenv lib ด้วย -m pip install -r bakery_lib.txt

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
                    if y0 < 10:
                        image = cv2.putText(frame_with_objects, detected_obj, (x0,y1+20), font, fontScale, color, thickness, cv2.LINE_AA)
                    else:    
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
                # frame_with_objects = cv2.putText(frame_with_objects, text, coordinates, font, fontScale, color, thickness, cv2.LINE_AA)
                coor_y += 75

        # Display the total price
        total_text = f'Total Price: {total_price} Bath'
        # frame_with_objects = cv2.putText(frame_with_objects, total_text, (50, coor_y + 75), font, fontScale, color, thickness, cv2.LINE_AA)

        self.obj_lists_count = obj_lists_count
        self.total_price = total_price
        
        return frame_with_objects, obj_lists_count

    def stop(self):
        self.running = False
        self.wait()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Capture and Save") #Set window name
        self.setGeometry(0, 0, 800, 600) #Set window coordinate

        #Add Bakery&Price Attribute
        self.show_item = None
        self.total_price = None
        self.items = None
        self.latest_frame = None
        self.captured_frame = None  

        #Set Layout
        self.page_layout = QVBoxLayout()
        self.frame_layout = QGridLayout()
        self.bakery_name_row = QHBoxLayout()
        self.bakery_count_row = QHBoxLayout()
        self.button_layout = QHBoxLayout()
    
        self.page_layout.addLayout(self.frame_layout)
        self.page_layout.addLayout(self.bakery_name_row)
        self.page_layout.addLayout(self.bakery_count_row)
        self.page_layout.addLayout(self.button_layout)
        

        # Set the spacing between the widgets in the horizontal layout to 0
        self.button_layout.setSpacing(10)

        self.frame_layout.setContentsMargins(0,0,1,1) 
        self.frame_layout.setSpacing(20)

        #video frame
        self.video_label = QLabel(self)
        self.frame_layout.addWidget(self.video_label,0,0)
        self.video_label.setMinimumHeight(0)
        self.video_label.setMinimumWidth(0)

        # Add QLabel for displaying the captured image
        self.captured_label = QLabel(self)
        self.captured_label.linkActivated.connect(self.the_button_was_clicked)
        self.frame_layout.addWidget(self.captured_label,0,1)

        #set Font
        _font = QFont("Sometype Mono", 20)
        #Group of Bakery Name
        self.cookie_name = QLabel(self)
        self.setCentralWidget(self.cookie_name)
        self.cookie_name.setFont(_font)
        self.cookie_name.setText("Cookie")
        self.bakery_name_row.addWidget(self.cookie_name)
        
        self.crossiant_name = QLabel(self)
        self.setCentralWidget(self.crossiant_name)
        self.crossiant_name.setFont(_font)
        self.crossiant_name.setText("Crossiant")
        self.bakery_name_row.addWidget(self.crossiant_name)

        self.donut_name = QLabel(self)
        self.setCentralWidget(self.donut_name)
        self.donut_name.setFont(_font)
        self.donut_name.setText("Donut")
        self.bakery_name_row.addWidget(self.donut_name)

        self.total_name = QLabel(self)
        self.setCentralWidget(self.total_name)
        self.total_name.setFont(_font)
        self.total_name.setText("Total Price")
        self.bakery_name_row.addWidget(self.total_name)

        #Group of Bakery Price
        self.cookie_price = QLabel(self)
        self.setCentralWidget(self.cookie_price)
        self.cookie_price.setFont(_font)
        self.cookie_price.setText("0")
        self.bakery_count_row.addWidget(self.cookie_price)

        self.crossiant_price = QLabel(self)
        self.setCentralWidget(self.crossiant_price)
        self.crossiant_price.setFont(_font)
        self.crossiant_price.setText("0")
        self.bakery_count_row.addWidget(self.crossiant_price)

        self.donut_price = QLabel(self)
        self.setCentralWidget(self.donut_price)
        self.donut_price.setFont(_font)
        self.donut_price.setText("0")
        self.bakery_count_row.addWidget(self.donut_price)

        self.price = QLabel(self)
        self.setCentralWidget(self.price)
        self.price.setFont(_font)
        self.price.setText("0")
        self.bakery_count_row.addWidget(self.price)

        #capture button
        self.capture_button = QPushButton("Capture Image", self)
        self.button_layout.addWidget(self.capture_button)
        self.capture_button.clicked.connect(self.capture_image)
        #save button
        self.save_button = QPushButton("Save Image", self)
        self.button_layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save_image)
        #pause button
        self.pause_button = QPushButton("Pause", self)
        self.button_layout.addWidget(self.pause_button)
        self.pause_button.clicked.connect(self.the_button_was_clicked)
        #resume button
        self.resume_button = QPushButton("Resume", self)
        self.button_layout.addWidget(self.resume_button)
        self.resume_button.clicked.connect(self.resume_video_capture)

        #Set Video Function
        self.video_thread = VideoCaptureThread()
        self.video_thread.new_frame.connect(self.update_video_label)
        self.video_thread.start()

        #Add Layout to Widget
        widget = QWidget()
        widget.setLayout(self.page_layout)
        self.setCentralWidget(widget)

    def the_button_was_clicked(self):
        self.video_thread.running = False

        self.obj_lists_count = self.video_thread.obj_lists_count
        self.total_price = self.video_thread.total_price
        self.show_item = self.obj_lists_count

        self.update_ui() #ต้อง Update Ui เพื่อให้โปรแกรมดึงข้อมูลจากปุ่มไปไว้บน MainWindow()

        print(self.obj_lists_count,self.total_price)

        # Wait for the thread to finish
        self.video_thread.wait()

    def update_ui(self):
        # Update the UI with the latest data
        obj_lists_count = self.video_thread.obj_lists_count
        # print(obj_lists_count)
        total_price = self.video_thread.total_price
        #Bakery Extract
        self.cookie_price.setText(f"{obj_lists_count['cookie']}")
        self.crossiant_price.setText(f"{obj_lists_count['croissant']}")
        self.donut_price.setText(f"{obj_lists_count['donut']}")
        self.price.setText(f"{total_price}")

        # _font = QFont("Sometype Mono", 20)
        # self.count_label.setFont(_font)
        
        # Tell the framework to redraw the UI
        self.update()

    def resume_video_capture(self):
        self.video_thread.running = True
        self.video_thread.start()

    @Slot(QImage)
    def update_video_label(self, frame):
        self.latest_frame = frame
        pixmap = QPixmap.fromImage(frame)

        # Calculate the size for displaying the video with the desired width
        desired_width = 900  # Change this to your desired width
        scaled_pixmap = pixmap.scaledToWidth(desired_width, Qt.SmoothTransformation)

        self.video_label.setPixmap(scaled_pixmap)

    @Slot()
    def capture_image(self):
        if self.latest_frame is not None:
            self.captured_frame = self.latest_frame

            # Convert QImage to QPixmap
            pixmap = QPixmap(self.captured_frame)

            # Convert QPixmap to QImage
            image = pixmap.toImage()

            # Assuming you have a QImage object named 'image'
            width, height = image.width(), image.height()

            # Convert QImage to PIL Image
            pil_image = Image.fromqpixmap(image)  # Convert QImage to PIL Image

            # Convert PIL Image to NumPy array
            numpy_array = np.array(pil_image)

            # If you need RGB format (ignoring alpha channel for transparency)
            rgb_array = numpy_array[:, :, :3]  # Extract RGB channels, ignore the alpha channel
            results = self.video_thread.detect_objects(rgb_array)
            #print(results)
            print(results[1])
            with open("object_counts.txt", "w") as file:
                file.write(str(results[1]) + "\n")

            pixmap = QPixmap.fromImage(self.captured_frame).scaled(320, 240, Qt.KeepAspectRatio)
            self.captured_label.setPixmap(pixmap)
            
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
