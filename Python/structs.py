from collections import deque
import datetime
import socket
from typing import Any

class Peer:
    id:str = None
    username:str = None
    ip:str = None
    file_server_port:int = None
    conn:socket.socket = None
    addr:tuple[str , int] = None

class PublicPeer:
    id:str = None
    username:str = None
    ip:str = None
    file_server_port:int = None


class SharedFile:
    file_id:str = None
    file_hash:str = None
    file_name:str = None
    file_path:str = None
    file_size:int = None


class Msg:
    type:str = None
    channel:str = None
    data:Any = None

class Chat:
    peer_id:str = None
    username:str = None
    msg:str = None
    send_time:datetime.datetime = None


class ResultResponse:
    success:bool = None
    error_type:str = None


# ---------------------------------------Username Request---------------------------------------
class UsernameRequestP2S:
    username:str = None

# ---------------------------------------File Server Detail Request---------------------------------------
class FileServerDetailsRequestP2S:
    port:int = None


# ---------------------------------------ID Detail of Peer Request---------------------------------------
class IdOfPeerRequestS2P:
    peer_id:str = None


# ---------------------------------------Peer List---------------------------------------    
class PeerListRequestS2P:
    peers:list[PublicPeer] = None

class PeerListUpdateS2P:
    peer:PublicPeer = None
    change:int = None

# ---------------------------------------Chatroom Chats---------------------------------------    
class ChatroomChatsRequestS2P:
    chats:deque = None

# ---------------------------------------Broadcast To Server---------------------------------------
class BroadcastMsgRequestP2S:
    msg:str = None
    send_time:datetime.datetime = None

class ChatroomChatsUpdateS2P:
    peer_id:str = None
    username:str = None
    msg:str = None
    send_time:datetime.datetime = None


# ---------------------------------------Update Share List---------------------------------------
class AddFileToShareListP2S:
    file_name:str = None
    file_path:str = None
    file_size:int = None
    file_hash:str = None

class AddFileTOShareListResponseS2P:
    file_id:str = None

class RemoveFileFromShareListP2S:
    file_id:str = None

# ---------------------------------------Query Share List---------------------------------------
class GetSharedFilesDetailsOfPeerP2S:
    peer_id:str = None

class GetSharedFilesDetailsOfPeerResponseS2P:
    files:dict[str , SharedFile] = None

# ---------------------------------------ID Detail of Peer Request---------------------------------------
class IdOfPeerRequestS2P:
    peer_id:str = None

# ---------------------------------------Download File---------------------------------------
class DownloadFileRequestP2P:
    file_id:str = None
