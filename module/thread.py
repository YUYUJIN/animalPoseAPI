import cv2
import time
import datetime
from threading import Thread

frame=None

class CamThread(Thread):
    def __init__(self,imageSrc):
        super().__init__()
        self.imageSrc=imageSrc
        self.camera = cv2.VideoCapture(imageSrc)
        self.streaming=None
        # now = datetime.datetime.now()
        # timeString = now.strftime("%Y-%m-%d %H:%M")
        # time.sleep(0.01)
        #self.model=model
    def run(self):
        print('Cam start')
        global frame
        while True:
            ret, frame_curr = self.camera.read()
            time.sleep(0.05)
            if ret==False:
                self.camera = cv2.VideoCapture(self.imageSrc)
                ret, frame_curr = self.camera.read()
            frame=frame_curr
            self.streaming=frame_curr
            # 참조, 송신 코드
            #self.frame_curr=self.model(self.frame_curr)
            
            # sql process

class PoseThread(Thread):
    def __init__(self,model,db):
        super().__init__()
        self.pose=None
        self.model=model
        self.db=db
        self.frame_done=None
    
    def run(self):
        print('Pose check')
        global frame
        while True:
            if frame is not None:
                self.frame_done=self.model(frame,self.db)
                #print(self.model.act_label,self.model.act_score)




            # 참조가능