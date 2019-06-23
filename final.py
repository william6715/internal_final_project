import RPi.GPIO as GPIO
import time

import requests

from http.server import BaseHTTPRequestHandler, HTTPServer
# import socketserver
import socket


class car_control(object):

    def __init__(self):
        self.Motor1A = 16
        self.Motor1B = 18
        self.Motor1E = 22

        self.Motor2A = 19
        self.Motor2B = 21
        self.Motor2E = 23
        #set 
        GPIO.setmode(GPIO.BOARD)

        GPIO.setup(self.Motor1A, GPIO.OUT)
        GPIO.setup(self.Motor1B, GPIO.OUT)
        GPIO.setup(self.Motor1E, GPIO.OUT)

        GPIO.setup(self.Motor2A, GPIO.OUT)
        GPIO.setup(self.Motor2B, GPIO.OUT)
        GPIO.setup(self.Motor2E, GPIO.OUT)

    def pause(self):
        GPIO.output(self.Motor1E, GPIO.LOW)
        GPIO.output(self.Motor2E, GPIO.LOW)

    def right(self):
        self.pause()
        GPIO.output(self.Motor1A, GPIO.LOW)
        GPIO.output(self.Motor1B, GPIO.HIGH)
        GPIO.output(self.Motor1E, GPIO.HIGH)
        GPIO.output(self.Motor2A, GPIO.HIGH)
        GPIO.output(self.Motor2B, GPIO.LOW)
        GPIO.output(self.Motor2E, GPIO.HIGH)

    def left(self):
        self.pause()
        GPIO.output(self.Motor1A, GPIO.HIGH)
        GPIO.output(self.Motor1B, GPIO.LOW)
        GPIO.output(self.Motor1E, GPIO.HIGH)
        GPIO.output(self.Motor2A, GPIO.LOW)
        GPIO.output(self.Motor2B, GPIO.HIGH)
        GPIO.output(self.Motor2E, GPIO.HIGH)

    def backward(self):
        self.pause()
        GPIO.output(self.Motor1A, GPIO.HIGH)
        GPIO.output(self.Motor1B, GPIO.LOW)
        GPIO.output(self.Motor1E, GPIO.HIGH)
        GPIO.output(self.Motor2A, GPIO.HIGH)
        GPIO.output(self.Motor2B, GPIO.LOW)
        GPIO.output(self.Motor2E, GPIO.HIGH)

    def forward(self):
        self.pause()
        GPIO.output(self.Motor1A, GPIO.LOW)
        GPIO.output(self.Motor1B, GPIO.HIGH)
        GPIO.output(self.Motor1E, GPIO.HIGH)
        GPIO.output(self.Motor2A, GPIO.LOW)
        GPIO.output(self.Motor2B, GPIO.HIGH)
        GPIO.output(self.Motor2E, GPIO.HIGH)

    def disconnect(self):
        self.pause()
        GPIO.cleanup()


target_ip = "http://172.20.10.12:5000/"
car_ID = None


# I put owner and car register together.
# Of course it can be seperated.
def register(ownername="new_owner", carname="new_car", car_age=2):
    # Owner part
    target = target_ip + "POST/user"
    data = {
        "name": ownername
    }
    r = requests.post(url=target, json=data)
    if r.status_code == 200:
        response = r.text.split()[2][1:-2]
        print("Onwer account:", response)
    else:
        print("Owner register fail!")
        return

    # car part
    target = target_ip + "POST/car"
    data = {
        "name": carname,
        "age": car_age,
        "owner": response
    }
    print(data)
    r = requests.post(url=target, json=data)
    if r.status_code == 201:
        print("Register success!")
        global car_ID
        print(r.text.split()[4][0:-1])
        car_ID = int(r.text.split()[4][0:-1])

        return True
    else:
        print("Car register fail!")
        print(r.status_code)
        return False


