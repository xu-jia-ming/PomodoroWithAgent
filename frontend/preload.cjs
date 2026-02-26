const { contextBridge } = require('electron')

const apiBaseURL =
  process.env.POMODORO_API_BASE_URL
  || `http://${process.env.POMODORO_BACKEND_HOST || '127.0.0.1'}:${process.env.POMODORO_BACKEND_PORT || '8000'}`

contextBridge.exposeInMainWorld('desktop', {
  platform: process.platform,
  apiBaseURL
})
