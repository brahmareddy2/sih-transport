/**
 * ML Dashboard — Phase 3 AI/ML Prediction & Risk Intelligence
 * Full-featured dashboard: demand forecasting, delay risk, vehicle health, anomaly detection.
 */
import React, { useState, useEffect, useCallback } from "react"
import {
  trainDemandModel, trainDelayModel, trainVehicleRisk,
  predictDemand, predictDelay, predictVehicleRisk, detectAnomalies,
  getModelRegistry, getPredictionsLog,
} from "../services/mlApi"

const CITIES = [
  "Mumbai","Delhi","Bangalore","Hyderabad","Chennai","Kolkata",
  "Pune","Ahmedabad","Jaipur","Surat","Lucknow","Kanpur",
  "Nagpur","Patna","Indore","Thane","Bhopal","Visakhapatnam",
  "Pimpri-Chinchwad","Vadodara",
]

function today(offset = 0) {
  const d = new Date()
  d.setDate(d.getDate() + offset)
  return d.toISOString().split("T")[0]
}

function riskColor(level) {
  if (!level) return "#6b7280"
  const l = level.toUpperCase()
  if (l === "HIGH")   return "#ef4444"
  if (l === "MEDIUM") return "#f59e0b"
  return "#22c55e"
}

function RiskBadge({ level }) {
  const color = riskColor(level)
  return (
    <span style={{
      display:"inline-block",padding:"2px 10px",borderRadius:"999px",
      fontSize:"0.72rem",fontWeight:700,letterSpacing:"0.05em",
      background:color+"22",color,border:`1px solid ${color}44`,
    }}>
      {level || "—"}
    </span>
  )
}

function StatCard({ icon, label, value, sub, accent="#6366f1" }) {
  return (
    <div style={{
      background:"var(--color-surface,#1e1e2e)",borderRadius:14,
      padding:"18px 22px",border:`1px solid ${accent}33`,
      boxShadow:`0 0 20px ${accent}18`,
    }}>
      <div style={{fontSize:"1.6rem",marginBottom:4}}>{icon}</div>
      <div style={{fontSize:"0.78rem",color:"var(--color-text-secondary,#9ca3af)",marginBottom:2}}>{label}</div>
      <div style={{fontSize:"1.5rem",fontWeight:800,color:accent}}>{value}</div>
      {sub && <div style={{fontSize:"0.72rem",color:"var(--color-text-secondary,#9ca3af)",marginTop:2}}>{sub}</div>}
    </div>
  )
}

function SectionCard({ title, badge, children }) {
  return (
    <div style={{
      background:"var(--color-surface,#1e1e2e)",borderRadius:16,
      padding:"24px",border:"1px solid var(--color-border,#2d2d3d)",marginBottom:24,
    }}>
      <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:18}}>
        <h3 style={{margin:0,fontSize:"1rem",fontWeight:700}}>{title}</h3>
        {badge && (
          <span style={{
            fontSize:"0.65rem",fontWeight:700,padding:"2px 8px",borderRadius:999,
            background:"#6366f122",color:"#818cf8",border:"1px solid #6366f144",letterSpacing:"0.06em",
          }}>
            {badge}
          </span>
        )}
      </div>
      {children}
    </div>
  )
}

function FormRow({ label, children }) {
  return (
    <div style={{marginBottom:12}}>
      <label style={{display:"block",fontSize:"0.78rem",fontWeight:600,marginBottom:4,color:"var(--color-text-secondary,#9ca3af)"}}>
        {label}
      </label>
      {children}
    </div>
  )
}

const inputStyle = {
  width:"100%",padding:"8px 12px",borderRadius:8,fontSize:"0.85rem",
  background:"var(--color-bg,#13131f)",border:"1px solid var(--color-border,#2d2d3d)",
  color:"var(--color-text,#f1f5f9)",outline:"none",boxSizing:"border-box",
}

function Btn({ onClick, loading, disabled, children, accent="#6366f1", size="md" }) {
  return (
    <button
      onClick={onClick}
      disabled={loading||disabled}
      style={{
        padding:size==="sm"?"6px 14px":"10px 22px",
        borderRadius:9,fontWeight:700,fontSize:size==="sm"?"0.78rem":"0.85rem",
        background:loading||disabled?"#374151":accent,
        color:"#fff",border:"none",cursor:loading||disabled?"not-allowed":"pointer",
        opacity:loading||disabled?0.7:1,transition:"all 0.2s",
      }}
    >
      {loading?"? Loading…":children}
    </button>
  )
}

