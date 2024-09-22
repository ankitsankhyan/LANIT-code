<script>
  import axios from 'axios'
  import {push, pop, replace} from 'svelte-spa-router'
  import Toasts from '../components/Toasts.svelte'
  import { addToast } from '../store'
  import { onMount } from 'svelte'

  let host = ''
  let port = null
  let username = ''

  let connecting = 0
  let startingServer = 0
  

  async function handleStartServer() {
    startingServer = 1
    const fastAPIPort = await window.electron.ipcRenderer.invoke('start-backend')
    const backendAddress = `http://127.0.0.1:${fastAPIPort}`
    localStorage.setItem('backendAddress' , JSON.stringify(backendAddress))
    try {
      const response = await axios.get(`${backendAddress}/start-server`)
      if (response.data['success'] == '1'){
          localStorage.setItem('serverDetails', JSON.stringify({
            host : response.data['host'], 
            port : response.data['port']
          }))
          replace("/server")
          return
      }
      else {
        console.log(response.data)
        addToast({
          message: response.data['error'],
          type: 'error',
          timeout : 3000
        })
      }
    } catch (error) {
      console.log(error)
      addToast({
        message: error.message,
        type: 'error',
        timeout : 3000
      })
    }
    await window.electron.ipcRenderer.invoke('kill-backend')
    startingServer = 0
  }

  function validate(){
    if (host == '' || port == '' || username == '') {
      addToast({
        message: 'All fields are required',
        type: 'error',
        timeout : 3000
      })
      return 0
    }

    if (port < 1024 || port > 65535) {
      addToast({
        message: 'Port must be between 1024 and 65535',
        type: 'error',
        timeout : 3000
      })
      return 0
    }

    if (username.length < 3) {
      addToast({
        message: 'Username must be at least 3 characters long',
        type: 'error',
        timeout : 3000
      })
      return 0
    }

    if (username.length > 10) {
      addToast({
        message: 'Username must be at most 10 characters long',
        type: 'error',
        timeout : 3000
      })
      return 0
    }

    if (!host.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/)) {
      addToast({
        message: 'Invalid IP address',
        type: 'error',
        timeout : 3000
      })
      return 0
    }

    return 1
  }

  async function handleConnect() {
    if (validate() == 0) {
      return
    }

    connecting = 1
    const fastAPIPort = await window.electron.ipcRenderer.invoke('start-backend')
    const backendAddress = `http://127.0.0.1:${fastAPIPort}`
    localStorage.setItem('backendAddress' , JSON.stringify(backendAddress))
    try {
      const response = await axios.post(`${backendAddress}/start-peer`, { host, port, username })
      if (response.data['success'] == '1'){
          localStorage.setItem('peerDetails', JSON.stringify(response.data))
        //   window.location.href = `/dashboard`
        //   navigate("/dashboard");
          replace("/dashboard")

          return
      }
      else {
        console.log(response.data)
        addToast({
          message: response.data['error'],
          type: 'error',
          timeout : 3000
        })
      }
    } catch (error) {
      console.log(error)
      addToast({
        message: error.message,
        type: 'error',
        timeout : 3000
      })
    }
    await window.electron.ipcRenderer.invoke('kill-backend')
    connecting = 0
  }

  onMount(() => {
    const toastMessage = sessionStorage.getItem('toastMessage');
    if (toastMessage) {
      const { message, type, timeout } = JSON.parse(toastMessage);
      // Display the toast message
      addToast({ message, type, timeout });
      // Remove the toast message from sessionStorage
      sessionStorage.removeItem('toastMessage');
    }
  })
</script>

<div class="wrapper">
    <div class="wrapper2">
        <label class="input input-bordered input-primary flex items-center gap-4">
          Host
          <input bind:value={host} type="text" class="grow" placeholder="127.0.0.1" />
        </label>
      
        <label class="input input-bordered input-primary flex items-center gap-4">
          Port
          <input bind:value={port} type="number" class="grow" placeholder="12345" />
        </label>
      
        <label class="input input-bordered input-primary flex items-center gap-4">
          Username
          <input bind:value={username} type="text" class="grow" placeholder="hsr" />
        </label>
      
        {#if connecting == 1}
          <button class="btn btn-primary" disabled><div class="loading"></div></button>
        {:else}
          <button on:click={handleConnect} class="btn btn-primary">Connect</button>
        {/if}
    </div>
    <div class="divider divider-horizontal">OR</div> 
    {#if startingServer == 1}
        <button class="btn btn-primary" disabled><div class="loading"></div></button>
    {:else}
        <button on:click={handleStartServer} class="btn btn-primary">Host Server Instead</button>
    {/if}
</div>


  

<style>
    .wrapper{
        width: 100vw;
        height: 100vh;

        display: flex;
        justify-content: center;
        align-items: center;
        gap: 2rem;
    }

    .wrapper2 {

    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    gap: 2rem;

   }

  label {
    width: 300px;
    font-weight: 700;
  }

  label > input::placeholder {
    opacity: 0.4;
  }

  label > input {
    font-weight: 500;
  }

  button {
    font-weight: 600;
    width: 300px;
  }
</style>
