$ErrorActionPreference = 'Stop'

$javaHome = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.10.7-hotspot'
$androidSdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'

if (-not (Test-Path $javaHome)) {
    throw "JDK 21 path not found: $javaHome"
}

if (-not (Test-Path $androidSdk)) {
    throw "Android SDK path not found: $androidSdk"
}

setx JAVA_HOME "$javaHome" | Out-Null
setx ANDROID_HOME "$androidSdk" | Out-Null
setx ANDROID_SDK_ROOT "$androidSdk" | Out-Null
setx HTTP_PROXY "http://127.0.0.1:7890" | Out-Null
setx HTTPS_PROXY "http://127.0.0.1:7890" | Out-Null
setx ALL_PROXY "socks5://127.0.0.1:7890" | Out-Null
setx GRADLE_OPTS "-Dhttp.proxyHost=127.0.0.1 -Dhttp.proxyPort=7890 -Dhttps.proxyHost=127.0.0.1 -Dhttps.proxyPort=7890" | Out-Null

Write-Host 'Mobile environment variables persisted for current user.'
Write-Host 'Please restart terminal/IDE to apply new environment variables.'
