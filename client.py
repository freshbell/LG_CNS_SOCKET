import socket 
import threading 
import json
import time
from collections import deque
import random
import sys

# JSON 파일 open
with open('./JSON/client/Report.json', 'r', encoding='UTF-8') as f:
    STATE_JSON = json.load(f)
with open('./JSON/client/Alarm.json', 'r', encoding='UTF-8') as f:
    ALARM_JSON = json.load(f)

# 알람 전송
ALARM_CD_LIST = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
ALARM_CD_USED = deque([])
temp_end_alarm = 10
temp_start_alarm = 10
ALARM_REPORT_JSON = {
    'DATA_TYPE': 'alarm',
    'AGV_NO': 'TEMP',
    'ALARMS': []
}
cnt = 0

# 랜덤 ALARM_CD
def random_alarm():
    global temp_end_alarm, temp_start_alarm

    temp_start_alarm = random.choice(ALARM_CD_LIST)
    ALARM_CD_LIST.remove(temp_start_alarm)
    ALARM_CD_USED.append(temp_start_alarm)
    
    # 알람이 발생하고 5초 후 해제
    if(len(ALARM_CD_USED) == 6):
        temp_end_alarm = ALARM_CD_USED.popleft()
        ALARM_CD_LIST.append(temp_end_alarm)

    ALARM_JSON['ALARMS'][temp_start_alarm]['ALARM_STATUS'] = 1
    ALARM_JSON['ALARMS'][temp_start_alarm]['OCCUR_DT'] = time.strftime('20%y%m%d %H:%M:%S')
    ALARM_JSON['ALARMS'][temp_start_alarm]['END_DT'] = None

    ALARM_REPORT_JSON['ALARMS'] = []
    if(temp_end_alarm != 10):
        ALARM_REPORT_JSON['ALARMS'].append(ALARM_JSON['ALARMS'][temp_end_alarm])
        ALARM_JSON['ALARMS'][temp_end_alarm]['END_DT'] = time.strftime('20%y%m%d %H:%M:%S')
        ALARM_JSON['ALARMS'][temp_end_alarm]['ALARM_STATUS'] = 0

    ALARM_REPORT_JSON['ALARMS'].append(ALARM_JSON['ALARMS'][temp_start_alarm])

    return ALARM_REPORT_JSON

def Send(client_sock): 
    client_sock.send(AGV_NO.encode())
    while True: 
        time.sleep(1)
        send_data = json.dumps(random_alarm(),ensure_ascii=False).encode()
        client_sock.send(send_data)

def Recv(client_sock): 
    while True:
        recv_data = client_sock.recv(2048).decode() 
        print(recv_data)
        try:
            recv_data = recv_data.split('}')
            state_data = json.loads(recv_data[0] + '}')
            move_data = json.loads(recv_data[1] + '}')

            if move_data['DATA_TYPE'] == 'moveCommand':
                move_avg(move_data)

            if state_data['DATA_TYPE'] == 'reportRqst':
                client_sock.send(json.dumps(STATE_JSON,ensure_ascii=False).encode())
  
        except:
            # 기존 코드
            '''recv_data = json.loads(recv_data)
            data_type = recv_data['DATA_TYPE']
            if data_type == 'moveCommand':
                pass
            elif data_type == 'reportRqst':
                client_sock.send(json.dumps(STATE_JSON,ensure_ascii=False).encode())'''
            pass

def move_avg(move_data):
    global cnt    

    length=len(move_data['BLOCKS'])
    if cnt+1<length: cnt+=1
    else: cnt=0

    STATE_JSON['LOCATION'] = move_data['BLOCKS'][cnt]

#TCP Client 
if __name__ == '__main__': 
    argument = sys.argv
    AGV_NO = argument[1]
    
    server = argument[2] if len(argument) == 3 else '0'

    if server == '0':
        Host = 'localhost'
    else:
        Host = '13.124.72.207'

    STATE_JSON['AGV_NO'] = AGV_NO
    ALARM_REPORT_JSON['AGV_NO'] = AGV_NO

    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    Port = 5000
    client_sock.connect((Host, Port))
    print('Connecting to ', Host, Port)
    
    send_thread = threading.Thread(target=Send, args=(client_sock, )) 
    send_thread.start()
    
    recv_thread = threading.Thread(target=Recv, args=(client_sock, )) 
    recv_thread.start()
