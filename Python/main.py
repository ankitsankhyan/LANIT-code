import asyncio
import datetime
import multiprocessing
import queue
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from peer import Peer
from pydantic import BaseModel, Field
from colors import bcolors
from server import Server
from structs import SharedFile
import argparse

app = FastAPI()
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


peer = None
server = None

@app.get("/")
async def root():
    return {"message": "Hello World"}

# ============================================START SERVER============================================
@app.get("/start-server")
async def start_server():
    global server , peer
    if server is not None:
        return {
            "success": "0",
            "error": "Server already started"
        }

    if peer is not None:
        return {
            "success": "0",
            "error": "Peer already started"
        }
    
    server = Server()
    try:
        host , port = server.startServer()

        return {
            "success": "1",
            "host": host,
            "port": port
        }
        
    except Exception as e:
        return {
            "success": "0", 
            "error": str(e)
        }



# ============================================START PEER============================================
class StartPeerReq(BaseModel):
    host:str = Field(default="192.168.69.149" , pattern='^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$') 
    port:int = Field(default=12345 , gt=0 , le=65535)
    username:str = Field(default="hsr" , min_length=3 , max_length=32)

@app.post("/start-peer")
async def start_peer(data:StartPeerReq):
    global peer , server

    if server is not None:
        return {
            "success": "0",
            "error": "Server already started"
        }

    if peer is not None:
        return {
            "success": "0",
            "error": "Peer already started"
        }
    
    peer = Peer(data.host , data.port , data.username)
    try:
        peer.startPeer()
        
        return {"success": "1" , **peer.getSelfDetails()}

    except Exception as e:
        return {
            "success": "0", 
            "error": str(e)
        }

# ============================================ONLINE PEERS============================================
class OnlinePeerResp(BaseModel):
    peer_id:str
    username:str
    ip:str
    file_server_port:int

@app.get('/peers/list' , response_model=list[OnlinePeerResp])
async def get_peers_list():
    if peer is None:
        return []

    onlinePeers = []

    for p in peer.getOnlinePeers().values():
        onlinePeers.append(OnlinePeerResp(
            peer_id = p.id,
            username = p.username,
            ip = p.ip,
            file_server_port = p.file_server_port
        ))
    
    return onlinePeers


# ============================================BROADCAST MSG============================================
class BroadcastMsg(BaseModel):
    msg:str

@app.post('/broadcast-msg')
async def broadcast_msg(data:BroadcastMsg):
    if peer is None:
        return {
            "success": "0",
            "error": "Peer not started"
        }

    peer.broadcastMsg(data.msg)

    return {"success": "1"}

# ============================================GET CHATROOM CHATS==============================================
class ChatResp(BaseModel):
    peer_id:str
    username:str
    msg:str
    send_time:datetime.datetime

@app.get('/chats' , response_model=list[ChatResp])
async def get_chats():
    if peer is None:
        return []

    resp = []

    for chat in peer.getChatroomChats():
        resp.append(ChatResp(
            peer_id = chat.peer_id,
            username = chat.username,
            msg = chat.msg,
            send_time = chat.send_time
        ))

    return resp


# ============================================Add File To Share List============================================
class AddFileToShareListReq(BaseModel):
    file_path:str = "D:/One Piece/EP.68.v1.1080p.mp4"

class AddFileResponse(BaseModel):
    success:str
    file_id:str|None = None
    file_path:str|None = None
    file_name:str|None = None
    file_size:int|None = None
    file_hash:str|None = None
    error:str|None = None

@app.post('/add-file-to-share-list' , response_model=AddFileResponse)
async def add_file_to_share_list(data:AddFileToShareListReq):
    if peer is None:
        return {
            "success": "0",
            "error": "Peer not started"
        }
    
    try:
        temp:list[SharedFile] = peer.addFilesToShareList([data.file_path])

        resp = AddFileResponse(
            success = "1",
            file_id = temp[0].file_id,
            file_path = temp[0].file_path,
            file_name = temp[0].file_name,
            file_size = temp[0].file_size,
            file_hash = temp[0].file_hash
        )

        return resp
    
    except Exception as e:
        resp = AddFileResponse(
            success = "0",
            error = str(e)
        )

        print(e)

        return resp

