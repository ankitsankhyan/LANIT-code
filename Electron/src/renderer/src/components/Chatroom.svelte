<script>
    import { onMount, afterUpdate } from 'svelte';
    import axios from 'axios';
    import {chats} from '../store'
    import userPng from '../../icons/user.png'

    const backendAddress = JSON.parse(localStorage.getItem('backendAddress'))


    export let peerDetails;

    let chatroomLoading = 1;


    async function handleInput(e){
        if (e.key == "Enter") {
            let msg = e.target.value
            if (msg == "") return
            try {
                const response = await axios.post(`${backendAddress}/broadcast-msg`, {"msg" : msg});
                console.log(response.data);
            }
            catch (error) {
                console.log(error);
            }
            e.target.value = ""
        }
    }

    async function getChats() {
        try {
            const response = await axios.get(`${backendAddress}/chats`);
            chats.set(response.data)
            chatroomLoading = 0
        }
        catch (error) {
            console.log(error);
            chatroomLoading = -1
        }
    }

    let msgsArea;
    function scrollToBottom() {
        if (chatroomLoading == 0)
            msgsArea.scrollTop = msgsArea.scrollHeight;
    }

    onMount(function(){
        getChats()
        scrollToBottom()
    });

    afterUpdate(function(){
        scrollToBottom();
    });
</script>

{#if chatroomLoading == 1}
<div class="wrapper2">
    <div class="loading"></div>
</div>

{:else if chatroomLoading == -1}
<div class="wrapper2">
    Couldn't load chatroom...
</div>

{:else}
<div class="wrapper">
    <div class="msgsArea" bind:this={msgsArea}>
        {#each $chats as chat}
            <div class={chat["peer_id"] == peerDetails['peer_id'] ? "chat chat-end" : "chat chat-start"}>
                <div class="chat-image avatar">
                    <div class="w-10 rounded-full">
                        <img
                            alt="Tailwind CSS chat bubble component"
                            src="{userPng}"
                        />
                    </div>
                </div>
                <div class="chat-header">
                    {chat['username']}
                    <!-- <time class="text-xs opacity-50">{chat['send_time'].slice(11, 16)}</time> -->
                    <time class="text-xs opacity-50">{new Date(chat['send_time']).toLocaleTimeString()}</time>
                </div>
                <div class="chat-bubble">{chat['msg']}</div>
            </div>
        {/each}
    </div>

    <input on:keydown={handleInput} type="text" placeholder="Type here" class="input input-bordered input-primary w-full" />
</div>


{/if}

<style>
    .wrapper2{
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%;
    }

    .wrapper {
        height: 100%;

        display: flex;
        flex-direction: column;
        gap: 20px;
        justify-content: end;

        padding: 5px 10px;
        
        /* border: 2px solid red; */
    }

    .msgsArea {
        display: flex;
        flex-direction: column;
        gap: 10px;
        padding: 0 5px;

        /* border: 2px solid blue; */
 
        flex: 1;
        overflow-y: auto;
        scrollbar-width: none;
    }

    input {
        height: 50px;
    }
</style>
