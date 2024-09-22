

from enum import Enum


class MsgType(Enum):
    request = '0'
    response = '1'
    result = '2'

class Channels(Enum):
    UsernameRequest = '0'
    FileServerDetailsRequest = '1'
    IdOfPeerRequest = '2'
    PeerListRequest = '3'
    PeerListUpdate = '4'
    ChatroomChatsRequest = '5'
    BroadcastMsg = '6'
    ChatroomChatsUpdate = '7'
    AddFileToShareList = '8'
    RemoveFileFromShareList = '9'
    GetSharedFilesDetailsOfPeer = '10'
    DownloadFileRequest = '11'


class ErrorType(Enum):
    UsernameAlreadyTaken = '0'

