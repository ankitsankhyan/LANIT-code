


from collections import deque
import queue
import socket
from enums import Channels, MsgType , ErrorType
from utils import (
    get_your_ip,
    msg_reciever,
    msg_sender,
    create_error_msg,
    create_success_msg,
)
from structs import (
    AddFileTOShareListResponseS2P,
    AddFileToShareListP2S,
    BroadcastMsgRequestP2S,
    ChatroomChatsRequestS2P,
    ChatroomChatsUpdateS2P,
    FileServerDetailsRequestP2S,
    GetSharedFilesDetailsOfPeerP2S,
    GetSharedFilesDetailsOfPeerResponseS2P,
    IdOfPeerRequestS2P,
    Msg,
    Peer,
    PeerListRequestS2P,
    PeerListUpdateS2P,
    PublicPeer,
    RemoveFileFromShareListP2S,
    SharedFile,
    UsernameRequestP2S
)
import threading
import uuid
from chatroom import Chatroom
from colors import bcolors


class Server:
    def __init__(self , port:int = 0 , backlog:int = 5):
        self.host:str = get_your_ip()
        self.port:int = port
        self.backlog:int = backlog

        self.__lock = threading.Lock()
        self.registered_peers:dict[str , Peer] = dict()
        self.uname_to_id:dict[str , str] = dict()
        self.ip_to_id:dict[tuple , str] = dict()
        self.shared_files:dict[str , dict[str , SharedFile]] = dict()
        self.send_queues:dict[str , queue.Queue] = dict()

        self.__chatroom = Chatroom()

    def __createSocket(self):
        self.socket = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET , socket.SO_REUSEADDR , 1)
        self.socket.setsockopt(socket.SOL_TCP , socket.TCP_NODELAY , 1)

        print(f'{bcolors["OKGREEN"]}Socket created : {self.socket}{bcolors["ENDC"]}')
    
    def __bindSocket(self):
        self.socket.bind((self.host , self.port))
        if self.port == 0:
            self.port = self.socket.getsockname()[1]
        self.socket.listen(self.backlog)

        print(f'{bcolors["OKGREEN"]}Socket binded : {self.socket}{bcolors["ENDC"]}')
    
    def startServer(self):
        self.__createSocket()
        self.__bindSocket()

        threading.Thread(target = self.__acceptConnections , daemon=True , name='__acceptConnections').start()
        return (self.host , self.port)

    def __getUsernameFromPeer(self , conn:socket.socket , addr:tuple):
        msg:Msg = msg_reciever(conn)

        if msg == None:
            return None

        elif msg.type == MsgType.request.value and msg.channel == Channels.UsernameRequest.value:
            data:UsernameRequestP2S = msg.data
            username = data.username

            if username in self.uname_to_id:
                msg:Msg = create_error_msg(Channels.UsernameRequest.value , ErrorType.UsernameAlreadyTaken.value)
                msg_sender(conn , msg)
                return None
            
            else:
                msg:Msg = create_success_msg(Channels.UsernameRequest.value)
                msg_sender(conn , msg)

                return username

        return None

    def __getFileServerDetailsOfPeer(self , conn:socket.socket , addr:tuple):
        msg:Msg = msg_reciever(conn)

        if msg == None:
            return None

        elif msg.type == MsgType.request.value and msg.channel == Channels.FileServerDetailsRequest.value:
            data:FileServerDetailsRequestP2S = msg.data
            peer_file_server_port = data.port

            return peer_file_server_port

        return None

    def __sendIdOfPeerToPeer(self , peer:Peer):
        msg:Msg = Msg()
        msg.type = MsgType.request.value
        msg.channel = Channels.IdOfPeerRequest.value

        data:IdOfPeerRequestS2P= IdOfPeerRequestS2P()
        data.peer_id = peer.id
        msg.data = data

        msg_sender(peer.conn , msg)

    def __sendListOfOnlinePeersToPeer(self , peer:Peer):
        with self.__lock:
            allPeers = []
            for p in tuple(self.registered_peers.values()):
                publicPeer = PublicPeer()
                publicPeer.id = p.id
                publicPeer.username = p.username
                publicPeer.ip = p.ip
                publicPeer.file_server_port = p.file_server_port
                allPeers.append(publicPeer)
            
        msg:Msg = Msg()
        msg.type = MsgType.request.value
        msg.channel = Channels.PeerListRequest.value

        data:PeerListRequestS2P = PeerListRequestS2P()
        data.peers = allPeers
        msg.data = data

        msg_sender(peer.conn , msg)

    def __sendChatroomChatsToPeer(self , peer:Peer):
        with self.__lock:
            chats:deque = self.__chatroom.getChats()

        msg:Msg = Msg()
        msg.type = MsgType.request.value
        msg.channel = Channels.ChatroomChatsRequest.value

        data:ChatroomChatsRequestS2P = ChatroomChatsRequestS2P()
        data.chats = chats
        msg.data = data

        msg_sender(peer.conn , msg)

    def __acceptConnections(self):
        print(f'{bcolors["HEADER"]}Server listening on {self.host}:{self.port}{bcolors["ENDC"]}')
        while True:
            conn, addr = self.socket.accept()
            print(f'{bcolors["OKGREEN"]}TCP Connection established with {addr}{bcolors["ENDC"]}')

            username = self.__getUsernameFromPeer(conn , addr)
            if username == None:
                self.__handleConnectionResetFromPeer(conn , addr)
                continue

            peer_file_server_port = self.__getFileServerDetailsOfPeer(conn , addr)
            if peer_file_server_port == None:
                self.__handleConnectionResetFromPeer(conn , addr)
                continue
            
            peer = Peer()
            peer.id = uuid.uuid4().hex
            peer.username = username
            peer.ip = addr[0]
            peer.file_server_port = peer_file_server_port
            peer.conn = conn
            peer.addr = addr

            with self.__lock:
                self.registered_peers[peer.id] = peer
                self.uname_to_id[username] = peer.id
                self.ip_to_id[addr] = peer.id
                self.send_queues[peer.id] = queue.Queue()
                self.shared_files[peer.id] = dict()

            self.__sendIdOfPeerToPeer(peer)
            self.__sendListOfOnlinePeersToPeer(peer)
            self.__sendChatroomChatsToPeer(peer)

            print(f'{bcolors["OKGREEN"]}{peer.username} joined the server{bcolors["ENDC"]}')
            threading.Thread(target = self.__msgSenderToPeer , args=(peer,) , daemon=True , name=f'__MsgSenderToPeer-{peer.addr}').start()
            threading.Thread(target = self.__msgRecieverFromPeer , args=(peer,) , daemon=True , name=f'__MsgRecieverFromPeer-{peer.addr}').start()

            self.__notifyPeerListChange(peer , 1)

    def __msgSenderToPeer(self , peer:Peer):
        try:                
            print(f'{bcolors["HEADER"]}__MsgSenderToPeer thread started for peer {peer.addr}({peer.username}){bcolors["ENDC"]}')

            while True:
                msg:Msg = self.send_queues[peer.id].get()

                if msg == 'stop':
                    break

                msg_sender(peer.conn , msg)

        except Exception as e:
            print(f'{bcolors["FAIL"]}Unexpected error occured in __MsgSenderToPeer thread of peer {peer.addr}({peer.username}): {e}{bcolors["ENDC"]}')

        finally: 
            print(f'{bcolors["HEADER"]}__MsgSenderToPeer thread stopped for peer {peer.addr}({peer.username}){bcolors["ENDC"]}')

    def __msgRecieverFromPeer(self , peer:Peer):
        try:
            print(f'{bcolors["HEADER"]}__MsgRecieverFromPeer thread started for peer {peer.addr}({peer.username}){bcolors["ENDC"]}')

            while True:
                msg:Msg = msg_reciever(peer.conn)
                
                if msg == None:
                    break

                if msg.type == MsgType.request.value:
                    if msg.channel == Channels.BroadcastMsg.value:
                        self.__handleBroadcastMsgFromPeer(peer , msg.data)
                    
                    elif msg.channel == Channels.AddFileToShareList.value:
                        self.__handleAddFileToShareListFromPeer(peer , msg.data)

                    elif msg.channel == Channels.RemoveFileFromShareList.value:
                        self.__handleRemoveFileFromShareListFromPeer(peer , msg.data)

                    elif msg.channel == Channels.GetSharedFilesDetailsOfPeer.value:
                        self.__handleGetSharedFilesDetailsOfPeer(peer , msg.data)

                elif msg.type == MsgType.response.value:
                    pass
        
        except ConnectionResetError:
            self.__handleConnectionResetFromPeer(peer.conn , peer.addr)

        except Exception as e:
            print(f'{bcolors["FAIL"]}Unexpected error occured in __MsgRecieverFromPeer thread of peer {peer.addr}({peer.username}): {e}{bcolors["ENDC"]}')

        finally: 
            print(f'{bcolors["HEADER"]}__MsgRecieverFromPeer thread stopped for peer {peer.addr}({peer.username}){bcolors["ENDC"]}')

    def __notifyPeerListChange(self , peer:Peer , change:int):
        try:
            publicPeer = PublicPeer()
            publicPeer.username = peer.username
            publicPeer.id = peer.id
            publicPeer.ip = peer.ip
            publicPeer.file_server_port = peer.file_server_port

            msg:Msg = Msg()
            msg.type = MsgType.request.value
            msg.channel = Channels.PeerListUpdate.value

            data:PeerListUpdateS2P = PeerListUpdateS2P()
            data.peer = publicPeer
            data.change = change
            msg.data = data

            for p in tuple(self.registered_peers.values()):
                if p.id == peer.id:
                    continue
                self.send_queues[p.id].put(msg)


        except Exception as e:
            print(f'{bcolors["FAIL"]}Unexpected error occured while notifying peer list change: {e}{bcolors["ENDC"]}')

    def __handleBroadcastMsgFromPeer(self , peer:Peer , data:BroadcastMsgRequestP2S):
        try:
            msg_to_broadcast = data.msg
            send_time = data.send_time

            self.__chatroom.addChat(peer.id , peer.username , msg_to_broadcast , send_time)                

            msg:Msg = Msg()
            msg.type = MsgType.request.value
            msg.channel = Channels.ChatroomChatsUpdate.value
            
            data:ChatroomChatsUpdateS2P = ChatroomChatsUpdateS2P()
            data.peer_id = peer.id
            data.username = peer.username
            data.msg = msg_to_broadcast
            data.send_time = send_time
            msg.data = data

            with self.__lock:
                for p in tuple(self.registered_peers.values()):
                    self.send_queues[p.id].put(msg)

            print(f'{bcolors["OKGREEN"]}broadcasted msg from {peer.username} : {msg_to_broadcast}{bcolors["ENDC"]}')
        
        except Exception as e:
            print(f'{bcolors["FAIL"]}Unexpected error occured while broadcasting msg from {peer.addr}({peer.username}): {e}{bcolors["ENDC"]}')

    def __handleAddFileToShareListFromPeer(self , peer:Peer , data:AddFileToShareListP2S):
        file = SharedFile()
        file.file_id = uuid.uuid4().hex
        file.file_name = data.file_name
        file.file_size = data.file_size
        file.file_hash = data.file_hash
        file.file_path = data.file_path

        with self.__lock:
            self.shared_files[peer.id][file.file_id] = file

        msg:Msg = Msg()
        msg.type = MsgType.response.value
        msg.channel = Channels.AddFileToShareList.value

        data:AddFileTOShareListResponseS2P = AddFileTOShareListResponseS2P()
        data.file_id = file.file_id
        msg.data = data

        with self.__lock:
            self.send_queues[peer.id].put(msg)

        print(f'{bcolors["OKGREEN"]}added file ({file.file_name}) to share list of {peer.username}{bcolors["ENDC"]}')

    def __handleRemoveFileFromShareListFromPeer(self , peer:Peer , data:RemoveFileFromShareListP2S):
        with self.__lock:
            file = self.shared_files[peer.id][data.file_id]

        if file == None:
            print(f'{bcolors["FAIL"]}File ({data.file_id}) not found in share list of {peer.username}{bcolors["ENDC"]}')

            msg:Msg = create_error_msg(Channels.RemoveFileFromShareList.value , f'File ({data.file_id}) not found in share list of {peer.username}')
            self.send_queues[peer.id].put(msg)

        else:
            file = self.shared_files[peer.id][data.file_id]
            del self.shared_files[peer.id][data.file_id]

            msg:Msg = create_success_msg(Channels.RemoveFileFromShareList.value) 
            self.send_queues[peer.id].put(msg)

            print(f'{bcolors["OKGREEN"]}removed file ({file.file_name}) from share list of {peer.username}{bcolors["ENDC"]}')

    def __handleGetSharedFilesDetailsOfPeer(self , peer:Peer , data:GetSharedFilesDetailsOfPeerP2S):
        with self.__lock:
            peerWhoseListToGet:Peer = self.registered_peers[data.peer_id]
            files:dict[str , SharedFile] = self.shared_files[peerWhoseListToGet.id]
        
        rsp:Msg = Msg()
        rsp.type = MsgType.response.value
        rsp.channel = Channels.GetSharedFilesDetailsOfPeer.value

        data:GetSharedFilesDetailsOfPeerResponseS2P = GetSharedFilesDetailsOfPeerResponseS2P()
        data.files = files
        rsp.data = data

        self.send_queues[peer.id].put(rsp)

        print(f'{bcolors["OKGREEN"]}sent list of shared files of {peerWhoseListToGet.username} to {peer.username}{bcolors["ENDC"]}')


    def __handleConnectionResetFromPeer(self , conn:socket.socket , addr:tuple):
        try:
            with self.__lock:
                if addr in self.ip_to_id:
                    peer = self.registered_peers[self.ip_to_id[addr]]
                    self.send_queues[peer.id].put('stop')

                    del self.registered_peers[peer.id]
                    del self.uname_to_id[peer.username]
                    del self.ip_to_id[peer.addr]
                    del self.send_queues[peer.id]
                    del self.shared_files[peer.id]

                    self.__notifyPeerListChange(peer , -1)

                    print(f'{bcolors["FAIL"]}{peer.addr}({peer.username}) left the server!{bcolors["ENDC"]}')

            conn.close()
            print(f'{bcolors["HEADER"]}TCP Connection closed with {addr}{bcolors["ENDC"]}')

        except Exception as e:
            print(f'{bcolors["FAIL"]}Unexpected error occured while handling connection reset from {addr}: {e}{bcolors["ENDC"]}')
