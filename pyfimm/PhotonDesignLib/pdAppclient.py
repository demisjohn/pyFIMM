#pdAppClient (PYTHON version)

from pdPythonLib import *
import sys
from string import *

if len(sys.argv)<3:
    print "pdAppClient (PYTHON Version) Syntax:"
    print "pdAppClient <portNo> <hostname>"
    print "<portNo> = the port number on which the application is serving"
    print "<hostname> = the name (or IP address) where application is serving"
else:
    _portNo = atoi(sys.argv[1])
    f = pdApp()
    retmsg = f.ConnectToApp(sys.argv[2],_portNo)
    if retmsg!="":
        print retmsg
    else:
        print "Connected to Application"
        print "Enter your commands or enter exit to finish"
        isDone = 0
        while isDone==0:
            comm = raw_input("COMMAND: ")
            if comm[0:4]=="exit":
                isDone = 1
            else:
                rec = f.Exec(comm)
                print rec
        
        
        
