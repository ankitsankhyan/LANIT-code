<script>
  import Router from 'svelte-spa-router'
  import Home from './pages/Home.svelte'
  import Dashboard from './pages/Dashboard.svelte'
  import Toasts from './components/Toasts.svelte'
  import Server from './pages/Server.svelte'
  
  const routes = {
    '/': Home,
    '/dashboard': Dashboard,
    '/server': Server,
  }

</script>

<Toasts />
<Router {routes}/>
