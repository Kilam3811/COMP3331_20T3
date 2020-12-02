#Python 3
#coding: utf-8
from socket import *
import threading
from _thread import *
import time
import datetime as dt
import sys
import json
import re
#User defined modules
from messageProcess import *
#Define connection (socket) parameters
#Address + Port no
#Server would be running on the same host as Client
serverName = 'localhost'

#Multithreading
t_lock=threading.Condition()

#Stores all the active users + password combination
activeClients=[]
# would communicate with clients after every second
UPDATE_INTERVAL= 0.5
userNameToSocket = dict()


if (len(sys.argv) < 3):
	print("Usage: python3 server.py server_port admin_passwd")
	sys.exit()
else:
	"""
	This is the port number which the server will use to communicate with
the clients. Recall that a TCP socket is NOT uniquely identified by the server port
number. It should thus be possible for multiple TCP connections to use the same serverside port number
	"""
	serverPort = int(sys.argv[1])

	"""
	This is the admin password for the server. It is required to shut down the
server (see operation SHT later).
	"""
	admin_passwd = str(sys.argv[2])

"""
This is welcome socket listening for incoming connection.
"""
def recv_handler():
    global t_lock
    global clients
    global serverSocket
    print ('Server started!')
    print ("Restart and destroy forum")
    print ('Waiting for clients...')

    while(1):
        connection_socket, client_address = serverSocket.accept()
        """Received connection from the client, now we know who we are talking with
        get lock as we might me accessing some shared data structures
        create a new thread for the client socket
        """
        socket_handler = connection_handler(connection_socket, client_address)
        socket_thread = threading.Thread(name=str(client_address), target=socket_handler)
        socket_thread.daemon = True
        socket_thread.start()



# handles all out going data that can not be handled by recev_dandler
def send_handler():
    global t_lock
    global clients
    global serverSocket
    #Go through the list of the subscribed clients and send them the current time after every 1 second
    while 1:
        #get lock
        with t_lock:
            #notify other threads
            t_lock.notify()
        #sleep for UPDATE_INTERVAL
        time.sleep(UPDATE_INTERVAL)

# return a function as connection handler for a specific socket for multi threading
alive = True
def connection_handler(connection_socket, client_address):
    def real_connection_handler():
        global alive
        while alive:

            message = recvall(connection_socket)
            
            # received data from the client, now we know who we are talking with
            # get lock as we might me accessing some shared data structures
            with t_lock:
                #For upload command , we have to transfer bytes over
                if(b'UPD' in message):
                    connection_socket.send("file recevied".encode())
                    temp = ''
                    
                    temp = connection_socket.recv(1024).decode()
                    data = json.loads(temp)
                    try:
                        alive = handleMessageFromUser(data,connection_socket,client_address,activeClients,userNameToSocket,admin_passwd,message[4:])
                    except Exception:
                        break
                else:
                    message = message.decode()
                    if(message == 'Are u alive?'):
                        connection_socket.send("I am alive".encode())
                    else:
                        #Handle login connections from the clients (including thoses in credential and new users)
                        data = json.loads(message)
                        try:
                            alive = handleMessageFromUser(data,connection_socket,client_address,activeClients,userNameToSocket,admin_passwd,None)
                        except Exception:
                            break
                
                # notify the thread waiting
                t_lock.notify()
        #Clean up client socket if breaks the loop
        try:
            del userNameToSocket[client_address]
            #print("Current connected socket(s): " + str(userNameToSocket))
        except KeyError as key:
            print(f"This socket is never existed and got {key}")
    return real_connection_handler

# Bind to the port
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((serverName, serverPort))
serverSocket.listen(5)
recv_thread = threading.Thread(name="RecvHandler", target=recv_handler)
recv_thread.daemon = True
recv_thread.start()

send_thread = threading.Thread(name="SendHandler", target=send_handler)
send_thread.daemon = True
send_thread.start()
#Indicates server is alive



if __name__ == "__main__":
    #main loop
    while alive:
        time.sleep(0.1)
