from ultralytics import YOLO
import numpy as np
import cv2

# model = YOLO('model.pt')
model = YOLO('bakery.pt')

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
num = 1
while cap.isOpened():

    timer = cv2.getTickCount()

    ret, frame = cap.read()
    frame = cv2.resize(frame, None, fx=1, fy=1)
    results = model.predict(frame, conf=0.8, show=True)

    # cv2.imshow('image',frame)
    cv2.waitKey(1)
    #cv2.imwrite('./image/im_'+str(num)+'.png',frame)
    num = num+1

    fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)
    print(fps)
  

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
