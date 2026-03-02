const { spawnSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const releaseDir = path.resolve(__dirname, '../release-build')
const winUnpackedDir = path.join(releaseDir, 'win-unpacked')
const builderConfigFile = path.join(releaseDir, 'builder-effective-config.yaml')

function sleep(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms)
}

function tryTaskKill(imageName) {
  const result = spawnSync('taskkill', ['/F', '/IM', imageName], {
    stdio: 'ignore',
    shell: false
  })
  return result.status === 0
}

function removeWithRetry(targetPath, retries = 8) {
  for (let index = 0; index <= retries; index += 1) {
    try {
      if (fs.existsSync(targetPath)) {
        fs.rmSync(targetPath, { recursive: true, force: true })
      }
      return true
    } catch (error) {
      if (index === retries) {
        throw error
      }
      sleep(250 * (index + 1))
    }
  }
  return false
}

try {
  // Kill stale desktop app processes that might lock ffmpeg.dll in win-unpacked.
  tryTaskKill('PomodoroTable.exe')
  tryTaskKill('electron.exe')

  try {
    removeWithRetry(winUnpackedDir)
  } catch (error) {
    console.warn(`[prepare-desktop-build] skip locked path: ${winUnpackedDir} (${error.message})`)
  }

  try {
    removeWithRetry(builderConfigFile)
  } catch (error) {
    console.warn(`[prepare-desktop-build] skip locked file: ${builderConfigFile} (${error.message})`)
  }

  console.log('[prepare-desktop-build] cleaned previous release artifacts')
} catch (error) {
  console.error('[prepare-desktop-build] failed to clean release folder lock.')
  console.error(String(error.message || error))
  process.exit(1)
}
