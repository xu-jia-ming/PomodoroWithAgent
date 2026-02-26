const { spawnSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const backendDir = path.resolve(__dirname, '../../backend')
const distDir = path.join(backendDir, 'dist-desktop')
const exeName = process.platform === 'win32' ? 'pomodoro-backend.exe' : 'pomodoro-backend'
const exePath = path.join(distDir, exeName)
const pythonBin = process.env.PYTHON || 'python'

const pyInstallerArgs = [
  '-m',
  'PyInstaller',
  '--noconfirm',
  '--clean',
  '--onefile',
  '--name',
  'pomodoro-backend',
  '--distpath',
  'dist-desktop',
  '--workpath',
  'build-desktop',
  '--specpath',
  'build-desktop',
  '--collect-all',
  'fastapi',
  '--collect-all',
  'starlette',
  '--collect-all',
  'pydantic',
  '--collect-all',
  'uvicorn',
  'desktop_server.py'
]

function run(command, args, cwd) {
  const result = spawnSync(command, args, {
    cwd,
    stdio: 'inherit',
    shell: false
  })

  if (result.error) {
    throw result.error
  }
  if (result.status !== 0) {
    throw new Error(`command failed: ${command} ${args.join(' ')}`)
  }
}

try {
  if (!fs.existsSync(path.join(backendDir, 'desktop_server.py'))) {
    throw new Error('missing backend/desktop_server.py')
  }

  run(pythonBin, pyInstallerArgs, backendDir)

  if (!fs.existsSync(exePath)) {
    throw new Error(`backend executable not found at ${exePath}`)
  }

  console.log(`[build-backend] backend packaged: ${exePath}`)
} catch (error) {
  console.error('[build-backend] failed to package backend executable.')
  console.error('[build-backend] ensure backend env is active and install: pip install -r backend/requirements-desktop.txt')
  console.error(error.message)
  process.exit(1)
}
