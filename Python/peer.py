import datetime
import os
import queue
import socket
import threading
from queue import Queue
import tqdm
from enums import Channels, MsgType, ErrorType
from structs import (
    AddFileTOShareListResponseS2P, 
    AddFileToShareListP2S, 
    BroadcastMsgRequestP2S, 
    ChatroomChatsRequestS2P,
    ChatroomChatsUpdateS2P,
    DownloadFileRequestP2P,
    FileServerDetailsRequestP2S,
    GetSharedFilesDetailsOfPeerP2S,
    GetSharedFilesDetailsOfPeerResponseS2P,
    IdOfPeerRequestS2P,
    Msg,
    PeerListRequestS2P,
    PeerListUpdateS2P,
    PublicPeer,
    RemoveFileFromShareListP2S,
    ResultResponse,
    SharedFile,
    UsernameRequestP2S
)
from utils import (
    create_error_msg,
    create_success_msg,
    get_file_details,
    get_your_ip,
    msg_reciever,
    msg_sender
)
from colors import bcolors
from exceptions import (
    UnexpectedRequestFromServer, 
    UnexpectedResponseFromServer, 
    UsernameAlreadyTaken
)
from chatroom import Chatroom

class Peer:
    def __init__(self , server_host:str , server_port:int , username:str):
        self.__server_host = server_host
        self.__server_port = server_port

        self.__ip = get_your_ip()

        self.__socket = None
        self.__username = username
        self.__id = None

        self.__file_socket = None
        self.__file_server_port = None
        self.__download_directory = None

        self.__msg_sender_to_server_queue = Queue()
        self.__add_file_to_share_list_response_queue = Queue()
        self.__remove_file_from_share_list_response_queue = Queue()
        self.__get_shared_files_details_from_peer_response_queue = Queue()
        

        self.__online_peers:dict[str , PublicPeer] = {}
        self.__uname_to_id:dict[str , str] = {}
        self.__shared_files:dict[str , SharedFile] = {}

        self.__chatroom = Chatroom()
        self.__lock = threading.Lock()

        self.notifications = Queue()

    # ================================================= File Server =================================================
    def __acceptFileConnections(self):
        print(f'{bcolors["HEADER"]}File server listening on {self.__ip}:{self.__file_server_port}{bcolors["ENDC"]}')
        while True:
            conn, addr = self.__file_socket.accept()

            threading.Thread(target = self.__msgRecieverFromOtherPeers , args=(conn , addr) , daemon=True , name=f'__msgRecieverFromOtherPeers({addr[0]}:{addr[1]})').start()

    def __startFileServer(self):
        self.__file_socket = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        self.__file_socket.setsockopt(socket.SOL_SOCKET , socket.SO_REUSEADDR , 1)
        self.__file_socket.bind((self.__ip , 0))

        self.__file_server_port = self.__file_socket.getsockname()[1]

        self.__file_socket.listen(5)

        threading.Thread(target = self.__acceptFileConnections , daemon=True , name='__acceptFileConnections').start()

    def __msgRecieverFromOtherPeers(self , conn:socket.socket , addr:tuple):
        try:
            # print(f'{bcolors["HEADER"]}msgRecieverFromOtherPeers thread started for {addr[0]}:{addr[1]} {bcolors["ENDC"]}')

            msg = msg_reciever(conn)

            if msg == None:
                pass

            elif msg.type == MsgType.request.value:
                if msg.channel == Channels.DownloadFileRequest.value:
                    data:DownloadFileRequestP2P = msg.data

                    self.__sendFileToPeer(conn , addr , data.file_id)
        
        except Exception as e:
            pass
            # print(f'{bcolors["FAIL"]}Error occured in msgRecieverFromOtherPeers : {e}{bcolors["ENDC"]}')

        finally:
            conn.close()
            # print(f'{bcolors["HEADER"]}msgRecieverFromOtherPeers thread stopped for {addr[0]}:{addr[1]} {bcolors["ENDC"]}')

    def __sendFileToPeer(self , conn:socket.socket , addr:tuple , file_id:str):
        try:
            if file_id not in self.__shared_files:
                rsp:Msg = create_error_msg(Channels.DownloadFileRequest.value , 'File not found')
                msg_sender(conn , rsp)

            file_path = self.__shared_files[file_id].file_path

            if not os.path.exists(file_path):
                rsp:Msg = create_error_msg(Channels.DownloadFileRequest.value , 'File not found')
                msg_sender(conn , rsp)
                return
            
            else:
                rsp:Msg = create_success_msg(Channels.DownloadFileRequest.value)
                msg_sender(conn , rsp)

            file = self.__shared_files[file_id]
            # print(f'{bcolors["WARNING"]}Sending {file.file_name} to {addr[0]}:{addr[1]}{bcolors["ENDC"]}')
            # progress = tqdm.tqdm(range(file.file_size), f'{bcolors["OKGREEN"]}Sending{bcolors["ENDC"]}', unit="B", unit_scale=True, unit_divisor=1024)
            with open(file_path , 'rb') as f:
                while True:
                    data = f.read(1024000)
                    if not data:
                        break
                    conn.sendall(data)
                    # progress.update(len(data))
            
            # progress.close()

            # print(f'{bcolors["OKGREEN"]}File ({file.file_name}) sent to {addr[0]}:{addr[1]}{bcolors["ENDC"]}')

        except ConnectionResetError:
            print(f'{bcolors["FAIL"]}Error sending file to {addr[0]}:{addr[1]} : Peer went offline{bcolors["ENDC"]}')

        except Exception as e:
            print(f'{bcolors["FAIL"]}Error sending file to {addr[0]}:{addr[1]} : {e}{bcolors["ENDC"]}')



    # ================================================= Server Interactions =================================================
    def __connectToServer(self):
        self.__socket = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_TCP , socket.TCP_NODELAY , 1)

        print(f'{bcolors["HEADER"]}Socket created : {self.__socket}{bcolors["ENDC"]}')
        print(f'{bcolors["HEADER"]}Connecting to {self.__server_host}:{self.__server_port}{bcolors["ENDC"]}')
        self.__socket.connect((self.__server_host , self.__server_port))

        print(f'{bcolors["HEADER"]}TCP Connection established with Server {self.__server_host}:{self.__server_port}{bcolors["ENDC"]}')

    def __sendUsernameToServer(self):
        msg:Msg = Msg()
        msg.type = MsgType.request.value
        msg.channel = Channels.UsernameRequest.value

        data:UsernameRequestP2S = UsernameRequestP2S()
        data.username = self.__username
        msg.data = data

        msg_sender(self.__socket , msg)

        result:Msg = msg_reciever(self.__socket)

        if result.type == MsgType.result.value:
            if result.channel == Channels.UsernameRequest.value:
                result_data:ResultResponse = result.data
                if result_data.success == True:
                    print(f'{bcolors["OKGREEN"]}Username ({self.__username}) allowed to be used{bcolors["ENDC"]}')
                    return

                elif result_data.error_type == ErrorType.UsernameAlreadyTaken.value:
                    raise UsernameAlreadyTaken('Username already taken')
                
        raise UnexpectedResponseFromServer('Unexpected response from server : Result Expected')

    def __sendFileServerDetailsToServer(self):
        msg:Msg = Msg()
        msg.type = MsgType.request.value
        msg.channel = Channels.FileServerDetailsRequest.value

        data:FileServerDetailsRequestP2S = FileServerDetailsRequestP2S()
        data.port = self.__file_server_port
        msg.data = data

        msg_sender(self.__socket , msg)

        print(f'{bcolors["OKGREEN"]}File Server Details sent to Server{bcolors["ENDC"]}')
    
    def __getYourIdFromServer(self):
        msg:Msg = msg_reciever(self.__socket)
    
        if msg.type == MsgType.request.value:
            if msg.channel == Channels.IdOfPeerRequest.value:
                data:IdOfPeerRequestS2P = msg.data

                self.__id = data.peer_id
                print(f'{bcolors["OKGREEN"]}Your ID ({self.__id}) received from Server{bcolors["ENDC"]}')
                return
        
        raise UnexpectedRequestFromServer('Unexpected request from server : Id Of Peer Request Expected')

    def __getChatroomChatsFromServer(self):
        msg:Msg = msg_reciever(self.__socket)
    
        if msg.type == MsgType.request.value:
            if msg.channel == Channels.ChatroomChatsRequest.value:
                data:ChatroomChatsRequestS2P = msg.data

                with self.__lock:
                    self.__chatroom.updateChats(data.chats)
                print(f'{bcolors["OKGREEN"]}Chatroom Chats received from Server{bcolors["ENDC"]}')
                return
            
        raise UnexpectedRequestFromServer('Unexpected request from server : Chatroom Chats Request Expected')

    def __getListOfOnlinePeersFromServer(self):
        msg:Msg = msg_reciever(self.__socket)
    
        if msg.type == MsgType.request.value:
            if msg.channel == Channels.PeerListRequest.value:
                data:PeerListRequestS2P = msg.data

                for p in data.peers:
                    with self.__lock:
                        self.__online_peers[p.id] = p
                        self.__uname_to_id[p.username] = p.id
                print(f'{bcolors["OKGREEN"]}Online Peers received from Server{bcolors["ENDC"]}')
                return
        
        raise UnexpectedRequestFromServer('Unexpected request from server : Peer List Request Expected')
    

    def startPeer(self):
        self.__startFileServer()
        self.__connectToServer()
        self.__sendUsernameToServer()
        self.__sendFileServerDetailsToServer()
        self.__getYourIdFromServer()
        self.__getListOfOnlinePeersFromServer()
        self.__getChatroomChatsFromServer()

        threading.Thread(target=self.__msgSenderToServer , daemon=True , name='__msgSenderToServer').start()
        threading.Thread(target=self.__msgRecieverFromServer , daemon=True , name='__msgRecieverFromServer').start()


    def __msgSenderToServer(self):
        try:
            print(f'{bcolors["OKBLUE"]}msgSenderToServer thread started{bcolors["ENDC"]}')

            while True:
                msg = self.__msg_sender_to_server_queue.get()

                if msg == 'stop':
                    break

                msg_sender(self.__socket , msg)
                self.__msg_sender_to_server_queue.task_done()

        except Exception as e:
            print(f'{bcolors["FAIL"]}Unexpected error occured in msgSenderToServer thread : {e}{bcolors["ENDC"]}')

        finally:
            print(f'{bcolors["FAIL"]}msgSenderToServer thread stopped{bcolors["ENDC"]}')
    
    def __msgRecieverFromServer(self):
        try:
            print(f'{bcolors["OKBLUE"]}msgRecieverFromServer thread started{bcolors["ENDC"]}')

            while True:
                msg = msg_reciever(self.__socket)

                if msg == None:
                    break

                if msg.type == MsgType.request.value:
                    if msg.channel == Channels.ChatroomChatsUpdate.value:
                        self.__handleChatroomChatsUpdateRequest(msg.data)
                    
                    elif msg.channel == Channels.PeerListUpdate.value:
                        self.__handlePeerListUpdateRequest(msg.data)

                elif msg.type == MsgType.response.value:
                    if msg.channel == Channels.AddFileToShareList.value:
                        self.__add_file_to_share_list_response_queue.put(msg.data)

                    elif msg.channel == Channels.GetSharedFilesDetailsOfPeer.value:
                        self.__get_shared_files_details_from_peer_response_queue.put(msg.data)
                
                elif msg.type == MsgType.result.value:
                    if msg.channel == Channels.RemoveFileFromShareList.value:
                        self.__remove_file_from_share_list_response_queue.put(msg.data)
        
        except ConnectionResetError as e:
            self.__handleConnectionResetFromServer()

        except Exception as e:
            print(f'{bcolors["FAIL"]}Unexpected error occured in msgRecieverFromServer thread : {e}{bcolors["ENDC"]}')

        finally:
            print(f'{bcolors["FAIL"]}msgRecieverFromServer thread stopped{bcolors["ENDC"]}')
    
    def __handleConnectionResetFromServer(self):
        print(f'{bcolors["FAIL"]}Server went offline{bcolors["ENDC"]}')
        os._exit(1)

    def __handleChatroomChatsUpdateRequest(self , data:ChatroomChatsUpdateS2P):
        with self.__lock:
            self.__chatroom.addChat(data.peer_id , data.username , data.msg , data.send_time)
        
        self.notifications.put({
            'type' : 'chat',
            'peer_id' : data.peer_id,
            'username' : data.username,
            'msg' : data.msg,
            'send_time' : data.send_time.isoformat()
        })

    def __handlePeerListUpdateRequest(self , data:PeerListUpdateS2P):
        with self.__lock:
            if data.change == 1:
                self.__online_peers[data.peer.id] = data.peer
                self.__uname_to_id[data.peer.username] = data.peer.id

            elif data.change == -1:
                del self.__online_peers[data.peer.id]
                del self.__uname_to_id[data.peer.username]
        
        self.notifications.put({
            'type' : 'peer_change',
            'peer_id' : data.peer.id,
            'username' : data.peer.username,
            'ip' : data.peer.ip,
            'file_server_port' : data.peer.file_server_port,
            'change' : data.change
        })

    # ================================================= Interface =================================================
    def broadcastMsg(self , msg_to_broadcast:str):
        msg:Msg = Msg()
        msg.type = MsgType.request.value
        msg.channel = Channels.BroadcastMsg.value

        data:BroadcastMsgRequestP2S = BroadcastMsgRequestP2S()
        data.msg = msg_to_broadcast
        data.send_time = datetime.datetime.now(datetime.timezone.utc)
        msg.data = data

        self.__msg_sender_to_server_queue.put(msg)

    def addFilesToShareList(self , file_paths:list[str] = []):
        response = []
        for file_path in file_paths:
            file_name , file_size , file_hash = get_file_details(file_path)

            msg:Msg = Msg()
            msg.type = MsgType.request.value
            msg.channel = Channels.AddFileToShareList.value

            data:AddFileToShareListP2S = AddFileToShareListP2S()
            data.file_path = file_path
            data.file_name = file_name
            data.file_size = file_size
            data.file_hash = file_hash
            msg.data = data

            self.__msg_sender_to_server_queue.put(msg)

            try:
                rsp:AddFileTOShareListResponseS2P = self.__add_file_to_share_list_response_queue.get(timeout=5)
            except queue.Empty:
                print(f'{bcolors["FAIL"]}File ({file_name}) not added to share list{bcolors["ENDC"]}')
                print(f'{bcolors["FAIL"]}Request timed out{bcolors["ENDC"]}')
                continue

            file:SharedFile = SharedFile()
            file.file_name = file_name
            file.file_path = file_path
            file.file_size = file_size
            file.file_hash = file_hash
            file.file_id = rsp.file_id

            with self.__lock:
                self.__shared_files[file.file_id] = file

            response.append(file)
            print(f'{bcolors["OKGREEN"]}File ({file_name}) added to share list{bcolors["ENDC"]}')

        return response

    def removeFilesFromShareList(self , file_ids:list[str] = []):
        for file_id in file_ids:
            if file_id not in self.__shared_files:
                print(f'{bcolors["FAIL"]}File ({file_id}) not found in share list{bcolors["ENDC"]}')
                continue

            msg:Msg = Msg()
            msg.type = MsgType.request.value
            msg.channel = Channels.RemoveFileFromShareList.value

            data:RemoveFileFromShareListP2S = RemoveFileFromShareListP2S()
            data.file_id = file_id
            msg.data = data

            self.__msg_sender_to_server_queue.put(msg)

            try:
                rsp:ResultResponse = self.__remove_file_from_share_list_response_queue.get(timeout=5)
            except queue.Empty:
                print(f'{bcolors["FAIL"]}File ({file_id}) not removed from share list{bcolors["ENDC"]}')
                print(f'{bcolors["FAIL"]}Request timed out{bcolors["ENDC"]}')

            if rsp.success == True:
                with self.__lock:
                    del self.__shared_files[file_id]
                    print(f'{bcolors["OKGREEN"]}File ({file_id}) removed from share list{bcolors["ENDC"]}')
            
            elif rsp.success == False:
                print(f'{bcolors["FAIL"]}File ({file_id}) not removed from share list{bcolors["ENDC"]}')
                print(f'{bcolors["FAIL"]}Reason : {rsp.error_type}{bcolors["ENDC"]}')

    def getYourSharedFilesDetails(self):
        with self.__lock:
            files = self.__shared_files

        return files

    def getSharedFilesDetailsOfPeer(self , peer_id:str):
        with self.__lock:
            if peer_id not in self.__online_peers:
                print(f'{bcolors["FAIL"]}Peer with id ({peer_id[:10]}...) not found{bcolors["ENDC"]}')
                return None
            peer:PublicPeer = self.__online_peers[peer_id]

        msg:Msg = Msg()
        msg.type = MsgType.request.value
        msg.channel = Channels.GetSharedFilesDetailsOfPeer.value

        data:GetSharedFilesDetailsOfPeerP2S = GetSharedFilesDetailsOfPeerP2S()
        data.peer_id = peer.id
        msg.data = data

        self.__msg_sender_to_server_queue.put(msg)

        try:
            rsp:GetSharedFilesDetailsOfPeerResponseS2P = self.__get_shared_files_details_from_peer_response_queue.get(timeout=5)
        except queue.Empty:
            print(f'{bcolors["FAIL"]}Request timed out{bcolors["ENDC"]}')
            return None

        return rsp.files

    def setDownloadDirectory(self , path:str):
        if not path:
            return
        
        with self.__lock:
            self.__download_directory = path

    def getDownloadDirectory(self):
        with self.__lock:
            return self.__download_directory
    
    def getSelfId(self):
        return self.__id

    def getSelfDetails(self):
        with self.__lock:
            return {
                'peer_id' : self.__id,
                'username' : self.__username,
                'ip' : self.__ip,
                'file_server_port' : self.__file_server_port
            }

    def getSelfUsername(self):
        return self.__username

    def getChatroomChats(self):
        with self.__lock:
            return self.__chatroom.getChats()
    
    def getOnlinePeers(self):
        with self.__lock:
            return self.__online_peers

    def __recieveFileFromPeer(self , conn:socket.socket , file:SharedFile):
        try:
            # print(f'{bcolors["HEADER"]}recieveFileFromPeer thread started{bcolors["ENDC"]}')

            file_path = os.path.join(self.__download_directory , file.file_name)
            remaining = file.file_size
            prev_time = datetime.datetime.now()
            # progress = tqdm.tqdm(range(file.file_size), f'{bcolors["OKGREEN"]}Downloading{bcolors["ENDC"]}', unit="B", unit_scale=True, unit_divisor=1024,)

            with open(file_path , 'wb') as f:
                while remaining > 0:
                    data = conn.recv(102400)
                    if not data:
                        break
                    f.write(data)
                    remaining -= len(data)
                    
                    if datetime.datetime.now() - prev_time >= datetime.timedelta(seconds=0.2):
                        self.notifications.put({
                            'type' : 'dp',
                            'file_id' : file.file_id,
                            'downloaded_size' : file.file_size - remaining
                        })
                        prev_time = datetime.datetime.now()
                    # progress.update(len(data))
            
            # progress.close()
            
            if remaining == 0:
                self.notifications.put({
                    'type' : 'dc',
                    'file_id' : file.file_id
                })
                # print(f'{bcolors["OKGREEN"]}File ({file.file_name}) downloaded{bcolors["ENDC"]}')
                pass
            else:
                print(f'{bcolors["FAIL"]}Error downloading file ({file.file_name}){bcolors["ENDC"]}')
                print(f'{bcolors["FAIL"]}Peer went offline{bcolors["ENDC"]}')

                self.notifications.put({
                    'type' : 'de',
                    'file_id' : file.file_id,
                    'reason' : 'Peer went offline'
                })

                
        except ConnectionResetError:
            print(f'{bcolors["FAIL"]}Error downloading file ({file.file_name}){bcolors["ENDC"]}')
            print(f'{bcolors["FAIL"]}Peer went offline{bcolors["ENDC"]}')
            os.remove(file_path)

            self.notifications.put({
                'type' : 'de',
                'file_id' : file.file_id,
                'reason' : 'Peer went offline'
            })

        except Exception as e:
            print(f'{bcolors["FAIL"]}Error downloading file ({file.file_name}){bcolors["ENDC"]}')
            print(f'{bcolors["FAIL"]}Reason : {e}{bcolors["ENDC"]}')

            self.notifications.put({
                'type' : 'de',
                'file_id' : file.file_id,
                'reason' : f'{e}'
            })

        finally:
            conn.close()
            # print(f'{bcolors["HEADER"]}recieveFileFromPeer thread stopped{bcolors["ENDC"]}')

    def downloadFileFromPeer(self , peer_id:str , file_id:str):
        if self.__download_directory == None:
            print(f'{bcolors["FAIL"]}Download directory not set{bcolors["ENDC"]}')
            return {
                'success' : "0",
                'error' : 'Download directory not set'
            }
        
        with self.__lock:
            if peer_id not in self.__online_peers:
                print(f'{bcolors["FAIL"]}Peer with id ({peer_id[:10]}...) not found{bcolors["ENDC"]}')
                return {
                    'success' : "0",
                    'error' : 'Peer not found'
                }
            peer:PublicPeer = self.__online_peers[peer_id]

        fileMapSharedByPeer = self.getSharedFilesDetailsOfPeer(peer_id)

        if fileMapSharedByPeer == None:
            return {
                'success' : "0",
                'error' : 'File not found'
            }

        if file_id not in fileMapSharedByPeer:
            print(f'{bcolors["FAIL"]}File ({file_id}) not found in share list of {peer.username}{bcolors["ENDC"]}')
            return {
                'success' : "0",
                'error' : 'File not found'
            }
        
        file:SharedFile = fileMapSharedByPeer[file_id]

        peerSocket = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        peerSocket.setsockopt(socket.SOL_TCP , socket.TCP_NODELAY , 1)
        peerSocket.settimeout(5)
        try:
            peerSocket.connect((peer.ip , peer.file_server_port))
        except Exception as e:
            print(f'{bcolors["FAIL"]}Could not connect to {peer.username}{bcolors["ENDC"]}')
            return {
                'success' : "0",
                'error' : f'{e}'
            }
        peerSocket.settimeout(None)

        msg:Msg = Msg()
        msg.type = MsgType.request.value
        msg.channel = Channels.DownloadFileRequest.value

        data:DownloadFileRequestP2P = DownloadFileRequestP2P()
        data.file_id = file_id
        msg.data = data

        msg_sender(peerSocket , msg)

        msg = msg_reciever(peerSocket)
        if msg == None:
            print(f'{bcolors["FAIL"]}Peer went offline{bcolors["ENDC"]}')
            return {
                'success' : "0",
                'error' : 'Peer went offline'
            }

        if msg.type == MsgType.result.value and msg.channel == Channels.DownloadFileRequest.value:
            data2:ResultResponse = msg.data
            if data2.success == False:
                print(f'{bcolors["FAIL"]}Error downloading file ({file_id}){bcolors["ENDC"]}')
                print(f'{bcolors["FAIL"]}Reason : {data2.error_type}{bcolors["ENDC"]}')
                return {
                    'success' : "0",
                    'error' : data2.error_type
                }
            
            elif data2.success == True:
                threading.Thread(target = self.__recieveFileFromPeer , args=(peerSocket , file) , daemon=True).start()
                return {
                    'success' : "1",
                    'error' : ''
                }

            else:
                print(f'{bcolors["FAIL"]}Invalid response from peer{bcolors["ENDC"]}')
        
        else:
            print(f'{bcolors["FAIL"]}Invalid response from peer{bcolors["ENDC"]}')
    
        return {
            'success' : "0",
            'error' : 'Invalid response from peer'
        }