function ErrorMsg({ msg }) {
  if (!msg) return null
  return (
    <div style={{marginTop:10,padding:"8px 14px",borderRadius:8,background:"#ef444422",color:"#ef4444",fontSize:"0.8rem",border:"1px solid #ef444433"}}>
      ?? {msg}
    </div>
  )
}

// Training Tab
function TrainingTab({ registry, reloadRegistry }) {
  const [status, setStatus] = useState({})
  const [loading, setLoading] = useState({})

  async function train(name, fn) {
    setLoading(l=>({...l,[name]:true}))
    setStatus(s=>({...s,[name]:null}))
    try {
      const res = await fn()
      setStatus(s=>({...s,[name]:{ok:true,data:res}}))
      reloadRegistry()
    } catch(e) {
      setStatus(s=>({...s,[name]:{ok:false,msg:e.response?.data?.detail||e.message}}))
    } finally {
      setLoading(l=>({...l,[name]:false}))
    }
  }

  const models=[
    {key:"demand",label:"Demand Forecasting",icon:"??",fn:trainDemandModel,accent:"#6366f1"},
    {key:"delay",label:"Delay Risk Classifier",icon:"??",fn:trainDelayModel,accent:"#f59e0b"},
    {key:"vehicle",label:"Vehicle Health Risk",icon:"??",fn:trainVehicleRisk,accent:"#22c55e"},
  ]

  return (
    <SectionCard title="Model Training Hub" badge="AI Decision-Support Only">
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(280px,1fr))",gap:16}}>
        {models.map(m=>{
          const reg=registry.find(r=>r.model_name.startsWith(m.key))
          const s=status[m.key]
          return (
            <div key={m.key} style={{background:"var(--color-bg,#13131f)",borderRadius:12,padding:18,border:`1px solid ${m.accent}33`}}>
              <div style={{fontSize:"1.6rem",marginBottom:6}}>{m.icon}</div>
              <div style={{fontWeight:700,fontSize:"0.95rem",marginBottom:4}}>{m.label}</div>
              {reg&&(
                <div style={{fontSize:"0.72rem",color:"#6b7280",marginBottom:10}}>
                  v{reg.model_version} · {reg.training_date?new Date(reg.training_date).toLocaleDateString("en-IN"):"Never trained"}
                </div>
              )}
              {reg?.evaluation_metrics&&Object.keys(reg.evaluation_metrics).length>0&&(
                <div style={{fontSize:"0.72rem",background:"#1e293b",borderRadius:6,padding:"6px 10px",marginBottom:10,fontFamily:"monospace"}}>
                  {Object.entries(reg.evaluation_metrics).slice(0,3).map(([k,v])=>(
                    <div key={k}>{k}: <span style={{color:m.accent}}>{typeof v==="number"?v.toFixed(3):v}</span></div>
                  ))}
                </div>
              )}
              <Btn onClick={()=>train(m.key,m.fn)} loading={loading[m.key]} accent={m.accent} size="sm">?? Retrain</Btn>
              {s?.ok&&<div style={{marginTop:8,fontSize:"0.75rem",color:"#22c55e"}}>? Trained successfully</div>}
              {s&&!s.ok&&<ErrorMsg msg={s.msg}/>}
            </div>
          )
        })}
      </div>
      <div style={{marginTop:16,padding:"10px 16px",borderRadius:8,background:"#6366f111",border:"1px solid #6366f133",fontSize:"0.78rem",color:"#818cf8"}}>
        ?? <strong>AI Decision-Support:</strong> Models bias OR-Tools route optimization via cost penalties. They do <em>not</em> override hard constraints.
      </div>
    </SectionCard>
  )
}

