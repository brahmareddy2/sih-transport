import api from './api'

export const getSeedStatus = async () => {
  const { data } = await api.get('/seed/status')
  return data
}

export const generateSeedData = async (overwrite = false) => {
  const { data } = await api.post('/seed/generate', { overwrite })
  return data
}

export const getScenarios = async () => {
  const { data } = await api.get('/optimization/scenarios')
  return data
}

export const runScenario = async (number, weights = null) => {
  const { data } = await api.post(`/optimization/scenario/${number}`, {
    scenario_number: number,
    weights,
  })
  return data
}

export const previewConsolidation = async (shipmentIds = '') => {
  const { data } = await api.get('/optimization/consolidate', {
    params: shipmentIds ? { shipment_ids: shipmentIds } : {},
  })
  return data
}

export const submitOptimization = async ({
  shipment_ids,
  vehicle_ids,
  weights,
  road_type = 'mixed',
  weight_profile = null,
  time_limit_seconds = 30,
  enable_consolidation = true,
}) => {
  const { data } = await api.post('/optimization/optimize', {
    shipment_ids,
    vehicle_ids,
    weights,
    road_type,
    weight_profile,
    time_limit_seconds,
    enable_consolidation,
  })
  return data
}

export const getExplanation = async (jobId) => {
  const { data } = await api.get(`/optimization/explain/${jobId}`)
  return data
}