def auth_renter(car_id=0, renter_account=""):
    target = target_ip + "POST/car/authorize"
    data = {
        "id": car_id,
        "account": renter_account
    }
    r = requests.post(url=target, json=data)
    if r.status_code == 200:
        print("Auth success!")
        return True
    else:
        print("Auth fail!")
        return False


def return_car(car_id=0, account="", oil=10, crashes=0, rate=5):
    target = target_ip + "PUT/car/return"
    data = {
        "id": car_id,
        "account": account,
        "oil": oil,
        "crashes": crashes,
        "rate": rate
    }
    r = requests.put(url=target, json=data)
    if r.status_code == 200:
        print("Return success!")
        return True
    else:
        print("Return fail!")
        return False


# TCP Server for cellphone.
def start_tcp_server(ip, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.bind((ip, port))
    server.listen(5)
    print("[*] Listening on %s:%d" % (ip, port))

    client, addr = server.accept()
    print("[*] Accepted connection from: %s:%d" % (addr[0], addr[1]))

    '''
    # get renter name from cellphone and auth check to blockchain
    renter_name = client.recv(1024).decode()
    if renter_name:
        print("Received!")
        print(renter_name)
        renter_name = client.recv(1024).decode()
        print(renter_name)
        global car_ID
        if auth_renter(car_id=car_ID, renter_account=renter_name):
            client.sendall("Yes")
        else:
            client.sendall("No")
            return 0
    else:
        print("no receive name!")
        print(renter_name)
    '''

    # Start to control the car via cellphone
    start_time = time.time()
    a = car_control()

    while True:
        try:
            print("[*]Waiting for receive!")
            data = client.recv(1024)

            if not data:
                break

            print("[*]Client input:", data.decode())
            data = data.decode()
            if(data == 'W'):
                a.forward()
            elif(data == 'S'):
                a.backward()
            elif(data == 'A'):
                a.left()
            elif(data == 'D'):
                a.right()
            elif (data == 'P'):
                a.pause()
            elif (data == 'H'):
                a.disconnect()
                break
            else:
                print("Unknown command")

        except socket.error:
            print("[*]Error occur in socket part.")
            a.disconnect()
            break
    end_time = time.time()

    # send launch time to cellphone
    launch_time = "%d" % (end_time - start_time)
    client.sendall(launch_time.encode())
    
    client.close()
    print("Close connection.")
    

def websocket_server(ip, port):
    import asyncio
    import websockets
    
    async def show(websocket, path):
        '''
        # get renter account from cellphone and auth check to blockchain
        renter_acc = await websocket.recv()
        print("Received renter account:", renter_acc)
        global car_ID
        if auth_renter(car_id=car_ID, renter_account=renter_acc):
            await websocket.send("Yes")
        else:
            await websocket.send("No")
            asyncio.get_event_loop().stop()
        '''
        
        start_time = time.time()
        a = car_control()
        while True:
            try:
                data = await websocket.recv()
                print("Receive input:", data)
                
                if(data == 'W'):
                    a.forward()
                elif(data == 'S'):
                    a.backward()
                elif(data == 'A'):
                    a.left()
                elif(data == 'D'):
                    a.right()
                elif (data == 'P'):
                    a.pause()
                elif (data == 'H'):
                    a.disconnect()
                    break
                else:
                    print("Unknown command")
            except Exception:
                print("Disconnected.")
                a.disconnect()
                break
        end_time = time.time()
        gas = end_time - start_time()
        
        # Send launch time to cellphone.
        try:
            await websocket.send("%d" % gas)
        except:
            pass
        asyncio.get_event_loop().stop()
    
    start_server = websockets.serve(show, ip, port)
    asyncio.get_event_loop().run_until_complete(start_server)
    print("Websocket server created.")
    asyncio.get_event_loop().run_forever()
    print("Server closed.")


def launch():
    register()
    # start_tcp_server("localhost", 5000)
    websocket_server('192.168.1.115', 6000)

# start_tcp_server('172.20.10.2', 6000)
#websocket_server('192.168.1.115', 6000)
register()