
<script>
  import axios from 'axios'
  import {sharedFilesStore} from '../store'
  import delsvg from '../../icons/del.svg'

  const backendAddress = JSON.parse(localStorage.getItem('backendAddress'))

//   import {sharedFilesData} from '../data'
//   let sharedFiles = sharedFilesData

    let adding = 0

    function formatSize(bytes) {
        const units = ['bytes', 'KB', 'MB', 'GB', 'TB'];
        let index = 0;

        while (bytes >= 1024 && index < units.length - 1) {
            bytes /= 1024;
            index++;
        }

        return `${bytes.toFixed(2)} ${units[index]}`;
    }

    async function handleDeleteButton(e){
        const file_id = e.currentTarget.getAttribute('data-fileid')
        e.currentTarget.classList.add('btn-disabled')
        try {
            const resp = await axios.post(`${backendAddress}/remove-file-from-share-list`, {file_id})
            sharedFilesStore.update((sharedFiles) => sharedFiles.filter((file) => file['file_id'] != file_id))
            return
        }
        catch (error) {
            console.log(error)
        }
        e.currentTarget.classList.remove('btn-disabled')
    }

    async function onAddClick() {
        const filePaths = await window.electron.ipcRenderer.invoke('select-files')
        if (filePaths.length == 0) {
            return
        }
        adding = 1
        for (let file of filePaths) {
            const temp = file.replace(/\\/g, '/')
            try{
                const resp = await axios.post(`${backendAddress}/add-file-to-share-list`, {file_path: temp})
                if (resp.data['success'] == '1'){
                    sharedFilesStore.update((sharedFiles) => [...sharedFiles, {
                        "file_id" : resp.data['file_id'],
                        "file_name" : resp.data['file_name'],
                        "file_path" : resp.data['file_path'],
                        "file_size" : resp.data['file_size'],
                        "file_hash" : resp.data['file_hash']
                    }])
                }
                else {
                    console.log(resp.data)
                }
            }
            catch (error) {
                console.log(error)
                continue
            }
        }
        adding = 0
    }

</script>


<div class="wrapper">
    <h1>Files Shared By You</h1>

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
                {#each $sharedFilesStore as file (file['file_id'])}
                    <tr>
                        <td>
                            <div class="tooltip" data-tip={file['file_name']}>
                                {file['file_name'].length > 10 ? file['file_name'].substring(0, 8) + '...' : file['file_name']}
                            </div>
                        </td>
                        <td>{formatSize(Number(file['file_size']))}</td>
                        <td class='deltd'><button on:click={handleDeleteButton} class="btn del" data-fileid={file['file_id']}><img src="{delsvg}" alt="Delete"></button></td>
                    </tr>
                {/each}
            </tbody>
          </table>
    </div>

    {#if adding == 0}
    <div class="tooltip tip" data-tip="Add files to your share list">
        <button on:click={onAddClick} class="btn btn-primary">Add</button>
    </div>
    {:else}
    <button class="btn btn-primary btn-disabled"><div class="loading"></div></button>
    {/if}
</div>

<style>
    .wrapper {

        width: 100%;
        height: 100%;

        padding: 20px;

        display: flex;
        flex-direction: column;
        gap: 20px;

        position: relative;
    }

    h1{
        font-size: 20px;
        color: oklch(var(--p));
    }

    .files {
        flex: 1;

        overflow: auto;

        scrollbar-width: none;
        scrollbar-color: oklch(var(--p)) transparent;
    }

    img{
        max-height: 100%;
        max-width: 20px;
    }

    tr > td > .del{
        padding: 1px;

        height: 100%;
        width: 40px;
    }

    td {
        padding-top: 0;
        padding-bottom: 10px;
    }


    .deltd{
        padding-right: 0;
    }

    .wrapper .tip button {
        width: 100%;
    }

</style>