// Demand Tab
function DemandTab() {
  const [form,setForm]=useState({origin:"Mumbai",dest:"Pune",date:today(7)})
  const [result,setResult]=useState(null)
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState("")

  async function predict() {
    setLoading(true);setError("");setResult(null)
    try { setResult(await predictDemand(form.origin,form.dest,form.date)) }
    catch(e) { setError(e.response?.data?.detail||e.message) }
    finally { setLoading(false) }
  }

  return (
    <SectionCard title="?? Demand Forecasting" badge="Random Forest Regressor">
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr auto",gap:12,alignItems:"end"}}>
        <FormRow label="Origin City">
          <select style={inputStyle} value={form.origin} onChange={e=>setForm(f=>({...f,origin:e.target.value}))}>
            {CITIES.map(c=><option key={c}>{c}</option>)}
          </select>
        </FormRow>
        <FormRow label="Destination City">
          <select style={inputStyle} value={form.dest} onChange={e=>setForm(f=>({...f,dest:e.target.value}))}>
            {CITIES.map(c=><option key={c}>{c}</option>)}
          </select>
        </FormRow>
        <FormRow label="Target Date">
          <input type="date" style={inputStyle} value={form.date} min={today(1)} onChange={e=>setForm(f=>({...f,date:e.target.value}))}/>
        </FormRow>
        <div style={{paddingBottom:1}}><Btn onClick={predict} loading={loading} accent="#6366f1">Predict</Btn></div>
      </div>
      <ErrorMsg msg={error}/>
      {result&&(
        <div style={{marginTop:20}}>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(160px,1fr))",gap:12}}>
            <StatCard icon="??" label="Predicted Shipments" value={result.predicted_shipments} sub={`${result.confidence_lower}–${result.confidence_upper} range`} accent="#6366f1"/>
            <StatCard icon="??" label="Predicted Weight (kg)" value={result.predicted_weight_kg?.toFixed(0)||"—"} accent="#8b5cf6"/>
            <StatCard icon="??" label="Prediction Horizon" value={result.prediction_horizon_days+" days"} accent="#a78bfa"/>
            <StatCard icon="??" label="Model MAE" value={result.model_mae?.toFixed(2)||"—"} sub="shipments/day error" accent="#c4b5fd"/>
          </div>
          <div style={{marginTop:14,padding:"10px 16px",borderRadius:8,background:"#1e293b",fontSize:"0.8rem",color:"#94a3b8"}}>
            Route: <strong>{result.origin_city}</strong> ? <strong>{result.destination_city}</strong> · Date: <strong>{result.target_date}</strong>
          </div>
        </div>
      )}
    </SectionCard>
  )
}

// Delay Tab
function DelayTab() {
  const [form,setForm]=useState({shipment_id:"",vehicle_id:"",distance_km:500,estimated_duration_min:420})
  const [result,setResult]=useState(null)
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState("")

  async function predict() {
    setLoading(true);setError("");setResult(null)
    try {
      setResult(await predictDelay(
        form.shipment_id||"00000000-0000-0000-0000-000000000001",
        form.vehicle_id||"00000000-0000-0000-0000-000000000002",
        parseFloat(form.distance_km),parseFloat(form.estimated_duration_min),
      ))
    } catch(e) { setError(e.response?.data?.detail||e.message) }
    finally { setLoading(false) }
  }

  return (
    <SectionCard title="?? Delivery Delay Risk Prediction" badge="Random Forest Classifier">
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
        <FormRow label="Shipment ID (leave blank for demo)">
          <input style={inputStyle} value={form.shipment_id} placeholder="00000000-0000-0000-0000-000000000001" onChange={e=>setForm(f=>({...f,shipment_id:e.target.value}))}/>
        </FormRow>
        <FormRow label="Vehicle ID (leave blank for demo)">
          <input style={inputStyle} value={form.vehicle_id} placeholder="00000000-0000-0000-0000-000000000002" onChange={e=>setForm(f=>({...f,vehicle_id:e.target.value}))}/>
        </FormRow>
        <FormRow label="Distance (km)">
          <input type="number" style={inputStyle} value={form.distance_km} min={1} onChange={e=>setForm(f=>({...f,distance_km:e.target.value}))}/>
        </FormRow>
        <FormRow label="Estimated Duration (min)">
          <input type="number" style={inputStyle} value={form.estimated_duration_min} min={30} onChange={e=>setForm(f=>({...f,estimated_duration_min:e.target.value}))}/>
        </FormRow>
      </div>
      <Btn onClick={predict} loading={loading} accent="#f59e0b">Predict Delay Risk</Btn>
      <ErrorMsg msg={error}/>
      {result&&(
        <div style={{marginTop:20}}>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(160px,1fr))",gap:12,marginBottom:16}}>
            <StatCard icon="??" label="Delay Probability" value={`${(result.delay_probability*100).toFixed(1)}%`} accent={riskColor(result.risk_level)}/>
            <div style={{background:"var(--color-bg,#13131f)",borderRadius:14,padding:"18px 22px",border:`1px solid ${riskColor(result.risk_level)}33`}}>
              <div style={{fontSize:"0.78rem",color:"#9ca3af",marginBottom:6}}>Risk Level</div>
              <RiskBadge level={result.risk_level}/>
            </div>
            <StatCard icon="?" label="Predicted Delay" value={`${result.predicted_delay_minutes} min`} accent="#f59e0b"/>
          </div>
          <div style={{background:"#1e293b",borderRadius:10,padding:"14px 18px"}}>
            <div style={{fontWeight:700,fontSize:"0.8rem",marginBottom:8,color:"#f59e0b"}}>?? Explanation</div>
            {result.explanation.map((line,i)=>(
              <div key={i} style={{fontSize:"0.8rem",color:"#94a3b8",marginBottom:4}}>• {line}</div>
            ))}
          </div>
        </div>
      )}
    </SectionCard>
  )
}

