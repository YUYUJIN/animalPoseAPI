import pymysql
from datetime import datetime, timedelta

label_dict={
    'REST':'쉬기','SITDOWN':'앉기','TAILING':'꼬리흔들기','WALKRUN':'걷기/뛰기','ARMSTRETCH':'기지개','PLAYING':'놀기','GROOMING':'그루밍','FOOTUP':'손','BODYSCRATCH':'긁기','BODYSHAKE':'몸떨기','UNKNOWN':'없음'
}

class Database:
    def __init__(self,host,port,user,password,db_name):
        print(host)
        # MySQL Connection 연결
        self.connect = pymysql.connect(host=host,
                                       port=port,
                                      user=user,
                                      password=password,
                                      db=db_name, charset='utf8')  # 한글처리 (charset = 'utf8')

        # Connection 으로부터 Cursor 생성
        self.cursor = self.connect.cursor()

    def getData(self, table_name, targets='*',option=None):
        curs = self.cursor

        if option == None:
            sql = f"select {targets} from {table_name};"
        else:
            sql = f"select {targets} from {table_name} where {option};"

        curs.execute(sql)
        rows = curs.fetchall()
        self.connect.commit()
        # self.connect.close()
        return rows

    def insData(self, table_name,values):
        curs = self.cursor
        
        options=''
        for t in values:
            options+='%s,'

        sql = f"INSERT INTO {table_name} " \
              f"VALUES (default,{options} default)"
        # print(sql)
        curs.execute(sql, values)
        self.connect.commit()
        # self.connect.close()

    def updData(self, table_name, values):
        curs = self.cursor
        option = ''
        for o in values:
            option += '%s,'
        option = option[:-1]

        sql = f"update INTO {table_name}   " \
              f"VALUES ({option});"
        curs.execute(sql, values)
        self.connect.commit()
        # self.connect.close()

    def delData(self, table_name, animal_id):
        curs = self.cursor
        sql = f'delete from {table_name} where album_id=%s'
        curs.execute(sql, animal_id)
        self.connect.commit()
        # self.connect.close()

    # def getCountByTimeRange(self, table_name):
    #     curs = self.connect.cursor()

    #     # animal_id의 최소값과 최대값에 해당하는 데이터의 animal_timestamp 값을 가져옴
    #     # sql = f"SELECT MIN(album_time), MAX(album_time) FROM {table_name}"
    #     # curs.execute(sql)
    #     # animal_timestamps = curs.fetchone()
    #     # start_timestamp = animal_timestamps[0]
    #     # end_timestamp = animal_timestamps[1]
    #     time=f'{datetime.datetime.now()}'.split(' ')
    #     today=time[0]
    #     hour=time[1].split(':')[0]
    #     # time range 내 animal_act별 count 계산
    #     sql = f"SELECT album_type, album_act, HOUR(album_time), COUNT(*) FROM {table_name} " \
    #           f"WHERE album_time like \'{today}%\' GROUP BY album_type, album_act, HOUR(album_time)"
    #     print(sql)
    #     curs.execute(sql)
    #     data = curs.fetchall()

    #     # 결과를 json 파일로 저장
    #     result = {}
    #     for row in data:
    #         animal_type = row[0]
    #         animal_act = row[1]
    #         hour = str(row[2])
    #         count = row[3]
    #         if animal_type not in result:
    #             result[animal_type] = {}
    #         if animal_act not in result[animal_type]:
    #             result[animal_type][animal_act] = {}
    #         result[animal_type][animal_act][hour] = count

    #     return hour,result

    def today(self, table_name, animal_type):
        curs = self.cursor

        # animal_id의 최대값에 해당하는 데이터의 animal_timestamp 값을 가져옴
        sql = f"SELECT MAX(album_time) FROM {table_name}"
        curs.execute(sql)
        max_animal_timestamp = curs.fetchone()[0]

        # 최대 animal_timestamp 기준으로 24시간 이전 시간대 구하기
        start_time = max_animal_timestamp - timedelta(days=1)
        end_time = max_animal_timestamp

        # time range 내 animal_act별 count 계산
        sql = f"SELECT album_type, album_act, HOUR(album_time), COUNT(*) FROM {table_name} " \
            f"WHERE album_type = \'{animal_type}\' AND album_time >= %s AND album_time < %s GROUP BY album_act, HOUR(album_time)"
        curs.execute(sql, (start_time, end_time))
        data = curs.fetchall()

        result = []
        for row in data:
            animal_act = row[1]
            hour = row[2]
            count = row[3]
            found = False
            for item in result:
                if item['id'] == animal_act:
                    found = True
                    item['data'].append({'x': str(hour), 'y': count})
                    break
            if not found:
                result.append({'id': animal_act, 'label':label_dict[animal_act], 'data': [{'x': str(hour), 'y': count}]})

        output = {
            'keys': 'day',
            'label': '하루',
            'data': result
        }
        return output
    
    def dailyPi(self, table_name, animal_type):
        curs = self.cursor

        # animal_id의 최소값과 최대값에 해당하는 데이터의 animal_timestamp 값을 가져옴
        sql = f"SELECT MIN(album_time), MAX(album_time) FROM {table_name}"
        curs.execute(sql)
        animal_timestamps = curs.fetchone()
        start_timestamp = animal_timestamps[0]
        end_timestamp = animal_timestamps[1]

        # time range 내 animal_act별 count 계산
        sql = f"SELECT album_type, album_act, DATE(album_time), COUNT(*) FROM {table_name} " \
            f"WHERE album_type = \'{animal_type}\' AND album_time >= %s AND album_time <= %s GROUP BY album_act"
        curs.execute(sql, (start_timestamp, end_timestamp))
        data = curs.fetchall()
        result = []
        for row in data:
            animal_act = row[1]
            count = row[3]
            result.append({'id': animal_act, 'label':label_dict[animal_act], 'value': count})

        output = {
            'keys': 'day',
            'data': result
        }
        return output
        
    def weeklyPi(self, table_name, animal_type):
        curs = self.cursor

        # animal_id의 최소값과 최대값에 해당하는 데이터의 animal_timestamp 값을 가져옴
        sql = f"SELECT MIN(album_time), MAX(album_time) FROM {table_name}"
        curs.execute(sql)
        animal_timestamps = curs.fetchone()
        start_timestamp = animal_timestamps[0]
        end_timestamp = animal_timestamps[1]

        # time range 내 animal_act별 count 계산
        sql = f"SELECT album_type, album_act, DATE(album_time), HOUR(album_time), COUNT(*) " \
            f"FROM {table_name} " \
            f"WHERE album_type = \'{animal_type}\' AND album_time >= %s AND album_time <= %s " \
            f"GROUP BY album_type, album_act, DATE(album_time), HOUR(album_time)"
        curs.execute(sql, (start_timestamp, end_timestamp))
        data = curs.fetchall()

        # 주 단위 데이터 생성
        result = {}
        for row in data:
            animal_type = row[0]
            animal_act = row[1]
            date = datetime.strptime(str(row[2]), '%Y-%m-%d')
            hour = str(row[3])
            count = row[4]

            # 주 단위 데이터 생성
            week_start = (date - timedelta(days=date.weekday())).strftime('%Y-%m-%d')
            if week_start in result:
                if animal_act in result[week_start]:
                    result[week_start][animal_act] += count
                else:
                    result[week_start][animal_act] = count
            else:
                result[week_start] = {animal_act: count}

        data = [{'id': animal_act,
                 'label':label_dict[animal_act],
                 'value': sum(result[week_start].get(animal_act, 0) for week_start in result)} for
                    animal_act in
                    set(animal_act for week_start in result for animal_act in result[week_start])]

        output = {
            'keys': 'week',
            'data': data
        }
        return output
    
    def monthlyPi(self, table_name, animal_type):
        curs = self.cursor

        # animal_id의 최소값과 최대값에 해당하는 데이터의 animal_timestamp 값을 가져옴
        sql = f"SELECT MIN(album_time), MAX(album_time) FROM {table_name}"
        curs.execute(sql)
        animal_timestamps = curs.fetchone()
        start_timestamp = animal_timestamps[0]
        end_timestamp = animal_timestamps[1]

        # time range 내 animal_act별 count 계산
        sql = f"SELECT album_type, album_act, YEAR(album_time), MONTH(album_time), HOUR(album_time), COUNT(*) " \
            f"FROM {table_name} " \
            f"WHERE album_type = \'{animal_type}\' AND album_time >= %s AND album_time <= %s " \
            f"GROUP BY album_type, album_act, YEAR(album_time), MONTH(album_time), HOUR(album_time)"
        curs.execute(sql, (start_timestamp, end_timestamp))
        data = curs.fetchall()

        # 월 단위 데이터 생성
        result = {}
        for row in data:
            animal_type = row[0]
            animal_act = row[1]
            year = str(row[2])
            month = str(row[3])
            hour = str(row[4])
            count = row[5]

            # 월 단위 데이터 생성
            month_start = f"{year}-{month}-01"
            if month_start in result:
                if animal_act in result[month_start]:
                    result[month_start][animal_act] += count
                else:
                    result[month_start][animal_act] = count
            else:
                result[month_start] = {animal_act: count}

        data = [{'id': animal_act, 'label':label_dict[animal_act],'value': sum(result[month_start].get(animal_act, 0) for month_start in result)} for
                animal_act in set(animal_act for month_start in result for animal_act in result[month_start])]

        output = {
            'keys': 'month',
                'data': data
            }
        return output

    def getAlbumList(self,category):
        curs = self.cursor

        sql = f"select album_act,album_address from album where album_type=\'{category}\';"

        curs.execute(sql)
        rows = curs.fetchall()
        self.connect.commit()

        if category=='cat':
            result={'REST':[],'SITDOWN':[],'TAILING':[],'WALKRUN':[],'ARMSTRETCH':[],'PLAYING':[],'GROOMING':[]}
        else:
            result={'REST':[],'SITDOWN':[],'TAILING':[],'WALKRUN':[],'FOOTUP':[],'BODYSCRATCH':[],'BODYSHAKE':[]}
        for row in reversed(rows):
            if len(result[row[0]])<20:
                result[row[0]].append(row[1])
        # self.connect.close()
        return result

    def db_disconnect(self):
        self.connect.close()

    def __del__(self):
        self.db_disconnect()