#Use Python3
#coding: utf-8
from socket import *
import sys
import time
import json
import threading
import select
#Define connection (socket) parameters
#Address + Port no
#Server would be running on the same host as Client

#This client program can be tested in different directories to the server.

t_lock=threading.Condition()
UPDATE_INTERVAL= 0.5
alive = True
if (len(sys.argv) != 3):
    print("Usage: python3 client.py server_IP server_port")
    sys.exit()
else:
    """
    this is the IP address of the machine on which the server is running.
    """
    server_IP = str(sys.argv[1])

    """
     this is the port number being used by the server. This argument should
be the same as the first argument of the server.
    """
    serverPort = int(sys.argv[2])
clientSocket = None

#Application protocol msg format in JSON
commandMsg = {}
avaCommands ='''
Enter one of the following commands: CRT,
MSG, DLT, EDT, LST, RDT, UPD, DWN, RMV,
XIT, SHT: '''
commandSet = {'CRT',
'MSG', 'DLT', 'EDT', 'LST', 'RDT', 'UPD', 'DWN', 'RMV',
'XIT', 'SHT'}
auth = False

def recv_handler():
    global t_lock
    global clientSocket
    global alive
    #print ('Client started!')
    while alive:
        with t_lock:
            if(clientSocket.fileno != -1):
                try:
                    #Heart beat signal
                    clientSocket.send("Are u alive?".encode())
                    data = clientSocket.recv(1024)
                    #print(data)
                    if(b'DWN' not in data):
                        if(not data):
                            print("\n\n\nGoodbye. Server shutting down")
                            alive = False
                            break
                        else:
                            data = data.decode()
                            if(data == "I am alive"):
                                #print(data)
                                pass
                except Exception:
                    print("\n\n\nGoodbye. Server shutting down")
                    alive = False
                    break
            t_lock.notify()
        time.sleep(UPDATE_INTERVAL)

def userAuth():
    global clientSocket
    global auth
    while(1):
        with t_lock:
            userName = input('Please enter your username: ')
            print()
            commandMsg['command'] = 'Authentication'
            commandMsg['userName'] = userName
            clientSocket.send(json.dumps(commandMsg).encode('utf-8'))

            response = clientSocket.recv(1024).decode('utf-8')
            if(response == f'{userName} has already logged in!'):
                print('\n' + response)
            else:
                password = input(response)
                print()
                commandMsg['password'] = password
                clientSocket.send(json.dumps(commandMsg).encode('utf-8'))
                response = clientSocket.recv(1024).decode('utf-8')
                if(response == "Welcome to the forum! You are good to go!"):
                    print(response)
                    auth = True
                    break
                else:
                    print(response + ", please enter again!\n")
            t_lock.notify()
        #time.sleep(UPDATE_INTERVAL)

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((server_IP, serverPort))

def recvall(sock):
    BUFF_SIZE = 4096 # 4 KiB
    data = b''
    while True:
        part = sock.recv(BUFF_SIZE)
        data += part
        if len(part) < BUFF_SIZE:
            # either 0 or end of data
            break
    return data
