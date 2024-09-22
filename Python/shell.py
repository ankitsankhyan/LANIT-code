



import inquirer
import pytz
import tabulate
from peer import Peer
from server import Server
from colors import bcolors
from structs import PublicPeer, SharedFile
from utils import format_size, getDirectory, getFiles


class Shell:
    def __init__(self):
        self.local_tz = pytz.timezone('Asia/Kolkata')

    def start(self):
        questions = [
            inquirer.List(
                'purpose',
                message="What would you like to be",
                choices=[
                    '1. Server', 
                    '2. Peer',
                ],
                carousel=True
            )]
        answers = inquirer.prompt(questions)

        if answers['purpose'] == '1. Server':
            self.startServer()

        elif answers['purpose'] == '2. Peer':
            self.startPeer()

    def startServer(self):
        server = Server(port=12345 , backlog=5)
        server.startServer()
        print(f'Enter "stop" to stop server')
        while True:
            msg = input()

            if msg == 'stop':
                break

    def startPeer(self):
        questions = [
            inquirer.Text('host', message="Enter server IP" , default='127.0.0.1'),
            inquirer.Text('port', message="Enter server Port" , default=12345),
            inquirer.Text('username', message="Enter your username" , default='hsr')
        ]
        answers = inquirer.prompt(questions)

        try:
            self.peer:Peer = Peer(answers['host'] , int(answers['port']) , answers['username'])
            self.peer.startPeer()

        except Exception as e:
            print(f'{bcolors["FAIL"]}Error occured while starting peer : {e}{bcolors["ENDC"]}')
            exit()

        self.showMenu()

    def showListOfOnlinePeers(self):
        online_peers = self.peer.getOnlinePeers().values()

        headers = [
            f'{bcolors["HEADER"]}S.NO{bcolors["ENDC"]}', 
            f'{bcolors["HEADER"]}PEER ID{bcolors["ENDC"]}',
            f'{bcolors["HEADER"]}USERNAME{bcolors["ENDC"]}'
        ]
        table = []
        for i , peer in enumerate(online_peers):
            if peer.id == self.peer.getSelfId():
                table.append([
                    f'{bcolors["OKGREEN"]}{i+1}{bcolors["ENDC"]}' , 
                    f'{bcolors["OKGREEN"]}{peer.id[:10]}...{bcolors["ENDC"]}' , 
                    f'{bcolors["OKGREEN"]}{peer.username}{bcolors["ENDC"]}'
                ])
            else:
                table.append([
                    i+1 , 
                    f'{peer.id[:10]}...' ,
                    peer.username
                ])
        print(tabulate.tabulate(table, headers, tablefmt="fancy_grid"))
    
    def selectFromOnlinePeers(self , online_peers:tuple[PublicPeer]):
        questions = [
            inquirer.List(
                'peer_id',
                message="Select peer", 
                choices=[
                    f'{peer.username} {peer.id}'  if peer.id != self.peer.getSelfId() 
                    else f'{bcolors["OKGREEN"]}{peer.username}{bcolors["ENDC"]} {peer.id}' 
                    for peer in online_peers]
            )
        ]
        answers = inquirer.prompt(questions)
        return answers['peer_id'].split(' ')[-1]

    def broadcastAMessage(self):
        questions = [
            inquirer.Text('msg', message="Enter message"),
        ]
        answers = inquirer.prompt(questions)

        self.peer.broadcastMsg(answers['msg'])
    
    def displayChatroom(self):
        chats = self.peer.getChatroomChats()

        table = []
        for chat in chats:
            if chat.peer_id == self.peer.getSelfId():
                table.append([
                    f'{bcolors["OKGREEN"]}{chat.username}{bcolors["ENDC"]}', 
                    f'{bcolors["OKGREEN"]}{chat.msg}{bcolors["ENDC"]}',
                    f'{bcolors["OKGREEN"]}{str(chat.send_time.astimezone(self.local_tz))[:19]}{bcolors["ENDC"]}'
                ]) 
            else:
                table.append([
                    chat.username,
                    chat.msg,
                    str(chat.send_time.astimezone(self.local_tz))[:19],
                ])
        if len(table) == 0:
            print(f'{bcolors["FAIL"]}Empty chatroom...{bcolors["ENDC"]}')
        else:
            print(tabulate.tabulate(table, tablefmt="simple_grid"))

    def selectFilesFromFilesList(self , files:list[SharedFile]):
        questions = [
            inquirer.Checkbox(
                'file_id',
                message="Select files using space",
                choices=[
                    f'{file.file_name} {format_size(file.file_size)} {file.file_id}' 
                    for file in files
                ]
            )
        ]
        answers = inquirer.prompt(questions)
        result = []
        for i in answers['file_id']:
            result.append(i.split(' ')[-1])
        return result

    def addFilesToShareList(self):
        filepaths = getFiles()
        self.peer.addFilesToShareList(filepaths)

    def removeFilesFromShareList(self):
        files = self.peer.getYourSharedFilesDetails().values()
        if len(files) == 0:
            print(f'{bcolors["FAIL"]}You have not shared any files...{bcolors["ENDC"]}')
            return

        file_ids = self.selectFilesFromFilesList(files)

        self.peer.removeFilesFromShareList(file_ids)

    def displayFilesList(self , files:list[SharedFile]):
        headers = [
            f'{bcolors["HEADER"]}S.NO{bcolors["ENDC"]}' ,
            f'{bcolors["HEADER"]}FILE ID{bcolors["ENDC"]}' ,
            f'{bcolors["HEADER"]}FILE NAME{bcolors["ENDC"]}' ,
            f'{bcolors["HEADER"]}FILE SIZE{bcolors["ENDC"]}' ,            
        ]
        table = []
        for i , file in enumerate(files):
            table.append([
                i+1, 
                f'{file.file_id[:10]}...', 
                file.file_name, 
                format_size(file.file_size)
            ])
        print(tabulate.tabulate(table, headers , tablefmt="fancy_grid"))

    def displayFilesSharedByYou(self):
        files:list[SharedFile] = self.peer.getYourSharedFilesDetails().values()
        print(f'{bcolors["HEADER"]}Files Shared By You{bcolors["ENDC"]}')
        self.displayFilesList(files)

    def displayFilesSharedByOtherPeers(self):
        online_peers_map = self.peer.getOnlinePeers()
        peer_id = self.selectFromOnlinePeers(online_peers_map.values())

        if peer_id == self.peer.getSelfId():
            files:list[SharedFile] = self.peer.getYourSharedFilesDetails().values()

        else:
            files:list[SharedFile] = self.peer.getSharedFilesDetailsOfPeer(peer_id).values()
        
        print(f'{bcolors["HEADER"]}Files Shared By {online_peers_map[peer_id].username}{bcolors["ENDC"]}')
        self.displayFilesList(files)

    def setDownloadDirectory(self):
        path = getDirectory()
        if path:
            self.peer.setDownloadDirectory(path)
    
    def displayDownloadDirectory(self):
        print(f'{bcolors["HEADER"]}Download Directory: {bcolors["ENDC"]}{bcolors["OKGREEN"]}{self.peer.getDownloadDirectory()}{bcolors["ENDC"]}')

    def downloadFileFromPeer(self):
        online_peers_map = self.peer.getOnlinePeers()
        peer_id = self.selectFromOnlinePeers(online_peers_map.values())

        if peer_id == self.peer.getSelfId():
            print(f'{bcolors["FAIL"]}You cannot download files from yourself...{bcolors["ENDC"]}')
            return

        files:list[SharedFile] = self.peer.getSharedFilesDetailsOfPeer(peer_id).values()
        if len(files) == 0:
            print(f'{bcolors["FAIL"]}{online_peers_map[peer_id].username} is not sharing any files...{bcolors["ENDC"]}')
            return

        file_ids = self.selectFilesFromFilesList(files)

        for file_id in file_ids:
            self.peer.downloadFileFromPeer(peer_id , file_id)

    def showMenu(self):
        questions = [
            inquirer.List(
                'action',
                message="What action would you like to perform?",
                choices=[
                    '1. Show list of online peers', 
                    '2. Broadcast a message to everyone',
                    '3. Display chatroom',
                    '4. Add files to your share list',
                    '5. Remove files from your share list',
                    '6. Display files shared by you',
                    '7. Display files shared by other peers',
                    '8. Set your download directory',
                    '9. Display your download directory',
                    '10. Download file from a peer',
                    '0. Exit',
                ],
                carousel=True
            )]
        answers = inquirer.prompt(questions)

        if answers['action'].startswith('1.'):
            self.showListOfOnlinePeers()
        
        elif answers['action'].startswith('2.'):
            self.broadcastAMessage()
        
        elif answers['action'].startswith('3.'):
            self.displayChatroom()
        
        elif answers['action'].startswith('4.'):
            self.addFilesToShareList()
        
        elif answers['action'].startswith('5.'):
            self.removeFilesFromShareList()
        
        elif answers['action'].startswith('6.'):
            self.displayFilesSharedByYou()
        
        elif answers['action'].startswith('7.'):
            self.displayFilesSharedByOtherPeers()
        
        elif answers['action'].startswith('8.'):
            self.setDownloadDirectory()
        
        elif answers['action'].startswith('9.'):
            self.displayDownloadDirectory()

        elif answers['action'].startswith('10.'):
            self.downloadFileFromPeer()

        elif answers['action'].startswith('0.'):
            exit()
        
        else:
            print(f'{bcolors["FAIL"]}Invalid action{bcolors["ENDC"]}')

        self.showMenu()    


if __name__ == '__main__':
    shell = Shell()
    shell.start()





