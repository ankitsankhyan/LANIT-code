
<script>
    import {push, pop, replace} from 'svelte-spa-router'
    const {host , port} = JSON.parse(localStorage.getItem('serverDetails'))

    async function stopServer() {
        await window.electron.ipcRenderer.invoke('kill-backend')
        replace("/")
    }
</script>


<div class="wrapper">
    <div class="wrapper2">
        <h1>Server is listening on : </h1>
        <label class="input input-bordered input-primary flex items-center gap-4">
            Host
            <input type="text" class="grow" value="{host}" readonly/>
          </label>
        
          <label class="input input-bordered input-primary flex items-center gap-4">
            Port
            <input type="number" class="grow" value="{port}" readonly/>
          </label>
        <button on:click={stopServer} class="btn btn-primary">Stop</button>
    </div>
</div>

<style>
    .wrapper {
        width: 100vw;
        height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    .wrapper2 {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
        gap: 2rem;
    }

    h1{
        font-size: 20px;
        color: oklch(var(--p));
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

    input{
        cursor: default;
    }
</style>