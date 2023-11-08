import cv2
import sys
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QFont, QPalette, QColor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QWidget,
    QFileDialog,
    QInputDialog,
)

from ultralytics import YOLO
import numpy as np
from PIL import Image, ImageFont

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
        results = self.model.predict(frame, conf=0.8, show=False)

        obj_lists = self.model.names  # Model Classes {0: 'cookie', 1: 'croissant', 2: 'donut'}
        total_bakery = {
            'cookie':0,
            'crossiant':0,
            'donut':0
            }

        objs = results[0].boxes.numpy()  # Arrays of Predicted result
        # obj_count = {value: key for key, value in obj_lists.items()} #{'cookie': 0, 'croissant': 1, 'donut': 2}{items:index}
        obj_lists_count = dict.fromkeys({value: key for key, value in obj_lists.items()}, 0)#{'cookie': 0, 'croissant': 0, 'donut': 1}

        if objs.shape[0] != 0:  # Check if object > 0 piece.
            for obj in objs:
                detected_obj = obj_lists[int(obj.cls[0])]  # Change Object index to name.
                if detected_obj == 'cookie' or 'croissant' or 'donut':
                    # Draw bounding boxes and labels on the frame
                    x0,y0,x1,y1 = obj.xyxy[0].astype(int)
                    frame = cv2.rectangle(frame_with_objects, (int(x0), int(y0)), (int(x1), int(y1)), (255, 255, 255),  3)
                    if y0 < 15:
                        image = cv2.putText(frame_with_objects, detected_obj, (x0,y1+20), font, fontScale, color, thickness, cv2.LINE_AA)
                    else:    
                        image = cv2.putText(frame_with_objects, detected_obj, (x0,y0-10), font, fontScale, color, thickness, cv2.LINE_AA)
                    
                obj_lists_count[detected_obj] += 1
    
        #TO RETURN BAKERY PIECES AND PRICES......
        for bread, quantity in obj_lists_count.items():
            if quantity > 0:
                price_per_piece = self.bakery_prices.get(bread, 0)
                if price_per_piece > 0:
                    print(obj_lists_count)
                    text = f'{bread.title()} = {quantity} >> {quantity * price_per_piece} Bath'
                    total_price += quantity * price_per_piece
                else:
                    text = f'{quantity} {bread.title()}s (Price not available)'

                # coordinates = (coor_x, coor_y)
                # frame_with_objects = cv2.putText(frame_with_objects, text, coordinates, font, fontScale, color, thickness, cv2.LINE_AA)
                # coor_y += 75

        # Display the total price
        # total_text = f'Total Price: {total_price} Bath'
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

        #Set Video Function
        self.video_thread = VideoCaptureThread()
        self.video_thread.new_frame.connect(self.update_video_label)
        self.video_thread.start()

        
        #Add Bakery&Price Attribute
        self.show_item = None
        self.total_price = None
        self.items = None
        self.latest_frame = None
        self.captured_frame = None  
        self.Bakery_price = self.video_thread.bakery_prices

        #Set Layout
        self.page_layout = QVBoxLayout()
        self.frame_layout = QHBoxLayout()
        self.text_layout = QVBoxLayout()

        # for setText Bread
        self.bakery_row = QVBoxLayout()
        self.cookie_result = QHBoxLayout()
        self.crossiant_result = QHBoxLayout()
        self.donut_result = QHBoxLayout()
            
        self.button_layout = QHBoxLayout() #Button Rows

        self.page_layout.addLayout(self.frame_layout)
        self.page_layout.addLayout(self.button_layout)

        # Set the spacing between the widgets in the horizontal layout to 0
        self.button_layout.setSpacing(10)
        self.frame_layout.setSpacing(20)
        self.bakery_row.setStretch(1,1)

        #video frame
        self.video_label = QLabel(self)
        self.frame_layout.addWidget(self.video_label)
        self.video_label.setMinimumHeight(0)
        self.video_label.setMinimumWidth(0)

        # Add QLabel for displaying the captured image
        self.captured_label = QLabel(self)
        self.captured_label.linkActivated.connect(self.the_button_was_clicked)
        # self.frame_layout.addWidget(self.captured_label)

        self.frame_layout.addLayout(self.bakery_row)

        #set Font
        _font = QFont("Sometype Mono", 20)
        #Set Color
        palette = QPalette()
        palette.setColor(QPalette.Window,Qt.black)


        #Group of Bakery Name
        self.cookie_name = QLabel(self)
        self.setCentralWidget(self.cookie_name)
        self.cookie_name.setFont(_font)
        self.cookie_name.setText("<font color='white'>Cookie</font>")

        #set Background
        self.cookie_name.setAutoFillBackground(True)
        self.cookie_name.setPalette(palette)
        self.cookie_name.setAlignment(Qt.AlignCenter)
        self.bakery_row.addWidget(self.cookie_name)
        self.bakery_row.addLayout(self.cookie_result)
        

        self.crossiant_name = QLabel(self)
        self.setCentralWidget(self.crossiant_name)
        self.crossiant_name.setAlignment(Qt.AlignCenter)
        self.crossiant_name.setAutoFillBackground(True)
        self.crossiant_name.setPalette(palette)
        self.crossiant_name.setFont(_font)
        self.crossiant_name.setText("<font color='white'>Crossiant</font>")
        self.bakery_row.addWidget(self.crossiant_name)
        self.bakery_row.addLayout(self.crossiant_result)
        

        self.donut_name = QLabel(self)
        self.setCentralWidget(self.donut_name)
        self.donut_name.setAlignment(Qt.AlignCenter)
        self.donut_name.setAutoFillBackground(True)
        self.donut_name.setPalette(palette)
        self.donut_name.setFont(_font)
        self.donut_name.setText("<font color='white'>Donut</font>")
        self.bakery_row.addWidget(self.donut_name)
        self.bakery_row.addLayout(self.donut_result)


        self.total_name = QLabel(self)
        self.setCentralWidget(self.total_name)
        self.total_name.setAlignment(Qt.AlignLeft | Qt.AlignCenter)
        self.total_name.setAutoFillBackground(True)
        self.total_name.setPalette(palette)
        self.total_name.setFont(_font)
        self.total_name.setText("<font color='white'>Total Price</font>")
        self.bakery_row.addWidget(self.total_name)

        #Group of Bakery Price
        self.cookie_pcs = QLabel(self)
        # self.setCentralWidget(self.cookie_pcs)
        self.cookie_pcs.setAlignment(Qt.AlignLeft | Qt.AlignCenter)
        self.cookie_pcs.setFont(_font)
        self.cookie_pcs.setText("0 ชิ้น")

        self.cookie_price = QLabel(self)
        # self.setCentralWidget(self.cookie_price)
        self.cookie_price.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.cookie_price.setFont(_font)
        self.cookie_cost = self.Bakery_price["cookie"]
        self.cookie_price.setText(str(self.cookie_cost)+ " บาท/ชิ้น")
        
        self.cookie_total = QLabel(self)
        self.setCentralWidget(self.cookie_total)
        self.cookie_total.setAlignment(Qt.AlignRight | Qt.AlignCenter)
        self.cookie_total.setFont(_font)
        cookie_t = 0
        self.cookie_total.setText(str(cookie_t)+ " บาท")

        self.cookie_result.addWidget(self.cookie_pcs)
        self.cookie_result.addWidget(self.cookie_price)
        self.cookie_result.addWidget(self.cookie_total)


        self.crossiant_pcs = QLabel(self)
        # self.setCentralWidget(self.crossiant_pcs)
        self.crossiant_pcs.setAlignment(Qt.AlignLeft | Qt.AlignCenter)
        self.crossiant_pcs.setFont(_font)
        self.crossiant_pcs.setText("0 ชิ้น")
        self.crossiant_result.addWidget(self.crossiant_pcs)

        self.crossiant_price = QLabel(self)
        # self.setCentralWidget(self.crossiant_price)
        self.crossiant_price.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.crossiant_price.setFont(_font)
        self.crossiant_cost = self.Bakery_price["croissant"]
        self.crossiant_price.setText(str(self.crossiant_cost)+ " บาท/ชิ้น")

        self.crossiant_total = QLabel(self)
        self.setCentralWidget(self.crossiant_total)
        self.crossiant_total.setAlignment(Qt.AlignRight | Qt.AlignCenter)
        self.crossiant_total.setFont(_font)
        crossiant_t = 0
        self.crossiant_total.setText(str(crossiant_t)+ " บาท")

        self.crossiant_result.addWidget(self.crossiant_pcs)
        self.crossiant_result.addWidget(self.crossiant_price)
        self.crossiant_result.addWidget(self.crossiant_total)

        self.donut_pcs = QLabel(self)
        # self.setCentralWidget(self.donut_pcs)
        self.donut_pcs.setAlignment(Qt.AlignLeft | Qt.AlignCenter)
        self.donut_pcs.setFont(_font)
        self.donut_pcs.setText("0 ชิ้น")
        self.donut_result.addWidget(self.donut_pcs)

        self.donut_price = QLabel(self)
        # self.setCentralWidget(self.donut_price)
        self.donut_price.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.donut_price.setFont(_font)
        self.donut_cost = self.Bakery_price["donut"]
        self.donut_price.setText(str(self.donut_cost)+ " บาท/ชิ้น")

        self.donut_total = QLabel(self)
        self.setCentralWidget(self.donut_total)
        self.donut_total.setAlignment(Qt.AlignRight | Qt.AlignCenter)
        self.donut_total.setFont(_font)
        donut_t = 0
        self.donut_total.setText(str(donut_t)+ " บาท")

        self.donut_result.addWidget(self.donut_pcs)
        self.donut_result.addWidget(self.donut_price)
        self.donut_result.addWidget(self.donut_total)

        self.price = QLabel(self)
        self.setCentralWidget(self.price)
        self.price.setAlignment(Qt.AlignCenter)
        self.price.setFont(_font)
        self.price.setText("0 บาท")
        self.bakery_row.addWidget(self.price)

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
        self.cookie_pcs.setText(f"{obj_lists_count['cookie']} ชิ้น")
        self.crossiant_pcs.setText(f"{obj_lists_count['croissant']} ชิ้น")
        self.donut_pcs.setText(f"{obj_lists_count['donut']} ชิ้น")
        self.price.setText(f"{total_price} บาท")
        self.cookie_total.setText(f"{obj_lists_count['cookie']*self.cookie_cost} บาท")
        self.crossiant_total.setText(f"{obj_lists_count['croissant']*self.crossiant_cost} บาท")
        self.donut_total.setText(f"{obj_lists_count['donut']*self.donut_cost} บาท")

        # Tell the framework to redraw the UI
        # self.update()

    def resume_video_capture(self):
        self.update_ui_resume()

        self.video_thread.running = True
        self.video_thread.start()

    def update_ui_resume(self):
        #Bakery Extract
        self.cookie_pcs.setText("0 ชิ้น")
        self.crossiant_pcs.setText("0 ชิ้น")
        self.donut_pcs.setText("0 ชิ้น")
        self.price.setText("0 บาท")

        # Tell the framework to redraw the UI
        self.update()

    @Slot(QImage)
    def update_video_label(self, frame):
        self.latest_frame = frame
        pixmap = QPixmap.fromImage(frame)

        # Calculate the size for displaying the video with the desired width
        desired_width = 1200  # Change this to your desired width
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

            pixmap = QPixmap.fromImage(self.captured_frame).scaled(900, 900, Qt.KeepAspectRatio)
            # self.captured_label.setPixmap(pixmap)
            
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
