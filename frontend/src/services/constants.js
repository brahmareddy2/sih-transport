/**
 * Application constants: roles, route paths, Indian cities, enums.
 */

// ── User Roles ───────────────────────────────────────────
export const ROLES = {
  ADMIN: 'admin',
  OPERATOR: 'operator',
  FLEET_MANAGER: 'fleet_manager',
  DRIVER: 'driver',
  CUSTOMER: 'customer',
}

// ── Role display labels ───────────────────────────────────
export const ROLE_LABELS = {
  admin: 'Administrator',
  operator: 'Logistics Operator',
  fleet_manager: 'Fleet Manager',
  driver: 'Driver',
  customer: 'Customer',
}

// ── Role colors ───────────────────────────────────────────
export const ROLE_COLORS = {
  admin: '#8b5cf6',
  operator: '#3b82f6',
  fleet_manager: '#06b6d4',
  driver: '#10b981',
  customer: '#f59e0b',
}

// ── Route paths by role ───────────────────────────────────
export const ROLE_HOME_PATH = {
  admin: '/admin',
  operator: '/operator',
  fleet_manager: '/fleet',
  driver: '/driver',
  customer: '/customer',
}

// ── Indian Cities (12 logistics hubs) ────────────────────
export const INDIAN_CITIES = [
  { name: 'Mumbai', state: 'Maharashtra', lat: 19.0760, lon: 72.8777 },
  { name: 'Pune', state: 'Maharashtra', lat: 18.5204, lon: 73.8567 },
  { name: 'Delhi', state: 'Delhi', lat: 28.6139, lon: 77.2090 },
  { name: 'Bengaluru', state: 'Karnataka', lat: 12.9716, lon: 77.5946 },
  { name: 'Hyderabad', state: 'Telangana', lat: 17.3850, lon: 78.4867 },
  { name: 'Chennai', state: 'Tamil Nadu', lat: 13.0827, lon: 80.2707 },
  { name: 'Ahmedabad', state: 'Gujarat', lat: 23.0225, lon: 72.5714 },
  { name: 'Kolkata', state: 'West Bengal', lat: 22.5726, lon: 88.3639 },
  { name: 'Nagpur', state: 'Maharashtra', lat: 21.1458, lon: 79.0882 },
  { name: 'Jaipur', state: 'Rajasthan', lat: 26.9124, lon: 75.7873 },
  { name: 'Surat', state: 'Gujarat', lat: 21.1702, lon: 72.8311 },
  { name: 'Lucknow', state: 'Uttar Pradesh', lat: 26.8467, lon: 80.9462 },
]

// ── Vehicle Types ─────────────────────────────────────────
export const VEHICLE_TYPES = [
  { value: 'mini_truck', label: 'Mini Truck (Tata Ace)', capacity: '750 kg' },
  { value: 'tempo', label: 'Tempo (Mahindra Supro)', capacity: '1,200 kg' },
  { value: 'medium_truck', label: 'Medium Truck (Tata 407)', capacity: '3,500 kg' },
  { value: 'large_truck', label: 'Large Truck (Ashok Leyland)', capacity: '16,000 kg' },
  { value: 'trailer', label: 'Trailer (Volvo FH)', capacity: '25,000 kg' },
]

// ── Shipment Status ───────────────────────────────────────
export const SHIPMENT_STATUS = {
  pending: { label: 'Pending', color: 'warning' },
  consolidated: { label: 'Consolidated', color: 'info' },
  assigned: { label: 'Assigned', color: 'info' },
  in_transit: { label: 'In Transit', color: 'success' },
  delivered: { label: 'Delivered', color: 'success' },
  cancelled: { label: 'Cancelled', color: 'muted' },
  delayed: { label: 'Delayed', color: 'danger' },
}

// ── Goods Types ───────────────────────────────────────────
export const GOODS_TYPES = [
  'FMCG',
  'Pharmaceutical',
  'Automotive',
  'Electronics',
  'Chemicals',
  'Textiles',
  'Perishables',
  'Industrial',
  'Construction',
  'Other',
]

// ── Priority levels ───────────────────────────────────────
export const PRIORITY_LEVELS = [
  { value: 'urgent', label: 'Urgent', color: 'danger' },
  { value: 'high', label: 'High', color: 'warning' },
  { value: 'normal', label: 'Normal', color: 'info' },
  { value: 'low', label: 'Low', color: 'muted' },
]

// ── Incident types ────────────────────────────────────────
export const INCIDENT_TYPES = [
  { value: 'breakdown', label: 'Vehicle Breakdown' },
  { value: 'tyre_puncture', label: 'Tyre Puncture' },
  { value: 'accident', label: 'Accident' },
  { value: 'traffic_jam', label: 'Traffic Jam' },
  { value: 'road_closure', label: 'Road Closure' },
  { value: 'low_fuel', label: 'Low Fuel' },
  { value: 'driver_unavailable', label: 'Driver Unavailable' },
  { value: 'weather_disruption', label: 'Weather Disruption' },
  { value: 'delay', label: 'Delivery Delay' },
  { value: 'other', label: 'Other' },
]

// ── Fuel types ────────────────────────────────────────────
export const FUEL_TYPES = [
  { value: 'diesel', label: 'Diesel', priceKey: 'diesel_price_per_liter' },
  { value: 'petrol', label: 'Petrol', priceKey: 'petrol_price_per_liter' },
  { value: 'cng', label: 'CNG', priceKey: 'cng_price_per_kg' },
  { value: 'ev', label: 'Electric', priceKey: null },
]

// ── Currency formatter ────────────────────────────────────
export const formatINR = (amount) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount)

// ── Distance / weight formatters ──────────────────────────
export const formatKm = (km) => `${Number(km).toFixed(1)} km`
export const formatKg = (kg) => kg >= 1000 ? `${(kg / 1000).toFixed(2)} T` : `${kg} kg`