// Vehicle Risk Tab
function VehicleRiskTab() {
  const [vehicleId,setVehicleId]=useState("")
  const [result,setResult]=useState(null)
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState("")

  async function predict() {
    setLoading(true);setError("");setResult(null)
    try { setResult(await predictVehicleRisk(vehicleId.trim())) }
    catch(e) { setError(e.response?.data?.detail||e.message) }
    finally { setLoading(false) }
  }

  const meterColor=result?riskColor(result.risk_level):"#6b7280"
  const meterPct=result?Math.min(100,result.risk_score):0

  return (
    <SectionCard title="?? Vehicle Health & Breakdown Risk" badge="Rule-Based Scoring + Heuristics">
      <div style={{display:"flex",gap:12,alignItems:"flex-end",flexWrap:"wrap"}}>
        <div style={{flex:1,minWidth:260}}>
          <FormRow label="Vehicle ID (UUID)">
            <input style={inputStyle} value={vehicleId} placeholder="Paste vehicle UUID from fleet data" onChange={e=>setVehicleId(e.target.value)}/>
          </FormRow>
        </div>
        <Btn onClick={predict} loading={loading} accent="#22c55e" disabled={!vehicleId.trim()}>Assess Risk</Btn>
      </div>
      <ErrorMsg msg={error}/>
      {result&&(
        <div style={{marginTop:20}}>
          <div style={{background:"var(--color-bg,#13131f)",borderRadius:14,padding:"20px 24px",marginBottom:16}}>
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:12}}>
              <span style={{fontWeight:700,fontSize:"0.9rem"}}>Risk Score</span>
              <RiskBadge level={result.risk_level}/>
            </div>
            <div style={{background:"#1e293b",borderRadius:999,height:12,overflow:"hidden",marginBottom:6}}>
              <div style={{width:`${meterPct}%`,height:"100%",borderRadius:999,background:`linear-gradient(90deg,#22c55e,${meterColor})`,transition:"width 0.8s ease"}}/>
            </div>
            <div style={{textAlign:"right",fontSize:"1.4rem",fontWeight:800,color:meterColor}}>
              {result.risk_score.toFixed(1)} / 100
            </div>
          </div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
            <div style={{background:"#1e293b",borderRadius:10,padding:"14px 18px"}}>
              <div style={{fontWeight:700,fontSize:"0.8rem",marginBottom:8,color:"#22c55e"}}>?? Risk Indicators</div>
              {result.risk_indicators.length===0
                ?<div style={{fontSize:"0.8rem",color:"#6b7280"}}>No active risk indicators.</div>
                :result.risk_indicators.map((r,i)=>(
                  <div key={i} style={{fontSize:"0.8rem",color:"#fbbf24",marginBottom:4}}>• {r}</div>
                ))
              }
            </div>
            <div style={{background:"#1e293b",borderRadius:10,padding:"14px 18px"}}>
              <div style={{fontWeight:700,fontSize:"0.8rem",marginBottom:8,color:"#6366f1"}}>?? Recommendation</div>
              <div style={{fontSize:"0.85rem",color:result.inspection_recommended?"#ef4444":"#22c55e"}}>
                {result.inspection_recommended?"?? Inspection Required":"?? Vehicle OK for dispatch"}
              </div>
            </div>
          </div>
        </div>
      )}
    </SectionCard>
  )
}

