
from collections import deque
import datetime
import threading
from structs import Chat

class Chatroom:
    def __init__(self , limit:int = 100):
        self.__chats:deque[Chat] = deque()
        self.__limit = limit
        self.__lock = threading.Lock()

    def addChat(self , peer_id:str , username:str , msg:str , send_time:datetime.datetime):
        with self.__lock:
            chat = Chat()
            chat.peer_id = peer_id
            chat.username = username
            chat.msg = msg
            chat.send_time = send_time

            if len(self.__chats) == self.__limit:
                self.__chats.popleft()
            self.__chats.append(chat)

    def getChats(self):
        with self.__lock:
            return self.__chats
    
    def updateChats(self , chats:deque[Chat]):
        with self.__lock:
            self.__chats = chats




