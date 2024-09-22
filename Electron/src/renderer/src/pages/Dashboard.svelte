<script>
  import { onMount } from 'svelte'
  import Chatroom from '../components/Chatroom.svelte'
  import PeerList from '../components/PeerList.svelte'
  import { chats, onlinePeersStore, selectedPeer, downloads, addToast } from '../store'
  import SharedFiles from '../components/SharedFiles.svelte'
  import Browse from '../components/Browse.svelte'
  import Downloads from '../components/Downloads.svelte'
  import {push, pop, replace} from 'svelte-spa-router'

  const backendAddress = JSON.parse(localStorage.getItem('backendAddress'))

  const peerDetails = JSON.parse(localStorage.getItem('peerDetails'))
  selectedPeer.set(peerDetails)

  let socket

  function websocketConnection() {
    // Initialize the WebSocket connection
    const websocketUrl = `${backendAddress.replace(/^http/, 'ws')}/ws`
    socket = new WebSocket(websocketUrl)

    socket.onopen = () => {
      console.log('WebSocket connection established')
    }

    // Handle incoming messages
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)

      //   console.log(data)

      if (data['type'] == 'chat') {
        const newChat = {
          peer_id: data['peer_id'],
          username: data['username'],
          msg: data['msg'],
          send_time: data['send_time']
        }

        chats.update((chats) => [...chats, newChat])
      } else if (data['type'] == 'peer_change') {
        if (data['change'] == 1) {
          const newPeer = {
            peer_id: data['peer_id'],
            username: data['username'],
            ip: data['ip'],
            file_server_port: data['file_server_port']
          }
          onlinePeersStore.update((peers) => [...peers, newPeer])
        } else if (data['change'] == -1) {
          if (data['peer_id'] == $selectedPeer['peer_id']) {
            selectedPeer.set(peerDetails)
          }
          onlinePeersStore.update((peers) =>
            peers.filter((peer) => peer['peer_id'] != data['peer_id'])
          )
        }
      } else if (data['type'] == 'dp') {
        const file_id = data['file_id']
        const downloaded_size = data['downloaded_size']

        downloads.update((downloads) => {
          return downloads.map((download) => {
            if (download['file_id'] == file_id) {
              return {
                ...download,
                downloaded_size: downloaded_size
              }
            } else {
              return download
            }
          })
        })
      }

      // Download Complete
      else if (data['type'] == 'dc') {
        const file_id = data['file_id']

        downloads.update((downloads) => {
          return downloads.map((download) => {
            if (download['file_id'] == file_id) {
              return {
                ...download,
                completed: 1
              }
            } else {
              return download
            }
          })
        })
      } else if (data['type'] == 'de') {
        const file_id = data['file_id']
        const error = data['reason']

        downloads.update((downloads) => {
          return downloads.map((download) => {
            if (download['file_id'] == file_id) {
              return {
                ...download,
                completed: -1,
                error: error
              }
            } else {
              return download
            }
          })
        })
      }
    }

    // Handle WebSocket connection close
    socket.onclose = async () => {
      console.log('WebSocket connection closed')
      sessionStorage.setItem('toastMessage', JSON.stringify({
        message: 'Disconnected From Server',
        type: 'error',
        timeout: 3000
      }));
      await window.electron.ipcRenderer.invoke('kill-backend')
      replace("/")
    }

    // Handle WebSocket errors
    socket.onerror = async (error) => {
      console.error('WebSocket error:', error)
      await window.electron.ipcRenderer.invoke('kill-backend')
      replace("/")
    }

    // Clean up the WebSocket connection when the component is destroyed
    return () => {
      socket.close()
    }
  }

  onMount(() => {
    websocketConnection()
  })

  // Function to send a message
  function sendMessage(text) {
    const message = { type: 'message', text }
    socket.send(JSON.stringify(message))
  }
</script>


<div class="wrapper">
  <div class="left">
    <div class="peerlist"><PeerList {peerDetails} /></div>
    <div class="sharedFiles"><SharedFiles /></div>
  </div>
  <div class="middle">
    <div class="browse"><Browse /></div>
    <div class="downloads"><Downloads /></div>
  </div>
  <div class="right">
    <Chatroom {peerDetails} />
  </div>
</div>

<style>
  .wrapper {
    width: 100vw;
    height: 100vh;

    display: flex;

    /* border: 2px solid blue; */
  }

  .middle {
    width: 45%;
    border-left: 3px solid black;
    border-right: 3px solid black;

    display: flex;
    flex-direction: column;
  }

  .right {
    width: 25%;
    height: 100%;
  }

  .left {
    width: 30%;
    height: 100%;

    display: flex;
    flex-direction: column;

    /* min-width: 320px; */
    /* border: 2px solid green; */
  }

  .peerlist {
    height: 50%;
    /* border: 2px solid yellow; */
  }

  .sharedFiles {
    height: 50%;
    border-top: 3px solid black;
    /* border: 2px solid red; */
  }

  .browse {
    height: 60%;
  }

  .downloads {
    border-top: 3px solid black;
    height: 40%;
  }
</style>