// Anomaly Tab
function AnomalyTab() {
  const [routeId,setRouteId]=useState("")
  const [result,setResult]=useState(null)
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState("")

  async function detect() {
    setLoading(true);setError("");setResult(null)
    try { setResult(await detectAnomalies(routeId.trim())) }
    catch(e) { setError(e.response?.data?.detail||e.message) }
    finally { setLoading(false) }
  }

  return (
    <SectionCard title="?? Anomaly Detection" badge="IsolationForest">
      <div style={{display:"flex",gap:12,alignItems:"flex-end",flexWrap:"wrap"}}>
        <div style={{flex:1,minWidth:260}}>
          <FormRow label="Route ID (UUID)">
            <input style={inputStyle} value={routeId} placeholder="Paste route UUID from historical trips" onChange={e=>setRouteId(e.target.value)}/>
          </FormRow>
        </div>
        <Btn onClick={detect} loading={loading} accent="#ef4444" disabled={!routeId.trim()}>Detect Anomaly</Btn>
      </div>
      <ErrorMsg msg={error}/>
      {result&&(
        <div style={{marginTop:20}}>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(160px,1fr))",gap:12,marginBottom:16}}>
            <div style={{background:"var(--color-bg,#13131f)",borderRadius:14,padding:"18px 22px",border:`1px solid ${result.is_anomaly?"#ef444444":"#22c55e44"}`}}>
              <div style={{fontSize:"0.78rem",color:"#9ca3af",marginBottom:6}}>Anomaly Detected</div>
              <div style={{fontSize:"1.5rem",fontWeight:800,color:result.is_anomaly?"#ef4444":"#22c55e"}}>
                {result.is_anomaly?"?? YES":"? NO"}
              </div>
            </div>
            <StatCard icon="??" label="Anomaly Score" value={result.anomaly_score?.toFixed(4)??"—"} accent="#ef4444"/>
            {result.anomaly_type&&<StatCard icon="???" label="Anomaly Type" value={result.anomaly_type} accent="#f59e0b"/>}
          </div>
          <div style={{background:"#1e293b",borderRadius:10,padding:"14px 18px"}}>
            <div style={{fontWeight:700,fontSize:"0.8rem",marginBottom:8,color:"#ef4444"}}>?? Explanation</div>
            {(Array.isArray(result.explanation)?result.explanation:[result.explanation]).map((line,i)=>(
              <div key={i} style={{fontSize:"0.8rem",color:"#94a3b8",marginBottom:4}}>• {line}</div>
            ))}
          </div>
        </div>
      )}
    </SectionCard>
  )
}

