import React, { useState, useEffect } from 'react'
import { useI18nStore } from '../../services/i18n'
import CommunicationModal from './CommunicationModal'

export default function DriverFacilities({ defaultCategory = 'restaurants' }) {
  const { language, t } = useI18nStore()
  const [activeTab, setActiveTab] = useState(defaultCategory)
  const [facilities, setFacilities] = useState([])
  const [loading, setLoading] = useState(false)
  const [contactTarget, setContactTarget] = useState(null)
  const [isCommOpen, setIsCommOpen] = useState(false)

  const TABS = [
    { id: 'restaurants', label: t('trip.food', 'Food & Dhabas'), icon: '🍛' },
    { id: 'parking', label: t('trip.parking', 'Free Parking'), icon: '🅿️' },
    { id: 'restrooms', label: t('trip.restroom', 'Restrooms & Showers'), icon: '🚻' },
    { id: 'fuel_stations', label: t('trip.fuel_stops', 'Diesel Bunkers'), icon: '⛽' },
    { id: 'puncture_shops', label: t('trip.puncture', 'Puncture Help'), icon: '⚙️' },
  ]

  // Verified Indian highway facilities mock dataset
  const DATA = {
    restaurants: [
      {
        id: 'rest-1',
        name: 'Shiva Dhaba & Family Restaurant',
        highway: 'NH48 (Delhi-Jaipur Highway)',
        distance_km: 4.2,
        detour_min: 5,
        cuisine: 'North Indian / Pure Veg & Non-Veg Dhaba',
        avg_cost: '₹180 / person',
        rating: 4.6,
        phone: '+91 98765 11223',
        amenities: ['Truck Bay', 'Clean Toilets', '24/7 Chai'],
      },
      {
        id: 'rest-2',
        name: 'Grand Highway Food Plaza (Nagpur Hub)',
        highway: 'NH44 North-South Corridor',
        distance_km: 12.0,
        detour_min: 8,
        cuisine: 'Multi-Cuisine / South & North Indian Thali',
        avg_cost: '₹220 / person',
        rating: 4.8,
        phone: '+91 94230 44556',
        amenities: ['Air Conditioned', 'CCTV Yard', 'Driver Rest Area'],
      },
    ],
    parking: [
      {
        id: 'park-1',
        name: 'NHAI Highway Truck Layby & Rest Bay',
        highway: 'NH48 Mile 78',
        distance_km: 3.5,
        detour_min: 2,
        fee: 'Free Parking',
        capacity: '60 Trucks',
        security: '24/7 Security & High-Mast Lighting',
        phone: '+91 80456 71001',
      },
      {
        id: 'park-2',
        name: 'Kisan Logistics Truck Terminal & Staging Bay',
        highway: 'NH44 Nagpur Ring Road',
        distance_km: 8.0,
        detour_min: 6,
        fee: '₹50 / overnight',
        capacity: '120 Trucks',
        security: 'Gated with CCTV & Guard',
        phone: '+91 80456 71002',
      },
    ],
    restrooms: [
      {
        id: 'wc-1',
        name: 'NHAI Swachh Highway Plaza Restrooms',
        highway: 'NH48 Mile 45',
        distance_km: 2.1,
        detour_min: 2,
        cleanliness: '5/5 Star Cleanliness',
        amenities: ['Running Water', 'Western & Indian Toilets', 'Hot Showers'],
        fee: 'Free Public Facility',
        phone: '+91 80456 79999',
      },
      {
        id: 'wc-2',
        name: 'BPCL Coco Highway Comfort Station',
        highway: 'NH44 Mile 180',
        distance_km: 6.8,
        detour_min: 4,
        cleanliness: '4.8/5 Star Cleanliness',
        amenities: ['Clean Restrooms', 'Driver Bathrooms', 'Drinking Water'],
        fee: 'Free for Commercial Drivers',
        phone: '+91 80456 79998',
      },
    ],
    fuel_stations: [
      {
        id: 'fuel-1',
        name: 'Indian Oil Highway Bunkering Plaza',
        highway: 'NH48 Express Mile 120',
        distance_km: 5.4,
        detour_min: 4,
        diesel_price: '₹93.0 / Litre',
        amenities: ['24/7 High-Speed Diesel', 'DEF AdBlue', 'Air Tower', 'Dormitory'],
        phone: '+91 98765 22334',
      },
      {
        id: 'fuel-2',
        name: 'BPCL Coco Bunkering Hub (Nagpur)',
        highway: 'NH44 Corridor',
        distance_km: 14.5,
        detour_min: 7,
        diesel_price: '₹92.5 / Litre',
        amenities: ['High-Flow Bunkering', 'Truck Wash', 'Free Restrooms'],
        phone: '+91 94230 55667',
      },
    ],
    puncture_shops: [
      {
        id: 'punc-1',
        name: 'XYZ Highway Tubeless Tyre & Radial Care',
        highway: 'NH48 Mile 64 (Near Lonavala)',
        distance_km: 2.4,
        detour_min: 7,
        services: 'Tubeless Puncture, Radial Patching, Nitrogen',
        phone: '+91 98765 44210',
        status: '24/7 OPEN',
      },
      {
        id: 'punc-2',
        name: 'Om Sai Highway Tyre Service',
        highway: 'NH44 North-South Corridor',
        distance_km: 6.1,
        detour_min: 12,
        services: 'Heavy Truck Tyre Retreading, Mobile Van',
        phone: '+91 94230 18832',
        status: 'OPEN',
      },
    ],
  }

  useEffect(() => {
    setFacilities(DATA[activeTab] || [])
  }, [activeTab])

  const handleCall = (item) => {
    setContactTarget(item)
    setIsCommOpen(true)
  }

  return (
    <div style={{ background: '#121222', borderRadius: 20, padding: '24px', border: '1px solid #2d2d48', marginTop: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
        <div>
          <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#fff', margin: 0 }}>
            🛣️ {t('facilities.food_title', 'Highway Amenities & Driver Facilities')}
          </h2>
          <p style={{ fontSize: '0.8rem', color: '#9ca3af', margin: '4px 0 0' }}>
            Verified pit-stops, dhabas, laybys, and tyre repair along Indian freight corridors
          </p>
        </div>
      </div>

      {/* Category Tabs */}
      <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '10px', marginBottom: '16px' }}>
        {TABS.map((tab) => {
          const isSelected = activeTab === tab.id
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '10px 16px',
                borderRadius: 12,
                background: isSelected ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : '#1a1a30',
                color: isSelected ? '#fff' : '#cbd5e1',
                border: isSelected ? '1px solid #a5b4fc' : '1px solid #2d2d44',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                whiteSpace: 'nowrap',
                transition: 'all 0.2s',
              }}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          )
        })}
      </div>

      {/* Facilities Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '14px' }}>
        {facilities.map((f) => (
          <div
            key={f.id}
            style={{
              background: '#181832',
              borderRadius: 16,
              border: '1px solid #2d2d48',
              padding: '18px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <h4 style={{ fontSize: '1rem', fontWeight: 800, color: '#fff', margin: 0 }}>
                  {f.name}
                </h4>
                <span
                  style={{
                    background: '#10b98122',
                    color: '#34d399',
                    padding: '4px 8px',
                    borderRadius: 8,
                    fontSize: '0.72rem',
                    fontWeight: 700,
                  }}
                >
                  {f.distance_km} km away
                </span>
              </div>

              <div style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: '6px' }}>
                📍 {f.highway}
              </div>

              {f.cuisine && <div style={{ fontSize: '0.8rem', color: '#e2e8f0', marginBottom: '4px' }}>🍽️ {f.cuisine}</div>}
              {f.fee && <div style={{ fontSize: '0.8rem', color: '#38bdf8', marginBottom: '4px' }}>🏷️ {f.fee}</div>}
              {f.cleanliness && <div style={{ fontSize: '0.8rem', color: '#a78bfa', marginBottom: '4px' }}>✨ {f.cleanliness}</div>}
              {f.diesel_price && <div style={{ fontSize: '0.8rem', color: '#fbbf24', marginBottom: '4px' }}>⛽ {f.diesel_price}</div>}
              {f.services && <div style={{ fontSize: '0.8rem', color: '#f87171', marginBottom: '4px' }}>🔧 {f.services}</div>}

              {f.amenities && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px' }}>
                  {f.amenities.map((a, i) => (
                    <span
                      key={i}
                      style={{
                        background: '#242444',
                        color: '#a5b4fc',
                        fontSize: '0.7rem',
                        padding: '3px 8px',
                        borderRadius: 6,
                      }}
                    >
                      ✓ {a}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: '8px', marginTop: '16px', paddingTop: '12px', borderTop: '1px solid #262640' }}>
              <button
                type="button"
                onClick={() => handleCall(f)}
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  borderRadius: 10,
                  background: 'linear-gradient(135deg, #10b981, #059669)',
                  color: '#fff',
                  border: 'none',
                  fontWeight: 700,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                }}
              >
                <span>📞</span>
                <span>{t('facilities.call', 'Call')}</span>
              </button>
              <button
                type="button"
                onClick={() => alert(`Navigating to ${f.name} on ${f.highway} (${f.distance_km} km away).`)}
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  borderRadius: 10,
                  background: '#2d2d48',
                  color: '#fff',
                  border: '1px solid #3b3b5c',
                  fontWeight: 700,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                }}
              >
                <span>📍</span>
                <span>{t('facilities.navigate', 'Navigate')}</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Safe Phone Dialer Bridge Modal */}
      <CommunicationModal
        isOpen={isCommOpen}
        onClose={() => setIsCommOpen(false)}
        contactData={contactTarget}
      />
    </div>
  )
}
