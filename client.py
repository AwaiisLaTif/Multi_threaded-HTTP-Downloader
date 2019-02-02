from socket import *
import time
import datetime
import os
import sys
import argparse
from urlparse import urlparse
import threading

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-r','--resume',metavar='',help='resume previous downloading',required=False)
parser.add_argument('-n','--number_of_connection',type=str,metavar='',help='Number of connection need to establish',default=1)
parser.add_argument('-i','--metric_interval',type=float,metavar='',help='metric interval',required=True)
#parser.add_argument('-c','--connection_type',type=str,metavar='',help='Specify the type UDP or TCP')
parser.add_argument('-f','--file_location',type=str,metavar='',help='Give file URL',required=True)
parser.add_argument('-o','--output_location',type=str,metavar='',help='Specify where you want to save the file',required=True)
args= parser.parse_args()
outputfile=""
files=[]
timeInterval=0;
downloadDir="."
def report(start, size, ids,downloaded,total_content):
    total = time.time() - start
    
    speed=0.00
    try:
            speed=(size / 1024.0) / total
    except:
            print "time interval should be greater than zero"

    print "connection: %s %d/%s, download speed: %.2f kb/s\n" % (
            ids, downloaded,total_content,speed )

# function for downloading chunk of file
def downloadPartialFile(serverIP,serverPort,hostName,filePath,startByte,endByte,downloadDestination,downloadName,resume,ids,content_length):
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((serverIP,serverPort))
        
        #sending query for range of byte
        clientSocket.send(b'GET /'+filePath+' HTTP/1.1\r\nHost:'+hostName+'\r\nRange: bytes='+str(startByte)+'-'+str(endByte)+' \r\n\r\n')
        # file directory where file is downloaded
        fileDir=os.path.join(downloadDestination,downloadName)

        #checking if it is resume request or new one
        if(resume):
                #if resume then open file in appending mode
                file = open(os.path.join(downloadDestination,downloadName),"ab")
                
        else:
                #else create new file in write mode
                file = open(os.path.join(downloadDestination,downloadName),"wb")
                
        
        #initialize data
        data = b'';
	data = clientSocket.recv(2048)

        #spliting header chunk
	data = data.split(b'\r\n\r\n')[1]
        datalength=len(data)
        ran=int(endByte)-int(startByte)

        #local variable for speed calculation
        startTime=0
	downloaded=0
        count=0
        stop=True

        # while loop for data reading
	try:
                while(data):
                        #writing data to file
                        file.write(data)
                        #when server file downloaded complete
                        if datalength>=ran:
                                
                                break
		
                        data = clientSocket.recv(1024)

                        #storing total downloaded data
                        downloaded+=len(data)
                        datalength+=len(data)

                        #condition for storing instance time and downloaded byte
                        if(stop):
                                count=downloaded
			        startTime=time.time()
		 	        stop=False
			
                        # checking for user given interval
		        if(time.time()-startTime>=timeInterval):
                                #function for printing speed 
			        report(startTime,downloaded-count,str(ids),downloaded,str(endByte-startByte))
                                #setting variable for next interval
			        stop=True
        # exception handling
        except Exception:
                print "waiting for server close.\n"
        #closing file and socket
        finally:
                file.close()
                clientSocket.close()

#function for getting header information 
def getHeaderInfo(serverIP,serverPort,hostName,storagePath):
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((serverIP,serverPort))

        #request for header
        clientSocket.send(b'HEAD /'+storagePath+' HTTP/1.1\r\nHost:'+hostName+' \r\n\r\n')
        # recieving data from socket
        data = clientSocket.recv(10240)

        #variable initialization
	headerInfo=["",""]

        #spliting into lines
        headers =  data.split(b'\r\n')
        temp=True

        #loop for checking all lines
	for x in headers:
                
                #condition for  line of content length
                if ("Content-Length" in x or "content-length" in x) & temp :
                        
                        # storing total file length from header
                        headerInfo[0]=x.split(b': ')[1]
                        temp=False
                
                # condition for checking accept byte range query
		if "Accept-Ranges" in x or "accept-ranges" in x:
			headerInfo[1]=x.split(b': ')[1] 
        #return that header information (content length and accept range)
	return headerInfo

