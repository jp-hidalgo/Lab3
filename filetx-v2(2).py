import PySimpleGUI as sg
from datetime import datetime
import socket
import threading as trd
from socketserver import ThreadingMixIn
import logging
import time
import os
import hashlib

BUFFER_SIZE = 1024


class ChatServerThread(trd.Thread):

    def __init__(self,ip,port,conn, window):
        trd.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.conn = conn
        self.window =  window
        print( " New thread started for "+ip+":"+str(port))

    def run(self):
        while True:
            str_recv = self.conn.recvfrom(1024)
            self.window['_SRVTEXT_'].update (str_recv[0])
            self.window.Refresh()
            


class FileServerThread(trd.Thread):

    def __init__(self,ip,port,sock,client):
        
        trd.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.sock = sock
        self.clients= client
        print( " New TCP thread started for "+ip+":"+str(port))
        logging.info("New TCP client connected from {}:{}".format(self.ip, self.port))

        
    def run(self):
        prueba =  3
        t = time.perf_counter()
        filename = 'Cliente{}-Prueba-{}.txt'.format(self.clients, prueba)
        hasher = hashlib.sha256()
        with open(filename, 'wb') as f:
            while True: 
                data = self.sock.recv(BUFFER_SIZE)
                if not data:
                    f.close()
                    print( 'file close()')
                    t = time.perf_counter()-t
                    break
                #write data to a file
                f.write(data)
                hasher.update(data)
        file_hash = hasher.hexdigest()
        logging.info("File transfered correctly")
        logging.info("Time for transfer: {}".format(t))
        logging.info("File hash recieved: {}".format(file_hash))
        self.sock.sendall(file_hash.encode())



def send_file(filename, sock):
    print ('openning file' + filename)
    logging.info("File name: {}".format(filename))
    logging.info("File size: {}".format(os.stat(filename).st_size) )
    f = open(filename,'rb')
    l = f.read(BUFFER_SIZE)
    hasher = hashlib.sha256()
    hasher.update(l)
    while (l):
        sock.send(l)
        l = f.read(BUFFER_SIZE)
        hasher.update(l)
        if not l:
            f.close()
            sock.close()
    file_hash = hasher.hexdigest()
    logging.info("File hash sent: {}".format(file_hash))

            
                


def start_server(values, window):
    srv_tcp_ip = values['_SRVHOSTNAME_']
    srv_tcp_port = int(values['_SRVCHATPORT_']) 
    srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    srv_socket.bind((srv_tcp_ip, srv_tcp_port))
    threads = []
    
    while True:
        srv_socket.listen(5)
        print ("Waiting for incoming connections...")
        (conn, (ip,port)) = srv_socket.accept()
        print ('Got chat connection from ', (ip,port))
        newthread = ChatServerThread(ip,port,conn, window)
        newthread.start()

        threads.append(newthread)
    for t in threads:
        t.join()




def start_tcp_server(values):
    srv_clients = values['_SRVMAXCLIENTS_']
    srv_tcp_ip = values['_SRVHOSTNAME_']
    srv_tcp_port = int(values['_SRVTCPPORT_']) 
    srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    srv_socket.bind((srv_tcp_ip, srv_tcp_port))
    threads = []
    
    while True:
        srv_socket.listen(5)
        print ("Waiting for files...")
        (conn, (ip,port)) = srv_socket.accept()
        print ('Got TCP connection from ', (ip,port))
        newthread = FileServerThread(ip,port,conn, srv_clients )
        newthread.start()
        threads.append(newthread)
    for t in threads:
        t.join()




