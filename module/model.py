#import os
import cv2
import torch
import torchvision
from torchvision.transforms import functional as F
import torch.nn.functional as f
import numpy as np
from module.RCNN.model import get_model
from module.RCNN.utils import visualize
from module.LSTM.model import LSTMModel
from module.LSTM.utils import keypointToTensor,visualize_act
import datetime

class LRModel():
    def __init__(self,RCNN_weight,LSTM_weight_cat,LSTM_weight_dog):
        self.DEVICE=torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        #DEVICE='cpu'
        self.FRAME_PER_LSTM=3    # frame/seq_len
        self.SEQ_LEN=5           # LSTM seq_len

        print('RCNN Model load')
        self.RCNN_model=get_model(num_keypoints=15,num_classes=3)
        self.RCNN_model.load_state_dict(torch.load(RCNN_weight))
        self.RCNN_model.eval()
        self.RCNN_model.to(self.DEVICE)
        print('LSTM Model load')
        self.LSTM_cat=LSTMModel(input_dim=30,hidden_dim=30,seq_len=5,output_dim=7,layers=3)
        self.LSTM_cat.load_state_dict(torch.load(LSTM_weight_cat))
        self.LSTM_cat.eval()
        self.LSTM_cat.to(self.DEVICE)
        self.LSTM_dog=LSTMModel(input_dim=30,hidden_dim=30,seq_len=5,output_dim=8,layers=3)
        self.LSTM_dog.load_state_dict(torch.load(LSTM_weight_dog))
        self.LSTM_dog.eval()
        self.LSTM_dog.to(self.DEVICE)

        # data about frame
        self.frame_queue=None
        self.frame_store=None
        self.keypointPerFrame=None
        self.act_label=11
        self.act_score=0
        self.category_labels=[]
        self.category_label_queue=[]
        self.category_id=1   # 최초 unknown 아무거나 상관없음

        self.category_dict={
            1:'cat',
            2:'dog'
        }
        self.label_dict_cat={0:'REST',1:'SITDOWN',2:'TAILING',3:'WALKRUN',4:'ARMSTRETCH',5:'PLAYING',6:'GROOMING',11:'UNKNOWN'}
        self.label_dict_dog={0:'REST',1:'SITDOWN',2:'TAILING',3:'WALKRUN',4:'FOOTUP',5:'BODYSCRATCH',6:'BODYSHAKE',11:'UNKNOWN'}

    def __call__(self,image,db):
        image_src=image.copy()
        with torch.no_grad():
            image_tensor=F.to_tensor(image_src).to(self.DEVICE).unsqueeze(0)
            rcnn_outputs=self.RCNN_model(image_tensor)
        # # #print(rcnn_outputs)

            if rcnn_outputs[0]['boxes'].shape[0]==0:
                pass
            else:
                scores = rcnn_outputs[0]['scores'].detach().cpu().numpy()

                high_scores_idxs = np.where(scores > 0.75)[0].tolist() # Indexes of boxes with scores > 0.7
                if len(high_scores_idxs)==0:
                    pass
                else:
                    high_scores_idxs = np.where(max([scores[idx] for idx in high_scores_idxs]))[0].tolist()
                    post_nms_idxs = torchvision.ops.nms(rcnn_outputs[0]['boxes'][high_scores_idxs], rcnn_outputs[0]['scores'][high_scores_idxs], 0.3).cpu().numpy() # Indexes of boxes left after applying NMS (iou_threshold=0.3)
                    
                    labels=[]
                    for lbs in rcnn_outputs[0]['labels'][high_scores_idxs][post_nms_idxs].detach().cpu().numpy():
                        labels.append(lbs)

                    keypoints = []
                    for kps in rcnn_outputs[0]['keypoints'][high_scores_idxs][post_nms_idxs].detach().cpu().numpy():
                        keypoints.append([list(map(int, kp[:2])) for kp in kps])

                    bboxes = []
                    for bbox in rcnn_outputs[0]['boxes'][high_scores_idxs][post_nms_idxs].detach().cpu().numpy():
                        bboxes.append(list(map(int, bbox.tolist())))
                    # if frame_queue is None:
                    #      frame_queue=torch.Tensor(np.array(keypoints[0]))
                    # print(frame_queue)
                    #image=visualize(img=image,labels=labels,bboxes=bboxes,keypoints=keypoints,keypoint_option=True,text_option=False)
                    
                    self.category_labels.append(labels[0])
                    if len(self.category_labels)==self.FRAME_PER_LSTM:
                        self.category_label_queue.append(2 if sum(self.category_labels)>4 else 1)
                        self.category_labels=[]
                    if len(self.category_label_queue)==self.SEQ_LEN:
                        self.category_id=1 if sum(self.category_label_queue)<7 else 2
                        del self.category_label_queue[0]

                    keypoints=keypointToTensor(keypoints[0]).to(self.DEVICE).unsqueeze(0)
                    if self.frame_store is None:
                        self.frame_store=keypoints
                    else:
                        self.frame_store=torch.cat([self.frame_store,keypoints],axis=0)
                        if self.frame_store.shape[0]==self.FRAME_PER_LSTM:
                            self.keypointPerFrame=self.frame_store.mean(dim=0).unsqueeze(0)
                            self.frame_store=None
                    if self.keypointPerFrame is not None:
                        if self.frame_queue is None:
                            self.frame_queue=self.keypointPerFrame
                        else:
                            self.frame_queue=torch.cat([self.frame_queue,self.keypointPerFrame],axis=0)
                            self.keypointPerFrame=None
                            if self.frame_queue.shape[0]>self.SEQ_LEN:
                                self.frame_queue=self.frame_queue[self.frame_queue.shape[0]-5:self.frame_queue.shape[0],:]

                                if labels[0]==1:
                                    lstm_outputs=self.LSTM_cat(self.frame_queue.unsqueeze(0))
                                    self.act_label=torch.argmax(lstm_outputs).item()
                                else:
                                    lstm_outputs=self.LSTM_dog(self.frame_queue.unsqueeze(0))
                                    self.act_label=torch.argmax(lstm_outputs).item()
                                self.act_score=torch.max(f.softmax(lstm_outputs,dim=1)).item()
                                if self.act_score>=0.8:
                                    now = datetime.datetime.now()
                                    filename=f'{now}.jpg'.replace(':','-')
                                    cv2.imwrite(f'./image/{filename}',image_src)
                                    #print(db.getData(table_name='animal_data'))
                                    #db.insData(table_name='animal_data',values=(self.category_id,self.act_label))

                                    if self.category_id==1:
                                        db.insData(table_name='album',values=(self.category_dict[self.category_id],self.label_dict_cat[self.act_label],f'/image/{filename}'))
                                    else:
                                        db.insData(table_name='album',values=(self.category_dict[self.category_id],self.label_dict_dog[self.act_label],f'/image/{filename}'))
                                    
                                
                    #image=visualize_act(image,labels=[self.act_label],bboxes=bboxes,category=self.category_id)
        return image