# function for single connection downloading with support of resume
def SingleDownloadResume(serverIP,serverPort,hostName,filePath,downloadDestination,downloadName):
        #getting header information
        info=getHeaderInfo(serverIP,serverPort,hostName,filePath)

        #file directory for download
        fileDir=os.path.join(downloadDestination,downloadName)
        #variabe for staring byte
        startByte="";

        #condition for checking if it support range query
        if(info[1]=="bytes"):
                #checking file exist
                if os.path.exists(fileDir):
                        

                        #checking file size
                        fileSize = os.path.getsize(fileDir)
                        


                        #checking for completed file or not 
                        if (fileSize < int(info[0])):
                                print "partial file Exist \n"

                                #if file is not complete than start from that bytes
                                startByte=fileSize
                                

                                #calling function for partial file download
                                downloadPartialFile(serverIP,serverPort,hostName,filePath,startByte,int(info[0]),downloadDestination,downloadName,True,"1",info[0])
                        else:
                                #if file size is content length than full file already downloaded
                                print "file already completely downloaded\n"

                #if file does not exist   
                else:
                           print "file does not exist\n"
                           print "downloading from start\n"
                           #starting from start
                           SingleDownloadWithoutResume(serverIP,serverPort,hostName,filePath,downloadDestination,downloadName)
        else:
                #if server does not support byte range query
                print "Server does not support resume option\n"
                print "downloading file from starting.\n"
                #starting from start
                SingleDownloadWithoutResume(serverIP,serverPort,hostName,filePath,downloadDestination,downloadName)

# single connection for downloading without resume
def SingleDownloadWithoutResume(serverIP,serverPort,hostName,filePath,downloadDestination,downloadName):
        #header information
        info=getHeaderInfo(serverIP,serverPort,hostName,filePath)
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((serverIP,serverPort))
        #query for full file
        clientSocket.send(b'GET /'+filePath+' HTTP/1.1\r\nHost:'+hostName+' \r\n\r\n')
        #directory for file download
        fileDir=os.path.join(downloadDestination,downloadName);

        #createing file in write mode
        file = open(os.path.join(downloadDestination,downloadName),"wb")
        
        
        #initialization variable
        data = b'';
	data = clientSocket.recv(2048)

        #spliting header form data
	data = data.split(b'\r\n\r\n')[1]
        datalength=len(data)

        #variable for speed calculation
        startTime=0
	downloaded=0
        count=0
        stop=True

        #while for data recieve from socket
        try:
                while(data):
                        #writing to file
                        file.write(data)

                        #when server file downloaded complete
                        if datalength>=int(info[0]):
                                
                                break
                        #receiving new data
                        data = clientSocket.recv(1024)

                        #storing total downloaded byte
                        downloaded+=len(data)
                        datalength+=len(data)

                        #condition for instance value of time and downloaded byte
                        if(stop):
                                #downloaded byet at that time
                                count=downloaded

                                #time instance 
			        startTime=time.time()
		 	        stop=False
                        
			#condition for checking different in interval
		        if(time.time()-startTime>=timeInterval):
                                #calling function for displaying speed
			        report(startTime,downloaded-count,"1",downloaded,info[0])
			        stop=True
        #exception handling
	except Exception:
                print "waiting server to close.\n"
        
        #closing file and socket
        finally:
                file.close()
	        clientSocket.close()

#methode for overall single connection        
def SingleConnection(serverIP,serverPort,hostName,filePath,downloadDestination,downloadName,resume):
        #checking resume flag
        if(resume):
                
                #if resume flag is set calling ainglewith resume 
                SingleDownloadResume(serverIP,serverPort,hostName,filePath,downloadDestination,downloadName)
        else:
                #if resume flag is not set than calling single connection without resume
                
                SingleDownloadWithoutResume(serverIP,serverPort,hostName,filePath,downloadDestination,downloadName)
        

