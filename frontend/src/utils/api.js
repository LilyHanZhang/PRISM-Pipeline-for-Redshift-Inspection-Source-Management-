import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

export const getSources = () => api.get('/sources/')
export const getSource = (id) => api.get(`/sources/${id}`)
export const searchSources = (q, tag) => api.get('/sources/search', { params: { q, tag } })
export const sourcesNear = (ra, dec, r) => api.get('/sources/near', { params: { ra, dec, r } })

export const get1DSpectrum = (id, filter, orient) => api.get(`/spectra/${id}/1d/${filter}/${orient}`)
export const get2DSpectrumUrl = (id, filter, orient, cmap = 'viridis', scale = 'zscale') =>
  `/api/spectra/${id}/2d/${filter}/${orient}?cmap=${cmap}&scale=${scale}`

export const getCutoutUrl = (id, band, size = 5, cmap = 'viridis', scale = 'zscale') =>
  `/api/images/cutout/${id}/${band}?size=${size}&cmap=${cmap}&scale=${scale}`
export const getRGBUrl = (id, size = 5) => `/api/images/rgb/${id}?size=${size}`
export const getBands = () => api.get('/images/bands')

export const getPdfUrl = (id, filter, orient) => `/api/pdf/${id}/${filter}/${orient}`

export const getTagList = () => api.get('/tags/list')
export const getSourceTags = (id) => api.get(`/tags/source/${id}`)
export const addTag = (id, tag) => api.post(`/tags/${id}/add`, { tag })
export const removeTag = (id, tag) => api.delete(`/tags/${id}/remove`, { data: { tag } })

export const updateZSpec = (id, zSpec) => api.patch(`/redshift/${id}`, { z_spec: zSpec })

export default api
