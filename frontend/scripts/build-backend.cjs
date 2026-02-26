const { spawnSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const backendDir = path.resolve(__dirname, '../../backend')
const distDir = path.join(backendDir, 'dist-desktop')
const exeName = process.platform === 'win32' ? 'pomodoro-backend.exe' : 'pomodoro-backend'
const exePath = path.join(distDir, exeName)
const explicitPython = process.env.PYTHON
const condaEnvName = process.env.POMODORO_CONDA_ENV || 'pomodoro-table'

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

function canUseConda() {
  const probe = spawnSync('conda', ['--version'], { stdio: 'ignore', shell: false })
  return probe.status === 0
}

function runPyInstaller(cwd) {
  if (explicitPython) {
    console.log(`[build-backend] using explicit python: ${explicitPython}`)
    run(explicitPython, pyInstallerArgs, cwd)
    return
  }

  if (canUseConda()) {
    try {
      console.log(`[build-backend] using conda env: ${condaEnvName}`)
      run('conda', ['run', '-n', condaEnvName, 'python', ...pyInstallerArgs], cwd)
      return
    } catch (error) {
      console.warn(`[build-backend] conda env build failed, fallback to system python (${error.message})`)
    }
  }

  console.log('[build-backend] using system python')
  run('python', pyInstallerArgs, cwd)
}

try {
  if (!fs.existsSync(path.join(backendDir, 'desktop_server.py'))) {
    throw new Error('missing backend/desktop_server.py')
  }

  runPyInstaller(backendDir)

  if (!fs.existsSync(exePath)) {
    throw new Error(`backend executable not found at ${exePath}`)
  }

  console.log(`[build-backend] backend packaged: ${exePath}`)
} catch (error) {
  console.error('[build-backend] failed to package backend executable.')
  console.error('[build-backend] install dependency with: conda run -n pomodoro-table pip install -r backend/requirements-desktop.txt')
  console.error('[build-backend] or set PYTHON to a ready interpreter.')
  console.error(error.message)
  process.exit(1)
}
