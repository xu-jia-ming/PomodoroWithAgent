import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from './http'

export const fetchTodos = () => apiGet('/api/todos')
export const createTodo = (payload) => apiPost('/api/todos', payload)
export const toggleTodo = (todoId) => apiPatch(`/api/todos/${todoId}/toggle`, {})
export const updateTodo = (todoId, payload) => apiPut(`/api/todos/${todoId}`, payload)
export const deleteTodo = (todoId) => apiDelete(`/api/todos/${todoId}`)

export const fetchCollections = () => apiGet('/api/collections')
export const createCollection = (payload) => apiPost('/api/collections', payload)
export const updateCollection = (collectionId, payload) => apiPut(`/api/collections/${collectionId}`, payload)
export const deleteCollection = (collectionId) => apiDelete(`/api/collections/${collectionId}`)

export const fetchFocusStatus = () => apiGet('/api/focus/status')
export const startFocus = (payload) => apiPost('/api/focus/start', payload)
export const stopFocus = () => apiPost('/api/focus/stop', {})

export const fetchStats = (days = null) => {
    if (days === null) {
        return apiGet('/api/stats')
    }
    return apiGet(`/api/stats?days=${days}`)
}
export const recordPomodoro = (payload) => apiPost('/api/stats/record', payload)
export const recordInterrupt = (payload) => apiPost('/api/stats/interrupt', payload)
export const fetchMe = () => apiGet('/api/me')

export const fetchAiConfig = () => apiGet('/api/ai/config')
export const updateAiConfig = (payload) => apiPut('/api/ai/config', payload)
export const generateAiAdvice = (payload) => apiPost('/api/ai/advice', payload, { timeout: 90000 })
