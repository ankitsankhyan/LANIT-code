
import hashlib
import math
import os
import pickle
import socket
import tkinter as tk
from tkinter import filedialog
from typing import Any

from constants import Constants
from enums import MsgType
from structs import Msg, ResultResponse


def recieve_payload(sock:socket.socket , payload_length:int):
    remaining = payload_length
    payload = bytes()

    while remaining > 0:
        data = sock.recv(min(1024 , remaining))
        remaining -= len(data)
    
        if not data:
            break

        payload += data

    return payload

def msg_sender(sock:socket.socket , payload:Any):
    payload_in_bytes = pickle.dumps(payload)
    payload_length:int = len(payload_in_bytes)

    sock.sendall(f'{payload_length:<{Constants.MSGLEN_LEN.value}}'.encode() + payload_in_bytes)

def msg_reciever(sock:socket.socket):
    payload_length =sock.recv(Constants.MSGLEN_LEN.value).decode()
    
    if payload_length == '':
        return None

    payload_length = int(payload_length)

    payload_in_bytes = recieve_payload(sock , payload_length)
    payload:Msg = pickle.loads(payload_in_bytes)

    return payload

def create_success_msg(channel:str , extra_data:Any = None) -> Msg:
    msg:Msg = Msg()
    msg.type = MsgType.result.value
    msg.channel = channel
    
    data:ResultResponse = ResultResponse()
    data.success = True
    data.data = extra_data
    msg.data = data

    return msg

def create_error_msg(channel:str , error_type:str) -> Msg:
    msg:Msg = Msg()
    msg.type = MsgType.result.value
    msg.channel = channel
    
    data:ResultResponse = ResultResponse()
    data.success = False
    data.error_type = error_type
    msg.data = data

    return msg

def get_your_ip():
    # return '127.0.0.1'
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    try:
        s.connect(("8.8.8.8", 80))
    except Exception:
        return "127.0.0.1"
    return s.getsockname()[0]

def calculate_sha256(file_path):
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        chunk = f.read(4096)
        while chunk:
            hash_sha256.update(chunk)
            chunk = f.read(4096)
    return hash_sha256.hexdigest()

def get_file_details(file_path:str):
    filename = file_path.split("/")[-1]
    filesize = os.path.getsize(file_path)
    filehash = calculate_sha256(file_path)

    return (filename , filesize , filehash)

def getFiles():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    root.update()
    
    filepaths = filedialog.askopenfilenames()
    root.attributes('-topmost', False)
    root.destroy()
    
    return filepaths

def getDirectory():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    root.update()
    
    dir = filedialog.askdirectory()
    root.attributes('-topmost', False)
    root.destroy()
    
    return dir

def format_size(size_bytes):
    units = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
    if size_bytes == 0:
        return "0 Bytes"
    
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {units[i]}"