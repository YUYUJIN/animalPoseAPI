import cv2
from model import LRModel

model=LRModel(RCNN_weight='./weight/keypointsrcnn_weights_150000.pth',
              LSTM_weight_cat='./weight\lstm_weights_best_cat.pth',
              LSTM_weight_dog='./weight\lstm_weights_best_dog.pth')

cap = cv2.VideoCapture('./test.mp4')

while cap.isOpened():
    success, image = cap.read()
    if not success:
        print("카메라를 찾을 수 없습니다.")
        break

    image=model(image)

    winname='test'
    cv2.namedWindow(winname)
    cv2.moveWindow(winname, 40, 30) 
    cv2.imshow(winname, image)
    cv2.waitKey(1)
cap.release()