# ============================================Remove File From Share List==============================================
class RemoveFileFromShareListReq(BaseModel):
    file_id:str

@app.post('/remove-file-from-share-list')
async def remove_file_from_share_list(data:RemoveFileFromShareListReq):
    if peer is None:
        return {
            "success": "0",
            "error": "Peer not started"
        }

    peer.removeFilesFromShareList([data.file_id])

    return {"success": "1"}

# ============================================Get Shared Files==============================================
class GetSharedFilesResp(BaseModel):
    file_id:str
    file_name:str
    file_path:str
    file_size:int
    file_hash:str

@app.get('/shared-files' , response_model=list[GetSharedFilesResp])
async def get_shared_files():
    if peer is None:
        return []

    resp = []

    for file in peer.getYourSharedFilesDetails().values():
        resp.append(GetSharedFilesResp(
            file_id = file.file_id,
            file_name = file.file_name,
            file_path = file.file_path,
            file_size = file.file_size,
            file_hash = file.file_hash
        ))
    
    return resp

@app.get('/shared-files/{peer_id}' , response_model=list[GetSharedFilesResp])
async def get_shared_files_of_peer(peer_id:str):
    if peer is None:
        return []

    resp = []

    for file in peer.getSharedFilesDetailsOfPeer(peer_id).values():
        resp.append(GetSharedFilesResp(
            file_id = file.file_id,
            file_name = file.file_name,
            file_path = file.file_path,
            file_size = file.file_size,
            file_hash = file.file_hash
        ))
    
    return resp


# ============================================Download File==============================================
class DownloadFileReq(BaseModel):
    file_id:str
    peer_id:str

@app.post('/download-file')
async def download_file(data:DownloadFileReq):
    if peer is None:
        return {
            "success": "0",
            "error": "Peer not started"
        }
    
    if peer.getDownloadDirectory() == None:
        return {
            "success": "0",
            "error": "Download directory not set"
        }

    return peer.downloadFileFromPeer(data.peer_id , data.file_id)

# ============================================Download Directory==============================================
class DownloadDirReq(BaseModel):
    dir_path:str
    
@app.post('/download-dir')
async def download_dir(data:DownloadDirReq):
    if peer is None:
        return {
            "success": "0",
            "error": "Peer not started"
        }

    try:
        peer.setDownloadDirectory(data.dir_path)

        return {"success": "1"}

    except Exception as e:
        return {
            "success": "0",
            "error": str(e)
            }


# @app.get("/restart-server")
# def restart_server():
#     try:
#         # Execute the command to restart the server process
#         subprocess.Popen(["fastapi", "dev"])  # Adjust the command as per your setup
#         return {"message": "Server restart initiated"}
#     except Exception as e:
#         return {"error": str(e)}



async def manager_send_data(websocket:WebSocket):
    while True:
        await asyncio.sleep(0)
        try:
            data = peer.notifications.get(block=False)  
        except queue.Empty:
            continue
        await websocket.send_json(data)

# async def websocket_receiver(websocket: WebSocket):
#     while True:
#         data = await websocket.receive_json()
#         print(data)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):        
    try:
        await websocket.accept()
        print(f'{bcolors["OKGREEN"]}Frontend connected{bcolors["ENDC"]}')
        asyncio.create_task(manager_send_data(websocket))

        while True:
            data = await websocket.receive_json()
            print(data)

    except WebSocketDisconnect:
        print(f'{bcolors["FAIL"]}Frontend disconnected{bcolors["ENDC"]}')

if __name__ == '__main__':
    multiprocessing.freeze_support()  # For Windows support

    parser = argparse.ArgumentParser(description='Start the Uvicorn server.')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on.')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker processes.')

    args = parser.parse_args()
    port = args.port
    workers = args.workers

    uvicorn.run(app, host="127.0.0.1", port=port, reload=False, workers=workers)

