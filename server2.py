from os import system
import socket 
import threading 
from queue import Queue 
import json
import time
import random
import sys
import logging

# JSON 파일 open
with open('./JSON/server/Request.json', 'r', encoding='UTF-8') as f:
    STATE_REQUEST = json.load(f)
with open('./JSON/server/Move.json', 'r', encoding='UTF-8') as f:
    MOVE_JSON = json.load(f)

# 로그 저장 text
now = time.strftime('20%y%m%d %H%M%S')

alarm_f = open("./log/alarm/alarm" + now + ".txt","w", encoding='utf-8')
state_f = open("./log/state/state" + now + ".txt","w", encoding='utf-8')

logging.basicConfig(filename='./log/debug' + now + '.log',level=logging.DEBUG, encoding='utf-8')
 
# thread 종료
chk = True

# 클라이언트
clients = {}

# priority number
pr_num = 0

def make_route():
    # 맵 크기
    MAX_N = MAX_M = 30 
    direction_x = [1,0,-1,0]
    direction_y = [0,1,0,-1]

    x, y = random.sample(range(1,31),1)[0], random.sample(range(1,31),1)[0]
    BLOCKS = [str(x).zfill(4) + str(y).zfill(4)]
    for _ in range(random.sample(range(20, 30),1)[0]):
        while True:
            direction = random.sample(range(0,3),1)[0]
            if 0 < x + direction_x[direction] <= MAX_N and 0 < y + direction_y[direction] <= MAX_M:
                x, y = x + direction_x[direction], y + direction_y[direction]
                break
        BLOCKS.append(str(x).zfill(4) + str(y).zfill(4))
    return BLOCKS
temp = 0
def Send():
    global clients, pr_num, group
    global temp
    print('Thread Send Start') 
    while chk:
        try: #새롭게 추가된 클라이언트가 있을 경우 Send 쓰레드를 새롭게 만들기 위해 루프를 빠져나감 
            ns = time.time_ns()
            time.sleep(0.05)
            for conn in group:
                STATE_REQUEST['AGV_NO'] = clients[conn]['AGV_NO']
                STATE_REQUEST['PRIORITY_NO'] = pr_num + 1
                MOVE_JSON['AGV_NO'] = clients[conn]['AGV_NO']
                MOVE_JSON['BLOCKS'] = clients[conn]['BLOCKS']

                pr_num = pr_num + 1
                state = json.dumps(STATE_REQUEST,ensure_ascii=False)
                move = json.dumps(MOVE_JSON, ensure_ascii=False)
                conn.send((state+move).encode())
            print(ns - temp)
            temp = ns
        except: 
            pass 

print_dic = {}
def Recv(conn):
    global clients, print_dic

    AGV_NO = conn.recv(2048).decode()
    clients[conn] = {}
    clients[conn]['AGV_NO'] = AGV_NO
    clients[conn]['BLOCKS'] = make_route()
    
    while chk:
        data = conn.recv(2048).decode()
        data = json.loads(data)
        
        data_type = data['DATA_TYPE']
        if data_type == 'alarm':
            logging.info('alarm json -' + str(data))
            alarm_f.write(str(data) + '\n')
        
        if data_type == 'report':
            print_dic[data['PRIORITY_NO']] = str(data)

chk_dic = {}
def printRecv():
    global print_dic
    pr_now = 0
    while chk:
        time.sleep(0.05)
        if pr_now + 1 in print_dic:
            logging.info('state json -' + print_dic[pr_now+1])
            state_f.write(print_dic[pr_now+1] + '\n')
            del(print_dic[pr_now+1])
            pr_now = pr_now + 1

def input_exit_chk():
    global chk
    
    while chk:
        exit_chk = int(input())
        if exit_chk == 0:
            chk = False
            break

group = []
if __name__ == '__main__': 
    argument = sys.argv
    HOST = argument[1] if len(argument) == 2 else ''

    send_queue = Queue() 
    HOST = '' # 수신 받을 모든 IP를 의미 
    PORT = 5001 # 수신받을 Port 
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP Socket 
    logging.debug('Socket Created')

    server_sock.bind((HOST, PORT)) # 소켓에 수신받을 IP주소와 PORT를 설정 
    logging.debug('Socket Bind Complete')

    server_sock.listen(10) # 소켓 연결, 여기서 파라미터는 접속수를 의미 
    logging.debug('Socket Listening')

    count = 0

    # 종료 감지 스레드
    end_thread = threading.Thread(target=input_exit_chk)
    end_thread.start()

    #연결된 클라이언트의 소켓정보를 리스트로 묶기 위함 
    while chk:
        conn, addr = server_sock.accept() # 해당 소켓을 열고 대기 
        group.append(conn) #연결된 클라이언트의 소켓정보 
        count = count + 1
        
        #소켓에 연결된 모든 클라이언트에게 동일한 메시지를 보내기 위한 쓰레드(브로드캐스트) #연결된 클라이언트가 1명 이상일 경우 변경된 group 리스트로 반영 
        logging.debug('Connected ' + str(addr[0]) + ':' + str(addr[1]))
        if count == 1:
            thread1 = threading.Thread(target=Send, args=()) 
            thread1.start() #소켓에 연결된 각각의 클라이언트의 메시지를 받을 쓰레드 

            print_thread = threading.Thread(target=printRecv,)
            print_thread.start()

        thread2 = threading.Thread(target=Recv, args=(conn,)) 
        thread2.start()
            