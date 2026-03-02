import axios from 'axios'
import { ElMessage } from 'element-plus'

const envBase = import.meta.env.VITE_API_BASE_URL
const desktopBase = typeof window !== 'undefined' ? window?.desktop?.apiBaseURL : null
const localBase = typeof localStorage !== 'undefined' ? localStorage.getItem('api-base-url') : null
const resolvedBaseURL = (localBase || envBase || desktopBase || 'http://127.0.0.1:8000').replace(/\/+$/, '')
const isLocalEmbeddedBackend = /^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i.test(resolvedBaseURL)

const http = axios.create({
    baseURL: resolvedBaseURL,
    timeout: 10000
})

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

let lastNetworkErrorAt = 0

http.interceptors.response.use(
    (response) => response,
    async (error) => {
        const now = Date.now()
        const detail = error?.response?.data?.detail
        const config = error?.config || {}

        if (!error.response && isLocalEmbeddedBackend) {
            config.__retryCount = config.__retryCount || 0
            if (config.__retryCount < 6) {
                config.__retryCount += 1
                await delay(500)
                return http.request(config)
            }
        }

        if (!error.response && now - lastNetworkErrorAt > 2500) {
            lastNetworkErrorAt = now
            if (isLocalEmbeddedBackend) {
                ElMessage.error(`后端仍在启动中（${resolvedBaseURL}），请稍后重试。`)
            } else {
                ElMessage.error(`无法连接后端 ${resolvedBaseURL}，请先启动 backend 服务。`)
            }
        } else if (error.response && detail) {
            ElMessage.error(typeof detail === 'string' ? detail : '请求失败，请稍后重试。')
        } else if (error.code === 'ECONNABORTED') {
            ElMessage.error('请求超时，请检查后端服务状态。')
        }

        return Promise.reject(error)
    }
)

export async function apiGet(url, config = {}) {
    const res = await http.get(url, config)
    return res.data
}

export async function apiPost(url, payload, config = {}) {
    const res = await http.post(url, payload, config)
    return res.data
}

export async function apiPatch(url, payload, config = {}) {
    const res = await http.patch(url, payload, config)
    return res.data
}

export async function apiPut(url, payload, config = {}) {
    const res = await http.put(url, payload, config)
    return res.data
}

export async function apiDelete(url, config = {}) {
    const res = await http.delete(url, config)
    return res.data
}
