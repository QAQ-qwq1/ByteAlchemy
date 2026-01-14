
const { app, BrowserWindow } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

let mainWindow
let backendProcess

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        backgroundColor: '#1C191F', // Deep purple background to match SiUI
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        },
    })

    // Load the app
    // For this refactor, we prioritize loading from the built dist folder
    // to ensure the user gets the native GUI experience immediately.
    const indexPath = path.join(__dirname, '../dist/index.html')

    if (isDev && process.env.VITE_DEV_SERVER_URL) {
        mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL)
        mainWindow.webContents.openDevTools()
    } else {
        mainWindow.loadFile(indexPath).catch(() => {
            console.error('Failed to load index.html. Have you run npm run build?')
        })
    }
}

const PY_HOST = '127.0.0.1'
const PY_PORT = 3333

function startBackend() {
    console.log('Starting Python backend...')

    const scriptPath = path.join(__dirname, '../backend/server.py')
    let pythonPath = 'python3' // Default fallback

    if (isDev) {
        pythonPath = path.join(__dirname, '../.venv/bin/python')
    } else {
        // In packaged app, we might expect the user to have python3 or python
        // Or we could have bundled it, but for now we rely on system python
        pythonPath = 'python3'
    }

    console.log(`Using python path: ${pythonPath}`)

    backendProcess = spawn(pythonPath, [scriptPath])

    backendProcess.on('error', (err) => {
        if (err.code === 'ENOENT' && pythonPath === 'python3') {
            console.log('python3 not found, trying python...')
            pythonPath = 'python'
            backendProcess = spawn(pythonPath, [scriptPath])
        } else {
            console.error('Failed to start backend process:', err)
        }
    })

    backendProcess.stdout.on('data', (data) => {
        console.log(`python: ${data}`)
    })

    backendProcess.stderr.on('data', (data) => {
        console.error(`python error: ${data}`)
    })

    backendProcess.on('close', (code) => {
        console.log(`python process exited with code ${code}`)
    })
}

app.whenReady().then(() => {
    startBackend()
    createWindow()

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow()
    })
})

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit()
})


app.on('before-quit', () => {
    if (backendProcess) {
        backendProcess.kill()
    }
})
