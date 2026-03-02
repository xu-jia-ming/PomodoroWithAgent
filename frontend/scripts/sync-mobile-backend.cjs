const fs = require('fs')
const path = require('path')

const workspaceRoot = path.resolve(__dirname, '..', '..')
const backendRoot = path.resolve(workspaceRoot, 'backend')
const androidPythonRoot = path.resolve(__dirname, '..', 'android', 'app', 'src', 'main', 'python')

function ensureDir(dirPath) {
    fs.mkdirSync(dirPath, { recursive: true })
}

function copyFile(src, dest) {
    ensureDir(path.dirname(dest))
    fs.copyFileSync(src, dest)
}

function copyPythonApp() {
    const sourceAppDir = path.resolve(backendRoot, 'app')
    const targetAppDir = path.resolve(androidPythonRoot, 'app')
    ensureDir(targetAppDir)

    for (const entry of fs.readdirSync(sourceAppDir, { withFileTypes: true })) {
        if (!entry.isFile() || !entry.name.endsWith('.py')) {
            continue
        }
        copyFile(path.resolve(sourceAppDir, entry.name), path.resolve(targetAppDir, entry.name))
    }
}

function syncMobileBackend() {
    ensureDir(androidPythonRoot)
    copyFile(path.resolve(backendRoot, 'main.py'), path.resolve(androidPythonRoot, 'main.py'))
    copyPythonApp()
    console.log(`[mobile-sync] Backend python files copied to ${androidPythonRoot}`)
}

syncMobileBackend()
