import axios from 'axios'
import { ElMessage } from 'element-plus'

const envBase = import.meta.env.VITE_API_BASE_URL
const desktopBase = typeof window !== 'undefined' ? window?.desktop?.apiBaseURL : null
const localBase = typeof localStorage !== 'undefined' ? localStorage.getItem('api-base-url') : null
const resolvedBaseURL = (localBase || envBase || desktopBase || 'http://127.0.0.1:8000').replace(/\/+$/, '')

const http = axios.create({
    baseURL: resolvedBaseURL,
    timeout: 10000
})

let lastNetworkErrorAt = 0

http.interceptors.response.use(
    (response) => response,
    (error) => {
        const now = Date.now()
        const detail = error?.response?.data?.detail

        if (!error.response && now - lastNetworkErrorAt > 2500) {
            lastNetworkErrorAt = now
            ElMessage.error(`无法连接后端 ${resolvedBaseURL}，请先启动 backend 服务。`)
        } else if (error.response && detail) {
            ElMessage.error(typeof detail === 'string' ? detail : '请求失败，请稍后重试。')
        } else if (error.code === 'ECONNABORTED') {
            ElMessage.error('请求超时，请检查后端服务状态。')
        }

        return Promise.reject(error)
    }
)

export async function apiGet(url) {
    const res = await http.get(url)
    return res.data
}

export async function apiPost(url, payload) {
    const res = await http.post(url, payload)
    return res.data
}

export async function apiPatch(url, payload) {
    const res = await http.patch(url, payload)
    return res.data
}

export async function apiPut(url, payload) {
    const res = await http.put(url, payload)
    return res.data
}

export async function apiDelete(url) {
    const res = await http.delete(url)
    return res.data
}
