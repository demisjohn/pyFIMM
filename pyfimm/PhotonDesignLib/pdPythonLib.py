# pdPythonLib version 1.6
# Command Line Interface with Python for Photon Design products
from string import *
from socket import *
from struct import *
from math import ceil
from time import sleep
import os
import re
import __main__
import types

INTBUFFSIZE = 20 #tcp/ip buffer length defined in the application
portsTaken = []#list of ports that are already taken
nextPortAvailable = 5101
CONNECTIONATTEMPTS = 10
MaxBuffSize = 4096 #maximum data size that can be retrieved at once (recommended values: 4096 (more stable) or 8192 (faster))
delay = 0.01 #delay (in s) between two batches of data (recommended values: 0.01 (more stable) or 0.001 (faster))

def IsPortAvailable(portNo):
    global portsTaken
    a = 1
    if (len(portsTaken)==1):
        if (portNo == portsTaken[0]):
            return 0
    for i in range(0,len(portsTaken)):
        if (portNo==portsTaken[i]):
            a=0
    return a

def getNextAvailablePort():
    global nextPortAvailable
    a = 0
    while (1):
        a = IsPortAvailable(nextPortAvailable)
        if (a==1):
            break
        nextPortAvailable = nextPortAvailable + 1
    return nextPortAvailable 

def getNumOrStr(msgstr):
    if (msgstr[0]=='('):
        reidx = find(msgstr,',')
        imidx = find(msgstr,')',0)
        try:
            rebit = float(msgstr[1:reidx])
        except:
            return msgstr
        try:
            imbit = float(msgstr[reidx+1:imidx])
        except:
            return msgstr
        return rebit + imbit*1j
    retval = None
    nlidx = find(msgstr,'\n')
    if (nlidx!=-1):
        recmsg2 = msgstr[0:nlidx]
    else:
        recmsg2 = msgstr
    try:
        retval = float(recmsg2)
    except:
        retval = msgstr
    return retval

def InterpretString1(commStr,varList):
    currIdx = 0
    nextIdx = 0
    noExpr = 0
    while (1):
        currIdx = find(commStr,'{',currIdx)
        nextIdx = find(commStr,'}',nextIdx)
        if ((currIdx==-1) or (nextIdx==-1)):
            break
        expression = commStr[currIdx+1:nextIdx]
        #Now find '%' and replace with object values
        idxtemp = 0
        while (1):
            idxtemp = find(expression,'%',idxtemp)
            if idxtemp==-1:
                break
            expression = expression[0:idxtemp] + repr(varList[noExpr]) + expression[idxtemp+1:]
            noExpr = noExpr + 1
        subobj = eval(expression,__main__.__dict__)
        if (type(subobj)==types.StringType):
            commStr = commStr[0:currIdx] + subobj + commStr[nextIdx+1:]
        else:
            commStr = commStr[0:currIdx] + repr(subobj) + commStr[nextIdx+1:]
    return commStr

def InterpretString(commStr,varList):
    commStr1 = ""
    commStr2 = ""
    currIdx = 0
    nextIdx = 0
    isStringDone = 0
    while (isStringDone!=1):
        nextIdx = find(commStr,'"',currIdx)
        if (nextIdx==-1):
            isStringDone=1
            commStr1 = commStr[currIdx:len(commStr)]
            commStr2 = commStr2 + InterpretString1(commStr1,varList)
        else:
            commStr1 = commStr[currIdx:nextIdx]
            commStr2 = commStr2 + InterpretString1(commStr1,varList)
            currIdx = find(commStr,'"',nextIdx+1) #Must have open quotes and end quotes!!!
            if (currIdx==-1):
                print "Error interpreting command\n"
                return commStr
            commStr2 = commStr2 + commStr[nextIdx:currIdx+1]
            currIdx = currIdx + 1
    return commStr2

