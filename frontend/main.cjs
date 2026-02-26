const { app, BrowserWindow, dialog } = require('electron')
const { spawn } = require('child_process')
const fs = require('fs')
const http = require('http')
const path = require('path')

const BACKEND_HOST = process.env.POMODORO_BACKEND_HOST || '127.0.0.1'
const BACKEND_PORT = Number(process.env.POMODORO_BACKEND_PORT || 8000)
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`

let backendProcess = null
let ownsBackendProcess = false

function checkBackendHealth(timeoutMs = 1200) {
  return new Promise((resolve, reject) => {
    const req = http.get(`${BACKEND_URL}/`, (res) => {
      res.resume()
      if (res.statusCode && res.statusCode < 500) {
        resolve()
        return
      }
      reject(new Error(`backend unhealthy status=${res.statusCode}`))
    })
    req.on('error', reject)
    req.setTimeout(timeoutMs, () => req.destroy(new Error('backend healthcheck timeout')))
  })
}

async function waitForBackendReady(timeoutMs = 20000) {
  const startedAt = Date.now()
  let lastError = null
  while (Date.now() - startedAt < timeoutMs) {
    try {
      await checkBackendHealth()
      return
    } catch (error) {
      lastError = error
      await new Promise((resolve) => setTimeout(resolve, 450))
    }
  }
  throw lastError || new Error('backend startup timed out')
}

function getBackendExecutablePath() {
  const candidates = [
    path.join(process.resourcesPath, 'backend', 'pomodoro-backend.exe'),
    path.join(__dirname, '..', 'backend', 'dist-desktop', 'pomodoro-backend.exe'),
    path.join(__dirname, 'backend', 'pomodoro-backend.exe')
  ]
  return candidates.find((candidate) => fs.existsSync(candidate)) || null
}

async function ensureBackendReady() {
  if (!app.isPackaged) {
    return
  }

  try {
    await checkBackendHealth()
    return
  } catch {
  }

  const backendExecutable = getBackendExecutablePath()
  if (!backendExecutable) {
    throw new Error('未找到后端可执行文件，请重新执行 npm run desktop:build。')
  }

  const dbPath = path.join(app.getPath('userData'), 'backend-data', 'pomodoro.db')
  fs.mkdirSync(path.dirname(dbPath), { recursive: true })

  backendProcess = spawn(backendExecutable, [], {
    cwd: path.dirname(backendExecutable),
    windowsHide: true,
    stdio: 'ignore',
    env: {
      ...process.env,
      POMODORO_HOST: BACKEND_HOST,
      POMODORO_PORT: String(BACKEND_PORT),
      POMODORO_DB_PATH: dbPath
    }
  })
  ownsBackendProcess = true

  backendProcess.once('exit', () => {
    backendProcess = null
  })

  await waitForBackendReady()
}

function stopManagedBackend() {
  if (!ownsBackendProcess || !backendProcess || backendProcess.killed) {
    return
  }
  backendProcess.kill()
}

async function createWindow() {
  const window = new BrowserWindow({
    width: 1280,
    height: 840,
    minWidth: 1000,
    minHeight: 700,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false
    }
  })

  if (!app.isPackaged) {
    window.loadURL('http://127.0.0.1:5173')
    return
  }

  try {
    await ensureBackendReady()
  } catch (error) {
    dialog.showErrorBox('后端启动失败', String(error.message || error))
    return
  }

  const rendererEntryCandidates = [
    path.join(process.resourcesPath, 'app-dist', 'index.html'),
    path.join(__dirname, 'app-dist', 'index.html'),
    path.join(__dirname, 'dist', 'index.html')
  ]
  const rendererEntry = rendererEntryCandidates.find((candidate) => fs.existsSync(candidate))

  if (!rendererEntry) {
    dialog.showErrorBox(
      '应用资源缺失',
      `未找到渲染入口文件：\n${rendererEntryCandidates.join('\n')}\n\n请重新执行 npm run desktop:build 后安装新版本。`
    )
    return
  }

  window.webContents.on('did-fail-load', (_event, code, description, url) => {
    dialog.showErrorBox(
      '页面加载失败',
      `code=${code}\nmessage=${description}\nurl=${url}`
    )
  })

  window.loadFile(rendererEntry)
}

app.whenReady().then(() => {
  void createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      void createWindow()
    }
  })
})

app.on('before-quit', () => {
  stopManagedBackend()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    stopManagedBackend()
    app.quit()
  }
})
