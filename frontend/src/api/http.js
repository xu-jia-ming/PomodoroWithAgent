import axios from 'axios'

const http = axios.create({
    baseURL: 'http://127.0.0.1:8000',
    timeout: 10000
})

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
