<script>
  import axios from 'axios'
  import { downloads , downloadDirStore} from '../store'

  const backendAddress = JSON.parse(localStorage.getItem('backendAddress'))

  async function setDownloadDir() {
      const dir = await window.electron.ipcRenderer.invoke('select-dir');
      const dir2 = dir[0].replace(/\\/g , '/')

      if (dir.length == 0) {
          return
      }
      
      try {
        const resp = await axios.post(`${backendAddress}/download-dir`, {dir_path: dir2})
        if (resp.data['success'] == '1'){
            downloadDirStore.set(dir)
        }
        else {
            console.log(resp.data)
        }
      }
      catch (error) {
          console.log(error)
      }
  }

  function clearDownloads(){
    downloads.update((downloads) => downloads.filter((download) => download['completed'] != -1 && download['completed'] != 1))
  }

  function formatSize(bytes) {
        const units = ['bytes', 'KB', 'MB', 'GB', 'TB'];
        let index = 0;

        while (bytes >= 1024 && index < units.length - 1) {
            bytes /= 1024;
            index++;
        }

        return `${bytes.toFixed(2)} ${units[index]}`;
  }
</script>

<div class="wrapper">
  <h1>Downloads ({$downloads.length})</h1>
  <div class="downloadArea">
    {#each $downloads as download (download['file_id'])}
      <div class="download">
        <div class="details">
          <p class="name">{download['file_name']}</p>
          <p>({formatSize(download['downloaded_size'])}/{formatSize(download['file_size'])})</p>
          {#if download['completed'] == -1}
          <p>[Error : {download['error']}]</p>
          {/if}
        </div>
        {#if download['completed'] == 1}
        <progress class="progress progress-success" value="100" max="100"></progress>
        {:else if download['completed'] == -1}
        <progress class="progress progress-error" value="{download['downloaded_size']}" max="{download['file_size']}"></progress>
        {:else}
        <progress class="progress progress-primary" value="{download['downloaded_size']}" max="{download['file_size']}"></progress>
        {/if}
      </div>
    {/each}
  </div>
  <div class="downloadDir">
    <p>Download Directory :</p>
    <span>{$downloadDirStore==null ? 'Not set' : $downloadDirStore}</span>
    <div class="tooltip" data-tip="Set download directory">
        <button on:click={setDownloadDir} class="btn btn-primary">Set</button>
    </div>
    <div class="tooltip" data-tip="Clear all downloaded and failed files">
        <button on:click={clearDownloads} class="btn btn-primary">Clear</button>
    </div>
  </div>
</div>

<style>
  .wrapper {
    /* border: 2px solid red; */
    width: 100%;
    height: 100%;

    padding: 20px;

    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  h1 {
    font-size: 20px;
    color: oklch(var(--p));
  }

  .downloadArea {
    flex: 1;

    /* border: 1px solid black; */

    display: flex;
    flex-direction: column;
    overflow: auto;
    gap: 25px;
  }

  .download {
    /* border: 2px solid yellow; */

    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .download .details {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .download .details .name {
    flex: 1;

    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .download .progress {
    width: 100%;
  }

  .downloadDir {
    display: flex;
    align-items: center;
    gap: 10px;

    font-size: 16px;
  }

  .downloadDir span {
    flex: 1;

    overflow-x: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }


</style>
