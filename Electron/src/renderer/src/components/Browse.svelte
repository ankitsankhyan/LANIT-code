<script>
  import { onMount } from 'svelte'
  import { selectedPeer, sharedFilesStore , downloads , downloadDirStore } from '../store'
  import axios from 'axios'
  import {addToast} from '../store'

  const backendAddress = JSON.parse(localStorage.getItem('backendAddress'))
  const peerDetails = JSON.parse(localStorage.getItem('peerDetails'))

  let sharedFiles = []
  let loadingFiles = 0
  
  async function getSharedFiles() {
    if ($selectedPeer == null || $selectedPeer == undefined){
      sharedFiles = []
    }

    else if ($selectedPeer['peer_id'] == peerDetails['peer_id']){
      sharedFiles = $sharedFilesStore
    }

    else
    {
      try {
        const response = await axios.get(`${backendAddress}/shared-files/${$selectedPeer['peer_id']}`)
        sharedFiles= response.data
      } catch (error) {
        console.log(error)
      }
    }
  }

  function formatSize(bytes) {
    const units = ['bytes', 'KB', 'MB', 'GB', 'TB']
    let index = 0

    while (bytes >= 1024 && index < units.length - 1) {
      bytes /= 1024
      index++
    }

    return `${bytes.toFixed(2)} ${units[index]}`
  }

  async function handleDownloadButton(e) {
    if ($downloadDirStore == null){
        addToast({
            message: 'Please set your download directory',
            type: 'error',
            timeout : 3000
        })
        return
    }

    const file_id = e.currentTarget.getAttribute('data-fileid')
    const peer_id = e.currentTarget.getAttribute('data-peerid')

    const file = sharedFiles.find((file) => file['file_id'] == file_id)
    console.log(file)
    if (!file) {
      console.log(`File ${file['file_name']} not found`)
      addToast({
        message: `File ${file['file_name']} not found`,
        type: 'error',
        timeout : 3000
    })
      return
    }

    for (let download of $downloads) {
      if (download['file_id'] == file_id) {
        if (download['completed'] == '1') {
          console.log(`Already downloaded ${file['file_name']}`)
          addToast({
            message: `File ${file['file_name']} is already downloaded`,
            type: 'error',
            timeout : 3000
          })
          return
        }

        else if (download['completed'] == '0') {
          console.log(`Already downloading ${file_id}`)
          addToast({
            message: `File ${file['file_name']} is already downloading`,
            type: 'error',
            timeout : 3000
          })
          return
        }

        else {
          downloads.update((downloads) => downloads.filter((download) => download['file_id'] != file_id))
        }
      }
    }

    try {
      const resp = await axios.post(`${backendAddress}/download-file`, { 'file_id' : file_id, 'peer_id' : peer_id })
      if (resp.data['success'] == '1') {
        downloads.update((downloads) => [{
          'file_id' : file_id,
          'file_name' : file['file_name'],
          'downloaded_size' : 0,
          'file_size' : file['file_size'],
          'file_hash' : file['file_hash'],
          'completed' : 0
        } , ...downloads])
      }

      else if (resp.data['success'] == '0') {
        addToast({
          message: `Error : ${resp.data['error']}`,
          type: 'error',
          timeout : 3000
        })
      }
    } catch (error) {
        addToast({
            message: `Error : ${error}`,
            type: 'error',
            timeout : 3000
        })
      console.log(error)
    }
  }

  onMount(async function () {
    loadingFiles = 1
    await getSharedFiles()
    loadingFiles = 0
  })

  $: {
    if ($selectedPeer) {
      getSharedFiles();
   }
  }
</script>

<div class="wrapper">
    <div class="heading">
        <h1>Browse Files Shared By Others</h1>
        <div class="tooltip tooltip-bottom" data-tip="Refresh shared files">
            <button on:click={getSharedFiles} class="btn btn-primary">Refresh</button>
        </div>
    </div>
  

  {#if loadingFiles == 1}
    <div class="loadingWrapper">
      <div class="loading"></div>
    </div>

  {:else if loadingFiles == 0}
  <div class="files">
    <table class="table">
      <thead>
        <tr>
          <th>File Name</th>
          <th>File Size</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {#each sharedFiles as file (file['file_id'])}
          <tr>
            <td>
              <div class="tooltip" data-tip={file['file_name']}>
                {file['file_name'].length > 75
                  ? file['file_name'].substring(0, 72) + '...'
                  : file['file_name']}
              </div>
            </td>
            <td>{formatSize(Number(file['file_size']))}</td>
            <td class="deltd">
              {#if $selectedPeer['peer_id'] == peerDetails['peer_id']}
              <button class="btn" data-fileid={file['file_id']} disabled>Download</button>
              {:else}
              <button on:click={handleDownloadButton} class="btn" 
              data-peerid={$selectedPeer['peer_id']} 
              data-fileid={file['file_id']}
              >Download</button>
              {/if}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
  {/if}
</div>

<style>
  .wrapper {
    /* border: 2px solid red; */

    width: 100%;
    height: 100%;

    padding: 20px;

    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .heading {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .heading button {
    height: 45px;
    min-height: 0;
  }

  h1 {
    font-size: 20px;
    color: oklch(var(--p));
  }

  .loadingWrapper {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
  }

  .files {
    flex: 1;

    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: oklch(var(--p)) transparent;
  }
</style>
