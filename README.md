# animalPostAPI
> 동영상을 API로 계속 스트리밍하면서 이전 프로젝트의 결과로 나온 Fast-RCNN 모델과 LSTM 모델을 사용해 반려동물의 행동에 대한 서비스를 제공하는 API.  
> Fast-RCNN 모델을 통해 반려동물의 keypoint와 category(고양이, 강아지)를 검출해내고, 이를 LSTM 모델의 입력으로 사용하여 각각의 반려동물의 행동을 분류한다.  
> MySQL로 구성된 Database를 server 환경에 구축하고 모델의 결과를 저장한다.  

<img src=https://img.shields.io/badge/python-3.8.0-green></img>
<img src=https://img.shields.io/badge/opencv--python-4.5.5.64-yellow></img>
<img src=https://img.shields.io/badge/Flask-2.2.2-blue></img>
<img src=https://img.shields.io/badge/PyMySQL-1.0.2-orange></img>
<img src=https://img.shields.io/badge/pytorch-1.11.0-red></img>  

## How to use
Fast-RCNN 모델과 LSTM 모델을 사용하기 위해 pytorch를 설치한다.  
환경에 맞게 설치하되, 본 프로젝트의 개발 환경에 맞는 설치는 다음과 같다.
```
pip install torch==1.11.0+cu113 torchvision==0.12.0+cu113 torchaudio==0.11.0 --extra-index-url https://download.pytorch.org/whl/cu113
```  
  
사전준비 및 필요 dependency 설치   
```
git clone https://github.com/YUYUJIN/animalPoseAPI
cd animalPostAPI
pip install -r requirements.txt
```

workplace 내에 .env 파일을 만들어 Database의 정보생성
본 프로젝트에서는 server 내에 Database를 이용하였고, 엔진으로는 MySQL로 구성하였다.  
<img src=https://github.com/YUYUJIN/animalPoseAPI/blob/main/pictures/db.PNG></img>

모델의 가중치를 weight 폴더에 넣어 프로젝트 폴더 내로 옮긴다.  
모델의 weight들은 github 특성 상 용량이 제한되어 누락되어있다.  

이후 app을 구동하여 간이 API를 사용한다.  
```
python app.py
```

## Fast-RCNN && LSTM
Keypoint와 Category 분류를 위한 Fast-RCNN 모델은 다음과 같은 출력을 가진다.  
시각화한 예시.  
<img src=https://github.com/YUYUJIN/animalPoseAPI/blob/main/pictures/fast_rcnn_result.png></img>  
  
검출된 정보를 바탕으로 고양이, 강아지에 따라 행동을 분류하는 LSTM 모델은 다음과 같은 출력을 가진다.  
시각화한 예시  
<img src=https://github.com/YUYUJIN/animalPoseAPI/blob/main/pictures/lstm_result.png></img>  

## Structure
<img src=https://github.com/YUYUJIN/animalPoseAPI/blob/main/pictures/structure.png></img>  
프로젝트의 구조도는 위와 같다.  
  
핵심은 홈캠의 프레임을 API로 제공하여 스트리밍하고, 추가적으로 홈캠의 영상을 준비한 모델들의 입력으로 사용하여 반려동물의 행동을 인식하는 것이다.  
Database로는 MySQL을 사용하였고, 모델의 결과를 저장한 뒤에 Client에 요청에 따라 일간, 주간, 월간 데이터를 제공한다. 추가로 image 폴더를 스토리지로 사용하여 사진을 저장하고 이 또한 Client에게 API 형태로 제공한다. API는 Flask를 이용하여 restfulAPI로 구성하였다.  

## API Document
프로젝트의 결과로 제공할 수 있는 API는 다음 명세와 같다.  
<img src=https://github.com/YUYUJIN/animalPoseAPI/blob/main/pictures/api1.PNG></img>  
<img src=https://github.com/YUYUJIN/animalPoseAPI/blob/main/pictures/api2.PNG></img>  
<img src=https://github.com/YUYUJIN/animalPoseAPI/blob/main/pictures/api3.PNG></img>  
  
API Document link: https://documenter.getpostman.com/view/15695216/2s93JzMLfV  

## Trouble Shooting
<details>
<summary>비디오와 모델 처리 속도</summary>

비디오를 스트리밍하는 속도와 준비한 Fast-RCNN 모델의 처리 속도 차이가 발생하였다. Fast-RCNN 모델의 속도가 스트리밍보다 현저히 느려 스트리밍되는 동영상에서 프레임 드랍이나 재생속도에 문제가 발생하였다.  
이를 해결하기 위한 방안으로 비디오를 스트리밍하는 동작과 모델의 영상 처리 동작을 스레드로 구성하여 실행하였다.  
<img src=https://github.com/YUYUJIN/animalPoseAPI/blob/main/pictures/thread_t.png></img>  
 
이 때 비디오 스레드에 맞추어 홈캠이 동작하므로 모델은 한 동작이 끝날 때마다 비디오 스레드의 영상 데이터를 참조한다. 두 동작의 속도 차이만큼 누락되는 프레임 데이터들이 존재한다. 이를 해결하기 위해 앞서 프로젝트에서 구현한 자료구조를 사용한다.  
<img src=https://github.com/YUYUJIN/animalPoseAPI/blob/main/pictures/dataqueue.png></img>  
최초에 Queue에 삽입하는 데이터 수를 6개에서 두 동작의 처리속도에 따라 유동적으로 조작하여 두 동장의 처리 속도를 보장한다.  
추가로 모델이 놓치는 프레임이 존재하여 모델의 성능에 영향이 갈 수 있어 테스트를 진행하였으나 1초마다 특정 수의 프레임의 평균이 5개의 시퀀스로 LSTM 모델의 입력으로 들어가는 상황이기에 큰 영향이 생기지 않았다.  
</details>

<details>
<summary>React 개발자와 협업</summary>

추가 프로젝트에서 React와 연동하였다. 첨부되지 않은 기존의 API는 Client 쪽에서 API를 사용함에 있어 제약사항이 있었다. Client에서 정보를 한번에 시각화하지 않으면 안된다거나 혹은 주기적인 API 호출이 힘든 경우, API 사용에 있어서 페이지 별로 제약이 존재하였다.  
이를 해결하기 위해 API를 대거 수정하고, React 개발자와 기능, 페이지 단위로 테스트를 진행하면서 스프린트 형식으로 API를 수정하면서 개발하였다.
</details>

## Produced by 푸루주투
<img src=https://github.com/YUYUJIN/animalPoseAPI/blob/main/pictures/logo.png style="width:100px; height:100px;"></img>  
team. 푸루주투 
