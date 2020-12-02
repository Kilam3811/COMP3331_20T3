def checkCredentialUserName(userName):
    with open("credentials.txt",'r+') as credentials:
        for accounts in credentials:
            #True if there is a match in the database
            if(accounts.split()[0] == userName):return True
    #False otherwise
    credentials.close()
    return False
def checkCredentialAccount(userName,password):
    with open("credentials.txt",'r+') as credentials:
        for accounts in credentials:
            #True if there is a match in the database
            account = accounts.split()
            #print(account[0],account[1],userName,password)
            if(account[0] == userName and account[1] == password):return True
    #False otherwise
    credentials.close()
    return False
def addToCredentials(userName,password):
    with open("credentials.txt",'a') as credentials:
        credentials.write('\n'+ userName + ' ' + password)
    credentials.close()