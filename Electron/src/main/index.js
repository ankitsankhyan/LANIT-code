import { app, shell, BrowserWindow, ipcMain, dialog } from 'electron'
import path, { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import iconPng from '../../resources/icon.png?asset'
import { execFile } from 'child_process'
import treeKill from 'tree-kill'
import net from 'net'
import axios from 'axios'

async function createWindow() {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 1200, // Minimum width
    height: 850, // Minimum height
    // minWidth: 1200, // Minimum width
    // minHeight: 850, // Minimum height
    icon: iconPng,
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      nodeIntegration: true,
      contextIsolation: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // HMR for renderer base on electron-vite cli.
  // Load the remote URL for development or the local html file for production.
    if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
      mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
    } else {
      mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
    }
}

ipcMain.handle('select-files', async (event) => {
  const result = await dialog.showOpenDialog({ properties: ['openFile', 'multiSelections'] })
  return result.filePaths
})

ipcMain.handle('select-dir', async (event) => {
  const result = await dialog.showOpenDialog({ properties: ['openDirectory'] })
  return result.filePaths
})

// function to generate random usable port
function getFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.unref()
    server.listen(0, () => {
      const port = server.address().port
      server.close(() => {
        resolve(port)
      })
    })
    server.on('error', (err) => {
      reject(err)
    })
  })
}

let fastAPIProcess = null
function startFastAPIServer(port) {
  fastAPIProcess = execFile(
    path.join(__dirname, `../../resources/main.exe`),
    ['--port', port.toString()],
    (err, stdout, stderr) => {
      if (err) {
        console.error(`Error starting FastAPI: ${stderr}`)
      }
      if (stdout) {
        console.log(`stdout: ${stdout}`)
      }
    }
  )
}

function killFastAPIProcess() {
  if (fastAPIProcess) {
    treeKill(fastAPIProcess.pid, 'SIGKILL', (err) => {
      if (err) {
        console.error('Failed to force kill FastAPI process:', err)
      } else {
        console.log('FastAPI process force killed')
      }
    })
  }
  fastAPIProcess = null
}

function waitForServer(port) {
  const url = `http://127.0.0.1:${port}/`
  return new Promise((resolve, reject) => {
    const interval = setInterval(async () => {
      try {
        await axios.get(url)
        clearInterval(interval)
        resolve()
      } catch (error) {
        console.log('Waiting for FastAPI server...')
      }
    }, 1000) // Check every 500 milliseconds
  })
}

ipcMain.handle('start-backend', async (event) => {
  if (fastAPIProcess) {
    killFastAPIProcess()
  }
  const port = await getFreePort()
  // const port = 8000;
  startFastAPIServer(port)
  await waitForServer(port)
  return port
})

ipcMain.handle('kill-backend', async (event) => {
  killFastAPIProcess()
  return true
})

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  electronApp.setAppUserModelId('com.electron')

  // Default open or close DevTools by F12 in development
  // and ignore CommandOrControl + R in production.
  // see https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // IPC test
  ipcMain.on('ping', () => console.log('pong'))

  createWindow()

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', async () => {
  if (fastAPIProcess) {
    treeKill(fastAPIProcess.pid, 'SIGKILL', (err) => {
      if (err) {
        console.error('Failed to force kill FastAPI process:', err)
      } else {
        console.log('FastAPI process force killed')
        fastAPIProcess = null
      }
    })
  }
  // wait for 5 sec
  await new Promise((resolve) => setTimeout(resolve, 5000))


  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('quit', () => {
  if (fastAPIProcess) {
    treeKill(fastAPIProcess.pid, 'SIGKILL', (err) => {
      if (err) {
        console.error('Failed to force kill FastAPI process:', err)
      } else {
        console.log('FastAPI process force killed')
        fastAPIProcess = null
      }
    })
  }
})

app.on('before-quit', () => {
  if (fastAPIProcess) {
    treeKill(fastAPIProcess.pid, 'SIGKILL', (err) => {
      if (err) {
        console.error('Failed to force kill FastAPI process:', err)
      } else {
        console.log('FastAPI process force killed')
        fastAPIProcess = null
      }
    })
  }
})

// In this file you can include the rest of your app"s specific main process
// code. You can also put them in separate files and require them here.