# thread class for connection
class Connection (threading.Thread):
   #contructor for initialization of variable
   def __init__(self,ranges,thread_id,content_length,last,serverIP,serverPort,hostName,storagePath,resume):
      threading.Thread.__init__(self)
      self.range=ranges
      self.thread_id=thread_id
      self.content_length=content_length
      self.last=last
      self.serverPort=serverPort
      self.serverIP=serverIP
      self.hostName=hostName
      self.storagePath=storagePath
      self.resume=resume
   #run function 
   def run(self):
           #download dire variable
	   Download_Destination=downloadDir

           #getting file name
	   Download_name=str(self.thread_id)+os.path.basename(obj.path)

           #file directory with name
	   fileDir=os.path.join(Download_Destination,Download_name)

           #variable for range query
	   startByte=""
	   endByte=""

           #checking resume flag
	   if(self.resume):
                   # checking for file exist
                   if os.path.exists(fileDir):
                        

                        #getting file size
                        fileSize = os.path.getsize(fileDir)
                        

                        #checking file size with request data byte
                        if (fileSize < int(self.range)):
                                print "partial file Exist"
                                #if partial file exist that starting byte is file exist size
                                startByte=fileSize+(self.range*self.thread_id)
                                

                                #cheking if it is last connection
                                if(self.thread_id==(self.last-1)):

                                        #for last connection ending is content length
                                        downloadPartialFile(self.serverIP,self.serverPort,self.hostName,self.storagePath,startByte,(int(self.content_length)-1),Download_Destination,Download_name,self.resume,str(self.thread_id+1),self.content_length)
                                else:
                                        #for other connection ending is calculated from formula
                                        downloadPartialFile(self.serverIP,self.serverPort,self.hostName,self.storagePath,startByte,(self.range*(self.thread_id+1)-1),Download_Destination,Download_name,self.resume,str(self.thread_id+1),self.content_length)
                        else:
                                #if file size is equal to request size, show file complete exist
                                print "file already completely downloaded"
                   
                   else:
                           #file does not exist in directory
                           print "file does not exist \n"
                           print "downloading from start\n"

                           #assigning start range for new file download 
                           startByte=self.range*self.thread_id

                           #condition for last connection
                           if(self.thread_id==(self.last-1)):
                                   #for last connection  endting byte is content langth
                                   downloadPartialFile(self.serverIP,self.serverPort,self.hostName,self.storagePath,startByte,(int(self.content_length)-1),Download_Destination,Download_name,False,str(self.thread_id+1),self.content_length)
                           else:
                                   #for other conection calculating ending range from formula
                                   downloadPartialFile(self.serverIP,self.serverPort,self.hostName,self.storagePath,startByte,(self.range*(self.thread_id+1)-1),Download_Destination,Download_name,False,str(self.thread_id+1),self.content_length)

	   else:
                   #if resume flage is not set
                   
                   startByte=self.range*self.thread_id
                   #checking if it is last connection
                   if(self.thread_id==(self.last-1)):
                           #for last connection it ending byte is content length
                           downloadPartialFile(self.serverIP,self.serverPort,self.hostName,self.storagePath,startByte,(int(self.content_length)-1),Download_Destination,Download_name,self.resume,str(self.thread_id+1),self.content_length)
                   else:
                           #for other it is calculated from formula
                           downloadPartialFile(self.serverIP,self.serverPort,self.hostName,self.storagePath,startByte,((self.range*(self.thread_id+1))-1),Download_Destination,Download_name,self.resume,str(self.thread_id+1),self.content_length)
	   

           #storing file name for combining in last
           files[self.thread_id]=(os.path.join(Download_Destination,Download_name))

#main function
if __name__ == '__main__':

        #number of connection parsing
        noOfconnection=int(args.number_of_connection)

        #output directory
        downloadDir=args.output_location
        
        #variable initilization for different connection
        files=[""]*noOfconnection
        
        #time interval parsing
        timeInterval=args.metric_interval

        #resume parsing
        resume=args.resume

        #parsing link
        obj = urlparse(args.file_location)

        #parsing host name from link
	hostName=obj.netloc

        #parsing file path from link
	storagePath=obj.path

        #ip from domain link
	serverIP = gethostbyname(hostName)
	serverPort=80

        #filename
	downloadFileName=os.path.basename(storagePath)
	#output single directory
        outputfile=os.path.join(downloadDir,downloadFileName)
	s=time.time()
        
	resumeFlage=False

        #checking user resume set
        if(resume=="1"):
                resumeFlage=True
        

        #checking for number of connection 
	if(noOfconnection>1):
                #getting header information
                content_length,accept_byte=getHeaderInfo(serverIP,serverPort,hostName,storagePath)
                
                #bytes for each connection
                dataToEachThread = int(content_length)/noOfconnection

                # checking server supporrt range query
                if(accept_byte=="bytes"):
                        print "downloading file with multiple connections."
                        # array for connection threads
                        connection=[]

                        ##creating connections threads
                        for i in range(0,noOfconnection):
                                #creating connection
                                conn = Connection(dataToEachThread,i,content_length,noOfconnection,serverIP,serverPort,hostName,storagePath,resumeFlage)
                                conn.start()
                                connection.append(conn)
                        # waiting for all connection complete
                        for c in connection:
                                c.join()
                        
                        print outputfile
                        #combining file into one in case of chunk
                        with open(outputfile, 'wb') as outfile:
                                for fname in files:
                                        with open(fname,'rb') as infile:
                                                outfile.write(infile.read())
                        
                        #removing files after combining
                        for fname in files:
                                if (os.path.getsize(fname) >= dataToEachThread):
                                        os.remove(fname)
                        print downloadFileName+" download completed.\n"
                        
                else:
                        #server does not support byte range query
                        print "Server does not support multiple coonection.\n"
                        print "Downloading file using single connection.\n"
                        SingleConnection(serverIP,serverPort,hostName,storagePath,downloadDir,downloadFileName,resumeFlage)
                        print downloadFileName+" download completed.\n"
                        
                        
        else:
                #for single connetion query
                print "downloading file with single connection."
                SingleConnection(serverIP,serverPort,hostName,storagePath,downloadDir,downloadFileName,resumeFlage)
                print downloadFileName+" download completed.\n"
        print "downloading completed in "+str(time.time()-s)+ " second"
