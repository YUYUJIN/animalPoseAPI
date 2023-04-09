from flask import Flask, render_template, Response,jsonify,request,send_from_directory
from flask_cors import CORS
import cv2
import os
import sys
import datetime
from module.model import LRModel
from module.thread import CamThread,PoseThread
from setDB import Database,label_dict
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
flag=True

@app.route('/')
def index():
    """Video streaming home page."""
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    templateData = {
            'title':'Image Streaming',
            'time': timeString
            }
    return render_template('index.html', **templateData)

def gen_frames():
    global flag
    flag=False
    # camera = cv2.VideoCapture('./cat_cam1.mp4')
    # time.sleep(0.2)
    # lastTime = time.time()*1000.0
    while True:
        # ret, image = camera.read()
        # #time.sleep(0.1)
        # if ret==False:
        #     camera = cv2.VideoCapture('./cat_cam1.mp4')
        #     ret, image= camera.read()
        # #image=cam.frame_curr
        #image=model(image)
        # #time.sleep(0.01)
        if flag:
            break
        if cam.streaming is not None:
            ret, buffer = cv2.imencode('.jpg',cam.streaming)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
@app.route('/video')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/videostop')
def video_stop():
    global flag
    flag=True
    response={'message':'video stoped'}
    return jsonify(response),200

@app.route('/image/<filename>')
def get_image(filename):
    return send_from_directory('./image', filename)

@app.route('/album',methods=['POST'])
def album_list():
    if request.method=='POST':
        req=request.get_json()
        category=req['category']
        rows=db.getAlbumList(category=category)
        response={'images':rows}

        return jsonify(response), 200
    else:
        return None
    
@app.route('/graph',methods=['POST'])
def linegraph():
    response=dict()
    if request.method=='POST':
        req=request.get_json()
        response['line']=db.today(table_name='album',animal_type=req['category'])
        response['pi_daily']=db.dailyPi(table_name='album',animal_type=req['category'])
        response['pi_weekly']=db.weeklyPi(table_name='album',animal_type=req['category'])
        response['pi_monthly']=db.monthlyPi(table_name='album',animal_type=req['category'])
        
        return jsonify(response),200
    else:
        return None

@app.route('/pose')
def returnPoss():
    if model.category_id==1:
        idx=model.label_dict_cat[model.act_label]
    else:
        idx=model.label_dict_dog[model.act_label]
    response={'pose':label_dict[idx]}
    
    return jsonify(response),200

if __name__ == '__main__':
    load_dotenv()
    db=Database(host=os.environ.get('HOST'),port=int(os.environ.get('PORT')),user=os.environ.get('USERNAME'),password=os.environ.get('PASSWARD'),db_name=os.environ.get('DATABASENAME'))
    frame=None
    flag=False
    model=LRModel(RCNN_weight='./weight/keypointsrcnn_weights_250000.pth',
              LSTM_weight_cat='./weight\lstm_weights_best_cat.pth',
              LSTM_weight_dog='./weight\lstm_weights_best_dog.pth')
    cam=CamThread('./test.mp4')
    #cam=CamThread('./dogsample2.mp4')
    cam.daemon=True
    pose=PoseThread(model,db)
    pose.daemon=True
    cam.start()
    pose.start()
    app.run(host='0.0.0.0',port=5000,debug=False)       