#NB: msgstr must contain (".....RETVAL:.......") or it will fail!!!
def InterpretString3(msgstr):
    retvalidx = find(msgstr,"RETVAL:")
    if (retvalidx==-1):
        return msgstr
    msgstr = msgstr[retvalidx+7:]
    currIdx = find(msgstr,'[')
    if (currIdx!=-1): #might be a list, a 1d array or a 2d array
        arrStr = re.split("\s*",msgstr)
        del arrStr[0] #if it is a list or an array, first element is ''
        arrStrlen = len(arrStr)
        del arrStr[arrStrlen-1] #last element is the \000 character
        arrList = []
        #check format to see if it is a list, a 1d array or a 2d array
        #list or 1d array format of arrStr[0] MUST BE:
        #<array-identifier>[integer]
        #for a 2d array it is:
        #<array-identifier>[integer][integer]
        currIdx = find(arrStr[0],'[')
        nextIdx = find(arrStr[0],']',currIdx)
        testStr = arrStr[0]
        idx1Start = 0
        try:
            idx1Start = int(testStr[currIdx+1:nextIdx])
        except:
            return msgstr
        #Now we know it's an array
        #We can fill array up to the first index
        for i in range(0,idx1Start):
            arrList.append(None) 
        if (nextIdx==(len(testStr)-1)): # only one '[...]'
            #This is either a 1D array or list
            # we now need to work out whether this is an array of a list
            #list format of arrStr[1] MUST BE:
            #<array-identifier>[integer]
            #for a 1d array it is:
            #value (no '[')
            try:
                arrayOrList = find(arrStr[1],'[')
            except IndexError: # this is a list with only one element
                return msgstr
            if arrayOrList==-1:
                # this is a 1D array
                for i in range(1,arrStrlen-1,2): # was range(1,arrStrlen-1,2); not sure why!
                    arrList.append(getNumOrStr(arrStr[i]))
                return arrList
            else:
                # this is a list
                for i in range(0,arrStrlen-1,1): # was range(1,arrStrlen-1,2); not sure why!
                    arrList.append(getNumOrStr(arrStr[i]))
                return arrList                
        nextIdx = nextIdx +1
        if (testStr[nextIdx]!='['):
            return msgstr
        currIdx = find(testStr[nextIdx:],']') + nextIdx
        if (currIdx!=-1):
            try:
                idx2Start = int(testStr[nextIdx+1:currIdx])
            except:
                return msgstr
            #Now we know it's a 2d array
            idx1 = -1
            for i in range(0,arrStrlen-2,2):
                testStr = arrStr[i]
                currIdx = find(testStr,'[')
                nextIdx = find(testStr[currIdx:],']') + currIdx
                x = int(testStr[currIdx+1:nextIdx])
                currIdx2 = find(testStr[nextIdx:],'[') + nextIdx
                nextIdx2 = find(testStr[currIdx2:],']') + currIdx2
                y = int(testStr[currIdx2+1:nextIdx2])
                #Assumed to ALWAYS be an int and currIdx+1!=nextIdx
                if (x!=idx1): #next row of matrix
                    idx1 = x
                    arrList.append([])
                    for k in range(0,idx2Start):
                        arrList[idx1].append(None)
                        #fill inner list(array) up to first index
                arrList[idx1].append(getNumOrStr(arrStr[i+1]))
            return arrList                               
    else:
        return getNumOrStr(msgstr)

