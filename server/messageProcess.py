from checkCredential import *
import json
import re
import os
import base64

#Globally defined data structures
activeThreads = []
activeFiles = []

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
#Helper function to process the incoming packet
def handleMessageFromUser(data,connection_socket,client_address,activeClients,userNameToSocket,admin_passwd,file):
    global activeThreads

    #data = {'command':authentication,'userName':userName,'password':password}
    if(data['command'] == 'Authentication'):
        userName = data['userName']
        if(userName in activeClients):
            connection_socket.send(f"{userName} has already logged in!".encode())
            print(f"\n{userName} has already logged in!")
            return True
        #user name exists in the credential file
        if(checkCredentialUserName(userName)):
            connection_socket.send("Please enter your password: ".encode())
            password = connection_socket.recv(1024).decode()
            password = json.loads(password)['password']
            if(checkCredentialAccount(userName,password)):
                connection_socket.send("Welcome to the forum! You are good to go!".encode())
                userNameToSocket[client_address] = connection_socket
                activeClients.append(userName)
                print(f"\n{userName} logs in successfully")
            else:
                print("Incorrect password")
                connection_socket.send("Incorrect password".encode())
                return True
        #User not exist in the credential file
        else:
            connection_socket.send("Please enter your new password: ".encode())
            password = connection_socket.recv(1024).decode()
            password = json.loads(password)['password']
            #Log the record
            addToCredentials(userName,password)
            connection_socket.send("Welcome to the forum! You are good to go!".encode())
            userNameToSocket[client_address] = connection_socket
            activeClients.append(userName)
            print(f"{userName} logs in successfully")
    
    elif(data['command'] == 'XIT'):
        print()
        print(f"{data['userName']} has logged out\n")
        print("\nWaiting for clients...")
        activeClients.remove(data['userName'])
        print("\nCurrently alive user(s): "+ str(activeClients))
        userNameToSocket[client_address].send('Goodbye!'.encode())
        userNameToSocket[client_address].close()
        raise Exception
    elif (data['command'] == 'CRT'):
        threadName = data['arg0']
        issuedCom(data)
        try:
            with open(threadName,'x') as f:
                f.write("Thread creator: " + str(data['userName']))
            msg = "Thread " + threadName + " is created by " + data['userName']
            print()
            print(msg)
            activeThreads.append(threadName)
            userNameToSocket[client_address].send(msg.encode())
        except FileExistsError:
            msg ="\n"+"Thread " + threadName + " exists"
            print()
            print(msg)
            userNameToSocket[client_address].send(msg.encode())

    elif (data['command'] == 'LST'):
        issuedCom(data)
        if(not activeThreads):
            msg = 'No threads to list'
            userNameToSocket[client_address].send(msg.encode())
        else:
            content = 'The list of active threads:\n\n'
            for th in activeThreads:
                content = content + th + '\n'
            userNameToSocket[client_address].send(content.encode())
    elif (data['command'] == 'MSG'):
        threadName = data['arg0']
        postMsg = data['arg1']
        issuedCom(data)
        try:
            seq = 1
            with open(threadName,'rt') as f:
                f.readline()
                for line in f:
                    #Lines do not contatin
                    #i.g. 1 Yoda: msg
                    pattern = "^"+ str(seq) + " .+: "
                    if(re.search(pattern,line) is not None):
                        if(int(line.split()[0]) >= seq):
                            seq = int(line.split()[0]) + 1
            
            with open(threadName,'a') as f:
                msg = '\n' + str(seq) + ' ' + data['userName'] + ': ' + postMsg
                f.write(msg)
            msg = "Message posted to " + threadName + " by " + data['userName']
            print()
            print(msg)
            #activeThreads.append(threadName)
            userNameToSocket[client_address].send(msg.encode())
        except FileNotFoundError:
            msg ="\nThread " + threadName + " dose not exist"
            print("\n"+msg)
            userNameToSocket[client_address].send(msg.encode())
    elif (data['command'] == 'RDT'):
        threadName = data['arg0']
        issuedCom(data)
        try:
            #Read the content to client
            content = ''
            with open(threadName) as f:
                f.readline()
                for line in f:
                    content = content + line + "\n"
            msg = "Thread "+ threadName + " is read by " + data['userName']
            print()
            print(msg)
            if(not content):
                userNameToSocket[client_address].send("This thread has no messages to be read!".encode())
            else:
                userNameToSocket[client_address].send(content.encode())
        except FileNotFoundError:
            msg ="\nThread " + threadName + " dose not exist"
            print(msg)
            userNameToSocket[client_address].send(msg.encode())
    elif (data['command'] == 'EDT'):
        threadName = data['arg0']
        messageNum = data['arg1']
        messageFromU = data['arg2']
        #Looking for specific msg
        pattern = "^"+ messageNum + ' ' + data['userName'] +": "
        issuedCom(data)
        try:
            #Edit the content for client
            with open(threadName,'rt') as f:
                list_of_lines = f.readlines()
                if(len(list_of_lines) > 1):
                    targetIdx = None
                    for idx , line in enumerate(list_of_lines):
                        if(re.search(pattern,line) is not None):
                            targetIdx = idx
                            break
                    if(targetIdx is None):
                        msg = f"The message belongs to another user and cannot be edited OR the message number you specified can not be found"
                        print()
                        print("Message cannot be edited")
                    else:
                        list_of_lines[targetIdx] = messageNum + ' ' + data['userName'] + ': ' + messageFromU + '\n'
                        with open(threadName,'w') as f:
                            f.writelines(list_of_lines)
                        print(list_of_lines)
                        msg = "The message has been edited by " + data['userName']
                        print()
                        print("Message has been edited")
                else:
                    print(f"Thread {threadName} has no messages to be edited")
                    msg = "This thread has no message to edit.Please post a new message"
            #activeThreads.append(threadName)
            userNameToSocket[client_address].send(msg.encode())
        except FileNotFoundError:
            msg ="\nThread " + threadName + " dose not exist"
            print(msg)
            userNameToSocket[client_address].send(msg.encode())
    elif (data['command'] == 'DLT'):
        threadName = data['arg0']
        messageNum = data['arg1']
        pattern = "^"+ messageNum + ' ' + data['userName'] +": "
        #Looking for specific msg
        issuedCom(data)
        try:
            #DLT the content to client
            with open(threadName,'rt') as f:
                list_of_lines = f.readlines()
                if(len(list_of_lines) > 1):
                    targetIdx = None
                    ##Rearrange number
                    for idx, line in enumerate(list_of_lines):
                        if(re.search(pattern,line) is not None):
                            targetIdx = idx
                            break
                    if(targetIdx is None):
                        msg = f"The message belongs to another user and cannot be deleted OR the message number you specified can not be found"
                        print()
                        print("Message cannot be deleted")
                    else:
                        #Remove that msg
                        #list_of_lines.pop(targetIdx)
                        seq = int(messageNum)
                        pattern = "^"+ str(seq) + " .+: "
                        newList_of_lines = list_of_lines.copy()
                        print(newList_of_lines)
                        for idx, line in enumerate(list_of_lines[targetIdx:]):
                            #serach next avalible seq
                            if(re.search(pattern,line) is not None):
                                newList_of_lines[targetIdx + idx] = str(int(line.split()[0]) - 1) + ' ' + ' '.join(line.split()[1:]) + '\n'
                                #Looking for next next
                                seq = int(line.split()[0]) + 1
                                pattern = "^"+ str(seq) + " .+: "
                        
                        print(newList_of_lines[-1])

                        print(newList_of_lines)
                        newList_of_lines[-1] = newList_of_lines[-1].rstrip('\n')
                        
                        

                        if(len(newList_of_lines) == 1):
                            newList_of_lines[0] = newList_of_lines[0].strip('\n')
                        elif (targetIdx == len(newList_of_lines) - 1):
                            newList_of_lines[targetIdx-1] = newList_of_lines[targetIdx-1].rstrip('\n')

                        newList_of_lines.pop(targetIdx)

                        with open(threadName,'w') as f:
                            f.writelines(newList_of_lines)
                        msg = "The message has been deleted by " + data['userName']
                        print()
                        print("Message has been deleted")
                else:
                    print(f"Thread {threadName} has no messages to be deleted")
                    msg = "This thread has no message to be deleted.Please post a new message"
            userNameToSocket[client_address].send(msg.encode())
        except FileNotFoundError:
            msg ="\nThread " + threadName + " dose not exist"
            print(msg)
            userNameToSocket[client_address].send(msg.encode())
    elif (data['command'] == 'UPD'):
        threadName = data['arg0']
        fileName = data['arg1']
        issuedCom(data)
        if(threadName not in activeThreads):
            msg ="\nThread " + threadName + " dose not exist"
            print(msg)
            userNameToSocket[client_address].send(msg.encode())
        else:
            #You may assume that the file name will be unique for each thread
            #DLT the content to client
            with open(f"{threadName}-{fileName}",'wb') as f:
                f.write(file)

            with open(threadName,'a') as f:
                msg = f"\n{data['userName']} uploaded {fileName}" 
                f.write(msg)
            #Successs uploaded
            msg = f"{fileName} has been uploaded to thread {threadName} by {data['userName']}"
            print(msg)
            activeFiles.append(f"{threadName}-{fileName}")
            userNameToSocket[client_address].send(msg.encode())

    elif (data['command'] == 'DWN'):
        threadName = data['arg0']
        fileName = data['arg1']
        issuedCom(data)
        if(threadName not in activeThreads):
            msg ="Thread " + threadName + " dose not exist"
            print(msg)
            userNameToSocket[client_address].send(msg.encode())
        elif(f"{threadName}-{fileName}" not in activeFiles):
            msg =f"{fileName} does not exist in Thread {threadName}"
            print(msg)
            msg = f"File dose not exist in Thread {threadName}"
            userNameToSocket[client_address].send(msg.encode())
        else:
            with open(f"{threadName}-{fileName}",'rb') as f:
                s = bytes("DWN:OK",'utf-8') + f.read()
                userNameToSocket[client_address].send(s)
                #clientSocket.send(s)
            #Successs uploaded
            msg = f"{fileName} has been downloaded from thread {threadName} by {data['userName']}"
            print(msg)
            #userNameToSocket[client_address].send(json.dumps(data).encode())
    elif (data['command'] == 'RMV'):
        threadName = data['arg0']
        issuedCom(data)
        if(threadName not in activeThreads):
            msg ="Thread " + threadName + " dose not exist"
            print(msg)
            userNameToSocket[client_address].send(msg.encode())
        else:
            #Thread existence checked
            with open(threadName) as f:
                if(f.readline().split()[2] != data['userName']):
                    msg ="Thread " + threadName + " can not be removed"
                    print(msg)
                    msg = "The thread was created by another user and cannot be removed!!"
                    userNameToSocket[client_address].send(msg.encode())
                else:
                    #Remove from active thread list
                    activeThreads.remove(threadName)
                    pattern = "^" + threadName + ".*"
                    #Delete the thread
                    directory = os.fsencode(os.getcwd())
                
                    for file in os.listdir(directory):
                        filename = os.fsdecode(file)
                        #print(filename)
                        if(re.search(pattern,filename)):
                            if(filename in activeFiles):
                                activeFiles.remove(filename)
                            os.remove(filename)
                    msg = f"Thread {threadName} has been removed by {data['userName']}"
                    print(msg)
                    userNameToSocket[client_address].send(msg.encode())
    elif (data['command'] == 'SHT'):
        issuedCom(data)
        if(data['arg0'] != admin_passwd):
            msg = "Incorrect admin password"
            print(msg)
            userNameToSocket[client_address].send(msg.encode())
        else:
            print("Server shutting down")
            msg = "Goodbye. Server shutting down"

            #Delete all the files from the thread
            directory = os.fsencode(os.getcwd())

            for file in os.listdir(directory):
                filename = os.fsdecode(file)
                if(filename in activeThreads or filename in activeFiles or filename == 'credentials.txt'):
                    if(filename in activeFiles):
                        activeFiles.remove(filename)
                    os.remove(filename)
            activeClients.clear()
            activeFiles.clear()
            for csS in userNameToSocket:
                userNameToSocket[csS].send(msg.encode())
                userNameToSocket[csS].close()
            return False
    return True
def issuedCom(data):
    print("\n" + data['userName'] + " issued " + data['command'] + " command" + "\n")