#
#
#
def the_gui ():

    col_client = sg.Column ([
                            [sg.Text('Partner configuration:')],      
                            [sg.Text('Partner Address:', size=(15, 1)), sg.InputText('192.168.43.61',key='_PARTNERNAME_',size=(12,1))],      
                            [sg.Text('Partner Chat Port:', size=(15, 1)), sg.InputText('8080', key='_PARTNERPORT_', size=(12,1))],   
                            [sg.Text('Partner TCP Port:', size=(20, 1)), sg.InputText('8082',key='_TCPPORT_',size=(12,1))],    
                            [sg.Button ('Init Chat', key='_STARTCHATCON_KEY_')]
                        ])
    col_server = sg.Column ([
                            [sg.Text('Server configuration: (This machine)')],      
                            [sg.Text('My Address', size=(10, 1)), sg.InputText('192.168.43.204',key='_SRVHOSTNAME_', size=(12,1))],      
                            [sg.Text('Chat Port:', size=(10, 1)), sg.InputText('8080',key='_SRVCHATPORT_',size=(12,1))],  
                            [sg.Text('TCP Port:', size=(10, 1)), sg.InputText('8082', key='_SRVTCPPORT_',size=(12,1))],    
                            [sg.Text('Clients:', size=(10, 1)), sg.InputText('5',key='_SRVMAXCLIENTS_' ,size=(12,1))], 
                            [sg.Button ('Start chat server', key='_STARTSERVER_KEY_'), sg.Button ('Start TCP server', key='_STARTTCPSERVER_KEY_')]
                        ])

    layout = [ 
            [sg.Pane([col_client , col_server ], orientation='h')],
            [sg.Text('Chat zone:')],  
            [sg.Text('Enter your text')],
            [sg.Multiline(default_text='Your text', key='_CLTTEXT_', size=(55, 10)),
             sg.Multiline(default_text='Partner text', key='_SRVTEXT_', size=(55, 10))],
            [sg.Button ('Send Message', key='_SENDMESSAGE_KEY_')], 
            [sg.Text('File transfer zone:')], 
            [sg.Text('Your File', size=(15, 1), auto_size_text=False, justification='right'),      
                sg.InputText('Default File', key='_FILENAME_'), sg.FileBrowse(), sg.Button ('Send File', key='_SENDFILE_KEY_')],    
            [sg.Text('Console:')],
            [sg.Output(size=(110,10))],
            [sg.Button ('Exit', key='_EXIT_KEY_')],
            ]
    window = sg.Window('Chat and File Transfer App').Layout(layout)         
    values = window.Read()


    # --------  Event Loop ----------------------
    while True:      
        event, values = window.Read() 

        if event ==  '_STARTSERVER_KEY_':
            print('Starting chat server...')
            trd.Thread (target=start_server,args=(values, window),daemon=True).start()
            
        
        if event == '_STARTTCPSERVER_KEY_':
            print('Starting TCP server...')
            trd.Thread (target=start_tcp_server,args=(values,),daemon=True).start()

        if event ==  '_STARTCHATCON_KEY_':
            print('Starting chat connection with server...')
            clt_tcp_ip = values['_PARTNERNAME_']
            clt_tcp_port = int(values['_PARTNERPORT_'])
            clt_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clt_socket.connect((clt_tcp_ip, clt_tcp_port))

        if event ==  '_SENDMESSAGE_KEY_':
            clt_socket.send(bytes(values['_CLTTEXT_'], 'utf-8'))
            window['_CLTTEXT_'].update(' ')
            window.Refresh()
        
        if event ==  '_SENDFILE_KEY_':
            print('Starting tcp connection with server...')
            tcp_tcp_ip = values['_PARTNERNAME_']
            tcp_tcp_port = int(values['_TCPPORT_'])
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((tcp_tcp_ip, tcp_tcp_port))
            print('Sending file' + values['_FILENAME_'])
            send_file (values['_FILENAME_'], tcp_socket)
            

        if event in (None, 'Exit'):      
            break      
    window.Close()

#
# Main
#

if __name__ == '__main__':
    now = datetime.now()
    dir_name = "Logs"

    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    logging.basicConfig(filename="Logs/"+str(now.year)+'-'+str(now.month)+'-'+str(now.day)+'-'+str(now.hour)+'-'+str(now.minute)+'-'+str(now.second)+'-log.txt', encoding='utf-8', level=logging.DEBUG)
    the_gui()
    print('Exiting Program')