def mainThread():
    global clientSocket
    global alive
    global auth
    try:
        userAuth()
        while(1):
            #with t_lock:
            stdin = input(avaCommands).split()
            #Error checking
            if(not stdin or stdin[0] not in commandSet):
                print()
                print('Invalid command.Please follow the instructions!')
                continue

            #Grab the command
            commandMsg['command'] = stdin[0]
            #CRT
            if(commandMsg['command'] == 'CRT'):
                if(len(stdin) != 2):
                    print()
                    print("Invalid argument for CRT\nTry: CRT threadTitle")
                    continue
                commandMsg['arg0'] = stdin[1]
            #XIT
            elif(commandMsg['command'] == 'XIT'):
                if(len(stdin) != 1):
                    print()
                    print("Invalid argument for XIT. XIT does not take any arguments")
                    continue
            elif (commandMsg['command'] == 'LST'):
                if(len(stdin) != 1):
                    print()
                    print("Invalid argument for LST. LST does not take any arguments")
                    continue
            elif (commandMsg['command'] == 'MSG'):
                if(len(stdin) < 3):
                    print()
                    print("Invalid argument for MSG\nTry: MSG threadTitle message")
                    continue
                commandMsg['arg0'] = stdin[1]
                commandMsg['arg1'] = ' '.join(stdin[2:])
            elif (commandMsg['command'] == 'RDT'):
                if(len(stdin) != 2):
                    print()
                    print("Invalid argument for RDT\nTry: RDT threadTitle")
                    continue
                commandMsg['arg0'] = stdin[1]
            elif (commandMsg['command'] == 'EDT'):
                if(len(stdin) < 4):
                    print()
                    print("Invalid argument for EDT\nTry: EDT threadTitle messagenumber message")
                    continue
                if(not str(stdin[2]).isnumeric()):
                    print()
                    print("Message number has to be postive integer!")
                    continue
                commandMsg['arg0'] = stdin[1]
                commandMsg['arg1'] = stdin[2]
                commandMsg['arg2'] = ' '.join(stdin[3:])
            elif (commandMsg['command'] == 'DLT'):
                if(len(stdin) != 3):
                    print()
                    print("Invalid argument for DLT\nTry: DLT threadTitle messagenumber")
                    continue
                if(not str(stdin[2]).isnumeric()):
                    print()
                    print("Message number has to be postive integer!")
                    continue
                commandMsg['arg0'] = stdin[1]
                commandMsg['arg1'] = stdin[2]
            #Handle all the input parameters if any
            elif (commandMsg['command'] == 'UPD'):
                if(len(stdin) < 3):
                    print()
                    print("Invalid argument for UPD\nTry: UPD threadTitle filename")
                    continue
                commandMsg['arg0'] = stdin[1]
                commandMsg['arg1'] = stdin[2]
            elif (commandMsg['command'] == 'DWN'):
                if(len(stdin) < 3):
                    print()
                    print("Invalid argument for DWN\nTry: DWN threadTitle filename")
                    continue
                commandMsg['arg0'] = stdin[1]
                commandMsg['arg1'] = stdin[2]
            elif (commandMsg['command'] == 'RMV'):
                if(len(stdin) != 2):
                    print()
                    print("Invalid argument for RMV\nTry: RMV threadTitle")
                    continue
                commandMsg['arg0'] = stdin[1] 
            elif (commandMsg['command'] == 'SHT'):
                if(len(stdin) != 2):
                    print()
                    print("Invalid argument for SHT\nTry: SHT admin_password")
                    continue
                commandMsg['arg0'] = stdin[1]
            
            if(commandMsg['command'] == 'UPD'):
                #print(commandMsg)
                with open(commandMsg['arg1'],'rb') as f:
                    s = bytes("UPD:",'utf-8') + f.read()
                    clientSocket.send(s)
            else:
                #print(commandMsg)
                clientSocket.send(json.dumps(commandMsg).encode())

            #DWN needs to receive bytes from server which can not be decoded
            if(commandMsg['command'] == 'DWN'):
                response = recvall(clientSocket)
                if(b"DWN:OK" in response):
                    with open(commandMsg['arg1'],'wb') as f:
                        f.write(response[6:])
                    print(f"\n{commandMsg['arg1']} downloaded successfully from {commandMsg['arg0']} thread")
                elif(response.decode() == "I am alive"):
                    #Wait for response from the server
                    response = clientSocket.recv(1024)
                    with open(commandMsg['arg1'],'wb') as f:
                        f.write(response[6:])
                    print(f"\n{commandMsg['arg1']} downloaded successfully from {commandMsg['arg0']} thread")
               
           
           
            #Other commands are able to be decoded
            else:
                response = recvall(clientSocket).decode('utf-8')
                if(response == "I am alive"):
                    response = clientSocket.recv(1024).decode('utf-8')
                if(commandMsg['command'] == 'XIT' and response == 'Goodbye!'):
                    print(f"\n{response}")
                    alive = False
                    break
                elif (commandMsg['command'] == "SHT" and response == "Goodbye. Server shutting down"):
                    print(f"\n{response}")
                    alive = False
                    break
                elif (commandMsg['command'] == 'UPD' and response == 'file recevied'):
                    clientSocket.send(json.dumps(commandMsg).encode())
                    print(f"\n{commandMsg['arg1']} uploaded successfully to {commandMsg['arg0']} thread")
                else:
                    print("\n" + response + "\n")

    except Exception as e:
        print(f"Can not develope TCP connection :) with exception:\n {e}")
    finally:
        if(clientSocket):
            clientSocket.close()

recThread = threading.Thread(name="recv_handler", target=recv_handler)
recThread.daemon = True
recThread.start()

mainThread = threading.Thread(name="mainThread", target=mainThread)
mainThread.daemon = True
mainThread.start()



if __name__ == "__main__":
    while alive:
        time.sleep(0.1)