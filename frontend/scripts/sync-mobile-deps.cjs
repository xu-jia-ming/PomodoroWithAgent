const { spawnSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const frontendRoot = path.resolve(__dirname, '..')
const requirementsPath = path.resolve(frontendRoot, 'requirements-mobile.txt')
const vendorPath = path.resolve(frontendRoot, 'android', 'app', 'src', 'main', 'python', 'vendor')

function ensureDir(dirPath) {
    fs.mkdirSync(dirPath, { recursive: true })
}

function runPipInstall() {
    ensureDir(vendorPath)

    const pipArgs = [
        '-m',
        'pip',
        'install',
        '-r',
        requirementsPath,
        '--upgrade',
        '--target',
        vendorPath,
        '--no-binary',
        'pydantic'
    ]

    const result = spawnSync('python', pipArgs, {
        cwd: frontendRoot,
        stdio: 'inherit',
        shell: process.platform === 'win32'
    })

    if (result.status !== 0) {
        throw new Error('sync-mobile-deps failed: pip install returned non-zero exit code')
    }

    console.log(`[mobile-sync] Python deps installed to ${vendorPath}`)
}

runPipInstall()
