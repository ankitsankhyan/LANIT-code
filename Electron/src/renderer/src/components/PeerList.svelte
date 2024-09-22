
<script>
    import { onMount } from 'svelte'
    import axios from 'axios'
    export let peerDetails;
    import {onlinePeersStore, selectedPeer} from '../store';

    const backendAddress = JSON.parse(localStorage.getItem('backendAddress'))
    

    let onlinePeersLoading = 1;

    async function getOnlinePeers() {
        try {
            const response = await axios.get(`${backendAddress}/peers/list`);
            onlinePeersStore.set(response.data)
            onlinePeersLoading = 0
        }
        catch (error) {
            console.log(error);
            onlinePeersLoading = -1
        }
    }

    onMount(function(){
        getOnlinePeers()
    });

</script>

<div class="wrapper">
    <h1>Online Peers ({$onlinePeersStore.length})</h1>
    {#if onlinePeersLoading == 1}
        <div class="loadingWrapper">
            <div class="loading"></div>
        </div>
    
    {:else if onlinePeersLoading == -1}
    <div class="loadingWrapper">
        Couldn't load online peers...
    </div>

    {:else }
        <table class="table">
            <tbody>
                {#each $onlinePeersStore as peer (peer['peer_id'])}
                    <tr on:click={() => selectedPeer.set(peer)} class="hover cursor-pointer {peer['peer_id'] == $selectedPeer['peer_id'] ? 'active' : ''}">
                        <td>
                            <div class="avatar {peer['peer_id'] == peerDetails['peer_id'] ? 'online' : ''} placeholder">
                                <div class="bg-neutral text-neutral-content rounded-full w-8">
                                    <span class="text-1xl">{peer['username'][0].toUpperCase()}</span>
                                </div>
                            </div>
                        </td>
                        <td>
                            <div class="username">{peer['username']}</div>
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
          <!-- {#each onlinePeers as peer}
            <div class="peer">
                <div class="avatar {peer['peer_id'] == peerDetails['peer_id'] ? 'online' : ''} placeholder">
                    <div class="bg-neutral text-neutral-content rounded-full w-8">
                        <span class="text-1xl">{peer['username'][0].toUpperCase()}</span>
                    </div>
                </div>
                <div class="username">{peer['username']}</div>
            </div>
        {/each} -->
    {/if}

</div>

<style>
    .wrapper{
        height: 100%;
        width: 100%;
        /* border: 2px solid red; */

        padding: 20px;

        display: flex;
        flex-direction: column;

        gap: 20px;
    }

    .loadingWrapper{
        height: 100%;
        width: 100%;

        display: flex;
        justify-content: center;
        align-items: center;
    }

    h1{
        font-size: 20px;
        color: oklch(var(--p));
    }

    table{
        /* border: 1px solid yellow; */
        display: flex;
        flex-direction: column;

        overflow-y: auto;
        scrollbar-width: thin;
        scrollbar-color: oklch(var(--p)) transparent;
    }

    tr{
        display: flex;
        justify-content: start;
        align-items: center;
        gap: 10px;

    }
</style>