class pdApp:
    def __init__(self):
        self.appSock = None
        self.currPort = None
        self.cmdList = ''

    def __del__(self):
        if (self.appSock!=None):
            self.appSock.close()    #close() = os function?
        self.CleanUpPort()

    def CleanUpPort(self):
        global portsTaken
        global nextPortAvailable
        if (len(portsTaken)==1):
            portsTaken = []
        for i in range(0,len(portsTaken)-1):
            if (portsTaken[i]==self.currPort):
                nextPortAvailable = portsTaken[i]
                del portsTaken[i]
        self.currPort = None    

    def StartApp(self,path,portNo = 5101):
        retstr = ''
        if (self.appSock!=None):
            return "This object is already in use." 
        a = IsPortAvailable(portNo)
        if (a==0):
            retstr =  retstr + "Port No: " + repr(portNo) + " is not available\n"
            portNo = getNextAvailablePort()
            retstr = retstr + "Using Port No: " + repr(portNo) +" instead.\n"

        #here try to change dir to the exe path dir.
        a = rfind(path,"\\")
        if (a!=-1):
            if (path[0:a]==''):
                os.chdir("\\")
            else:
                os.chdir(path[0:a])
       
        try:
            os.spawnv(os.P_DETACH,path,[path,"-pt",repr(portNo)])
        except:
            retstr = retstr + "Could not start the application\n"
            return retstr
        retstr1 = self.ConnectToApp1('localhost',portNo,0)
        retstr = retstr + retstr1

    def ConnectToApp(self,hostname = 'localhost',portNo = 5101):
        return self.ConnectToApp1(hostname,portNo,1)

    def ConnectToApp1(self,hostname,portNo,selectPort = 1):
        retstr = ''
        if (self.appSock!=None):
            return "This object is already in use.\n"
        global portsTaken
        global CONNECTIONATTEMPTS
        if (selectPort==1):
            a = IsPortAvailable(portNo)
            if (a==0):
                retstr =  retstr + "Port No: " + repr(portNo) + " is not available\n"
                portNo = getNextAvailablePort()
                retstr = retstr + "Using Port No: " + repr(portNo) +" instead.\n"
                
        self.appSock = socket(AF_INET,SOCK_STREAM)
        a = 0
        print "Attempting to connect to application on TCP/IP Port No. " + repr(portNo)
        while (a<CONNECTIONATTEMPTS):
            try:
                self.appSock.connect((hostname,portNo))
                break
            except:
                a = a + 1
                print "Connection Attempt Number " + repr(a)
                if (a==CONNECTIONATTEMPTS):
                    print "WARNING: Failed to connect to the application\n"
                    return retstr + "Failed to connect to the application\n"
        portsTaken.append(portNo)
        self.currPort = portNo
        return retstr
            
    def AddCmd(self,commStr,varList = []):
        commStr = InterpretString(commStr,varList)
        commStr = commStr + ';' #doesn't hurt to add the extra semicolon
        self.cmdList = self.cmdList + commStr
        return None

    def Exec(self,commStr,varList = []):
        msgstr = None
        global INTBUFFSIZE
        global portsTaken
        global nextPortAvailable
        if (self.appSock==None):
            return "application not initialised\n"
        self.AddCmd(commStr,varList)
        #commlen = len(self.cmdList) #old protocol
        commlen = len(self.cmdList)+1 #new protocol
        commlenstr = repr(commlen)
        self.cmdList = commlenstr + (INTBUFFSIZE-len(commlenstr))*' ' + self.cmdList + '\0'
        try:
            self.appSock.send(self.cmdList)
        except:
            self.CleanUpPort()            
            return "Error sending message from this port"
        #here we can flush cmdList
        self.cmdList = ''
        recmsg = self.appSock.recv(INTBUFFSIZE) #first line received is length of message
        nulIdx = find(recmsg,'\x00')
        recmsg = recmsg[0:nulIdx]
        try:
            recmsglen = int(recmsg)
        except ValueError:
            return None #probably a app.exit command
        recmsg = ""
        if (recmsglen>MaxBuffSize): # if there is more data than can be transmitted in one go
            batches=int(ceil(float(recmsglen)/float(MaxBuffSize)))
            for i in range(1,batches+1,1):
                while True:
                    try:
                        recmsg = recmsg + self.appSock.recv(MaxBuffSize)
                        sleep(delay)
                        break
                    except:
                        pass
        else:
            recmsg = self.appSock.recv(recmsglen)
        #now test to see what has been returned
        if (len(recmsg)<recmsglen): # part of the message is missing
            print "================================================================="
            print "WARNING: some of the data sent by the application has not been received."
            print "Please reduce 'MaxBuffSize' or increase 'delay' in pdPythonLib.py"
            print "and try to run the script again."
            print "If the problem remains please contact Photon Design."
            print "================================================================="
            raw_input("Press Enter to continue")
        retvalcount = count(recmsg,"RETVAL:")
        if retvalcount==0: #if no RETVAL, return what was returned (usually an error message)
            return recmsg
        if retvalcount==1:
            msgstr = InterpretString3(recmsg)
            return msgstr
        else:
            msgstr = []
            riidxprev = find(recmsg,"RETVAL:") #the position of the first RETVAL statement
            recmsg = recmsg[riidxprev:]
            for a in range(0,retvalcount):
                ridx = find(recmsg[1:],"RETVAL:")
                if ridx==-1:
                    msgstr.append(InterpretString3(recmsg))
                    return msgstr
                msg1 = recmsg[0:ridx+1]
                msgstr.append(InterpretString3(msg1))
                recmsg = recmsg[ridx+1:]
            return msgstr