// Predictions Log
function PredictionsLog() {
  const [logs,setLogs]=useState([])
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState("")
  const load=useCallback(async()=>{
    setLoading(true);setError("")
    try{setLogs(await getPredictionsLog(50))}
    catch(e){setError(e.response?.data?.detail||e.message)}
    finally{setLoading(false)}
  },[])
  useEffect(()=>{load()},[load])
  return (
    <SectionCard title="?? Predictions Log" badge="Last 50 Records">
      <div style={{display:"flex",gap:10,marginBottom:14}}>
        <Btn onClick={load} loading={loading} accent="#6366f1" size="sm">?? Refresh</Btn>
      </div>
      <ErrorMsg msg={error}/>
      {logs.length===0&&!loading&&(
        <div style={{color:"#6b7280",fontSize:"0.85rem",padding:"20px 0"}}>No predictions logged yet.</div>
      )}
      <div style={{overflowX:"auto"}}>
        <table style={{width:"100%",borderCollapse:"collapse",fontSize:"0.78rem"}}>
          <thead>
            <tr style={{borderBottom:"1px solid var(--color-border,#2d2d3d)"}}>
              {["Model","Version","Entity Type","Risk Level","Timestamp"].map(h=>(
                <th key={h} style={{padding:"8px 12px",textAlign:"left",color:"#6b7280",fontWeight:600}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {logs.map((log,i)=>(
              <tr key={i} style={{borderBottom:"1px solid #1e293b"}}>
                <td style={{padding:"8px 12px",fontWeight:600}}>{log.model_name}</td>
                <td style={{padding:"8px 12px",color:"#6b7280"}}>v{log.model_version}</td>
                <td style={{padding:"8px 12px"}}>{log.target_entity_type}</td>
                <td style={{padding:"8px 12px"}}><RiskBadge level={log.risk_level}/></td>
                <td style={{padding:"8px 12px",color:"#6b7280"}}>{new Date(log.prediction_timestamp).toLocaleString("en-IN")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  )
}

// Main Dashboard
const TABS=[
  {id:"training",label:"?? Training Hub"},
  {id:"demand",label:"?? Demand Forecast"},
  {id:"delay",label:"?? Delay Risk"},
  {id:"vehicle",label:"?? Vehicle Health"},
  {id:"anomaly",label:"?? Anomaly Detect"},
  {id:"logs",label:"?? Predictions Log"},
]

export default function MlDashboard() {
  const [tab,setTab]=useState("training")
  const [registry,setRegistry]=useState([])
  const reloadRegistry=useCallback(async()=>{
    try{setRegistry(await getModelRegistry())}catch{}
  },[])
  useEffect(()=>{reloadRegistry()},[reloadRegistry])
  const trainedCount=registry.filter(m=>m.training_date).length

  return (
    <div style={{fontFamily:"'Inter','Segoe UI',sans-serif"}}>
      <div style={{marginBottom:24}}>
        <div style={{display:"flex",alignItems:"center",gap:14,flexWrap:"wrap"}}>
          <div>
            <h2 style={{margin:0,fontSize:"1.4rem",fontWeight:800,background:"linear-gradient(90deg,#6366f1,#a78bfa)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}}>
              ?? AI/ML Prediction & Risk Intelligence
            </h2>
            <p style={{margin:"4px 0 0",fontSize:"0.8rem",color:"#6b7280"}}>
              Phase 3 · Decision-support models powering OR-Tools optimization
            </p>
          </div>
          <span style={{marginLeft:"auto",fontSize:"0.72rem",padding:"4px 12px",borderRadius:999,background:"#22c55e22",color:"#22c55e",border:"1px solid #22c55e44",fontWeight:700}}>
            {trainedCount}/{registry.length} Models Trained
          </span>
        </div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(140px,1fr))",gap:12,marginTop:18}}>
          <StatCard icon="??" label="AI Models" value={registry.length||3} sub="demand · delay · anomaly" accent="#6366f1"/>
          <StatCard icon="?" label="Models Ready" value={trainedCount} sub="trained on fleet data" accent="#22c55e"/>
          <StatCard icon="??" label="OR-Tools Integration" value="Active" sub="penalty injection enabled" accent="#f59e0b"/>
          <StatCard icon="???" label="Hard Constraints" value="OR-Tools" sub="AI cannot override" accent="#ef4444"/>
        </div>
      </div>
      <div style={{display:"flex",gap:4,marginBottom:20,overflowX:"auto",paddingBottom:4}}>
        {TABS.map(t=>(
          <button key={t.id} onClick={()=>setTab(t.id)} style={{
            padding:"8px 18px",borderRadius:999,fontWeight:600,fontSize:"0.8rem",whiteSpace:"nowrap",
            background:tab===t.id?"#6366f1":"transparent",
            color:tab===t.id?"#fff":"#9ca3af",
            border:tab===t.id?"none":"1px solid #2d2d3d",
            cursor:"pointer",transition:"all 0.2s",
          }}>
            {t.label}
          </button>
        ))}
      </div>
      {tab==="training"&&<TrainingTab registry={registry} reloadRegistry={reloadRegistry}/>}
      {tab==="demand"&&<DemandTab/>}
      {tab==="delay"&&<DelayTab/>}
      {tab==="vehicle"&&<VehicleRiskTab/>}
      {tab==="anomaly"&&<AnomalyTab/>}
      {tab==="logs"&&<PredictionsLog/>}
    </div>
  )
}
