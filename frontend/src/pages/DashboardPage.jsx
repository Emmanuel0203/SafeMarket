import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiRequest } from '../services/api'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import {
  Shield, Home, CreditCard, AlertTriangle, FileText,
  Settings, Bell, Search, LogOut, DollarSign, Ban,
  RefreshCcw, TrendingUp, Activity
} from 'lucide-react'

// ── Colores institucionales tipo banco ────────────────────────────────────
const BRAND   = '#1a3c6e'   // azul oscuro principal
const BRAND2  = '#2563eb'   // azul acción
const SUCCESS = '#0d9488'   // verde
const WARN    = '#f59e0b'   // amarillo
const DANGER  = '#ef4444'   // rojo

const DONUT_COLORS = [BRAND2, SUCCESS, WARN, DANGER]

// ── Tooltip personalizado estilo banco ───────────────────────────────────
const BankTooltip = ({ active, payload, label, prefix = '$', suffix = '' }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10,
      padding: '10px 14px', boxShadow: '0 4px 16px rgba(0,0,0,.08)',
      fontFamily: 'DM Sans,sans-serif', fontSize: 13,
    }}>
      {label && <div style={{ color: '#64748b', marginBottom: 4 }}>{label}</div>}
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || BRAND, fontWeight: 700 }}>
          {prefix}{typeof p.value === 'number'
            ? p.value.toLocaleString('es', { maximumFractionDigits: 0 })
            : p.value}{suffix}
        </div>
      ))}
    </div>
  )
}

// ── Gauge de riesgo ───────────────────────────────────────────────────────
const RiskGauge = ({ value = 0, label = '' }) => {
  // value: 0-100
  const pct    = Math.min(100, Math.max(0, value))
  const angle  = -135 + (pct / 100) * 270   // -135° a +135°
  const color  = pct < 34 ? SUCCESS : pct < 67 ? WARN : DANGER
  const text   = pct < 34 ? 'Bajo' : pct < 67 ? 'Medio' : 'Alto'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
      <svg width={180} height={110} viewBox="0 0 180 110">
        {/* Track */}
        <path d="M 20 100 A 70 70 0 1 1 160 100" fill="none" stroke="#e2e8f0" strokeWidth={14} strokeLinecap="round"/>
        {/* Fill */}
        <path d="M 20 100 A 70 70 0 1 1 160 100" fill="none" stroke={color} strokeWidth={14} strokeLinecap="round"
          strokeDasharray={`${(pct / 100) * 220} 220`}/>
        {/* Aguja */}
        <g transform={`translate(90,100) rotate(${angle})`}>
          <line x1={0} y1={0} x2={0} y2={-55} stroke={BRAND} strokeWidth={3} strokeLinecap="round"/>
          <circle cx={0} cy={0} r={6} fill={BRAND}/>
        </g>
        {/* Valor */}
        <text x={90} y={88} textAnchor="middle" fontSize={22} fontWeight={800}
          fontFamily="Sora,sans-serif" fill={color}>{pct.toFixed(0)}%</text>
      </svg>
      <div style={{ fontSize: 13, color: '#64748b' }}>Riesgo <strong style={{ color }}>{text}</strong></div>
      {label && <div style={{ fontSize: 12, color: '#94a3b8' }}>{label}</div>}
    </div>
  )
}

// ── Badges ────────────────────────────────────────────────────────────────
const StatusBadge = ({ status }) => {
  const map = {
    APPROVED: ['#ecfdf5', '#059669', 'Aprobada'],
    DECLINED: ['#fef2f2', '#dc2626', 'Bloqueada'],
    REVIEW:   ['#fffbeb', '#d97706', 'Revisión'],
    PENDING:  ['#eff6ff', '#2563eb', 'Pendiente'],
  }
  const [bg, color, label] = map[status] || ['#f1f5f9', '#64748b', status]
  return (
    <span style={{ background: bg, color, fontSize: 12, fontWeight: 600, padding: '3px 10px', borderRadius: 6 }}>
      {label}
    </span>
  )
}

const RiskBadge = ({ risk }) => {
  const map = {
    LOW:    ['#ecfdf5', '#059669', 'Bajo'],
    MEDIUM: ['#fffbeb', '#d97706', 'Medio'],
    HIGH:   ['#fef2f2', '#dc2626', 'Alto'],
  }
  const [bg, color, label] = map[risk] || ['#f1f5f9', '#64748b', risk]
  return (
    <span style={{ background: bg, color, fontSize: 12, fontWeight: 600, padding: '3px 10px', borderRadius: 6 }}>
      {label}
    </span>
  )
}

// ── Card reutilizable ─────────────────────────────────────────────────────
const Card = ({ children, style = {} }) => (
  <div style={{
    background: '#fff', borderRadius: 16, padding: 24,
    border: '1px solid #e8edf3', boxShadow: '0 1px 4px rgba(26,60,110,.06)',
    ...style,
  }}>{children}</div>
)

const CardTitle = ({ children }) => (
  <h3 style={{
    fontFamily: 'Sora,sans-serif', fontSize: 15, fontWeight: 700,
    color: BRAND, marginBottom: 20, letterSpacing: -.2,
  }}>{children}</h3>
)

// ── Componente principal ──────────────────────────────────────────────────
export default function DashboardPage() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const [activeNav, setActiveNav]       = useState('Inicio')
  const [profile, setProfile]           = useState(null)
  const [stats, setStats]               = useState(null)
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading]           = useState(true)
  const [error, setError]               = useState('')

  useEffect(() => {
    Promise.all([
      apiRequest('/transactions/stats'),
      apiRequest('/transactions/'),
      apiRequest('/users/profile'),
    ])
      .then(([statsData, txData, profileData]) => {
        setStats(statsData)
        setTransactions(txData)
        setProfile(profileData)
      })
      .catch(err => {
        console.error(err)
        setError('No se pudieron cargar los datos. Verifica que el backend esté corriendo.')
      })
      .finally(() => setLoading(false))
  }, [])

  const initials    = profile?.email?.slice(0, 2).toUpperCase() || user?.email?.slice(0, 2).toUpperCase() || 'U'
  const displayName = profile?.email || user?.email || 'Usuario'
  const displayRole = profile?.role  || user?.role  || 'VIEWER'

  const navItems = [
    { label: 'Inicio',        icon: <Home size={18} /> },
    { label: 'Transacciones', icon: <CreditCard size={18} /> },
    { label: 'Riesgos',       icon: <AlertTriangle size={18} /> },
    { label: 'Reportes',      icon: <FileText size={18} /> },
    { label: 'Configuración', icon: <Settings size={18} /> },
  ]

  // ── Datos para gráficas calculados desde transactions reales ─────────────

  // 1. Volumen diario de dinero (área) — agrupa por fecha
  const volumeByDate = Object.values(
    transactions.reduce((acc, tx) => {
      const date = tx.created_at ? tx.created_at.slice(0, 10) : 'Sin fecha'
      if (!acc[date]) acc[date] = { fecha: date.slice(5), total: 0, fraudes: 0 }
      acc[date].total   += tx.amount
      if (tx.is_fraud) acc[date].fraudes += tx.amount
      return acc
    }, {})
  ).slice(-14)  // últimos 14 días

  // 2. Donut — distribución por tipo de transacción
  const byType = Object.entries(
    transactions.reduce((acc, tx) => {
      acc[tx.transaction_type] = (acc[tx.transaction_type] || 0) + 1
      return acc
    }, {})
  ).map(([name, value]) => ({ name, value }))

  const typeLabels = { PURCHASE: 'Compra', TRANSFER: 'Transferencia', WITHDRAWAL: 'Retiro', DEPOSIT: 'Depósito' }

  // 3. Barras horizontales — monto por categoría de comercio (top 6)
  const byCategory = Object.entries(
    transactions.reduce((acc, tx) => {
      const cat = tx.merchant_category || 'Sin categoría'
      acc[cat] = (acc[cat] || 0) + tx.amount
      return acc
    }, {})
  )
    .map(([categoria, monto]) => ({ categoria, monto }))
    .sort((a, b) => b.monto - a.monto)
    .slice(0, 6)

  // 4. Score de riesgo promedio (para el gauge)
  const avgRiskScore = transactions.length
    ? (transactions.reduce((s, tx) => s + (tx.risk_score || 0), 0) / transactions.length) * 100
    : 0

  // Métricas
  const metrics = stats ? [
    {
      icon: <DollarSign size={20} color={BRAND2} />, bg: '#eff6ff',
      val: `$${Number(stats.total_sales).toLocaleString('es', { maximumFractionDigits: 0 })}`,
      label: 'Volumen Total', sub: `${stats.total_transactions} transacciones`,
      border: BRAND2,
    },
    {
      icon: <Ban size={20} color={DANGER} />, bg: '#fef2f2',
      val: stats.blocked_transactions,
      label: 'Bloqueadas', sub: 'Estado DECLINED',
      border: DANGER,
    },
    {
      icon: <RefreshCcw size={20} color={WARN} />, bg: '#fffbeb',
      val: stats.reviewed_transactions,
      label: 'En Revisión', sub: 'Requieren atención',
      border: WARN,
    },
    {
      icon: <AlertTriangle size={20} color={DANGER} />, bg: '#fef2f2',
      val: stats.fraud_count,
      label: 'Fraudes Detectados', sub: `Nivel: ${stats.risk_level}`,
      border: DANGER,
    },
    {
      icon: <TrendingUp size={20} color={SUCCESS} />, bg: '#ecfdf5',
      val: `$${(stats.protected_income / 1000).toFixed(1)}K`,
      label: 'Monto Protegido', sub: '95% del volumen total',
      border: SUCCESS,
    },
  ] : []

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'DM Sans,sans-serif', background: '#f4f7fb' }}>

      {/* ── SIDEBAR ── */}
      <aside style={{
        width: 220, background: BRAND,
        display: 'flex', flexDirection: 'column',
        position: 'fixed', height: '100vh', top: 0, left: 0, zIndex: 100,
      }}>
        <div style={{ padding: '24px 20px 20px', borderBottom: '1px solid rgba(255,255,255,.1)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 34, height: 34, background: 'linear-gradient(135deg,#2563eb,#0d9488)',
              borderRadius: 9, display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Shield size={18} color="#fff" />
            </div>
            <span style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 17, color: '#fff' }}>
              SafeMarket
            </span>
          </div>
        </div>

        <nav style={{ flex: 1, padding: '20px 12px', overflowY: 'auto' }}>
          {navItems.map(item => (
            <div
              key={item.label}
              onClick={() => setActiveNav(item.label)}
              style={{
                display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
                borderRadius: 10, marginBottom: 4, cursor: 'pointer', fontSize: 14, fontWeight: 500,
                transition: 'all .2s',
                background: activeNav === item.label ? 'rgba(255,255,255,.15)' : 'transparent',
                color: activeNav === item.label ? '#fff' : 'rgba(255,255,255,.6)',
              }}
              onMouseEnter={e => { if (activeNav !== item.label) e.currentTarget.style.background = 'rgba(255,255,255,.07)' }}
              onMouseLeave={e => { if (activeNav !== item.label) e.currentTarget.style.background = 'transparent' }}
            >
              {item.icon} {item.label}
            </div>
          ))}
        </nav>

        <div style={{ padding: 16, borderTop: '1px solid rgba(255,255,255,.1)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 36, height: 36, borderRadius: '50%',
              background: 'linear-gradient(135deg,#2563eb,#0d9488)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff', fontWeight: 700, fontSize: 14, flexShrink: 0,
            }}>
              {initials}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {displayName}
              </div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,.5)' }}>{displayRole}</div>
            </div>
            <button
              onClick={() => { logout(); nav('/') }}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(255,255,255,.5)', padding: 4 }}
              title="Cerrar sesión"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* ── MAIN ── */}
      <main style={{ marginLeft: 220, flex: 1, display: 'flex', flexDirection: 'column' }}>

        {/* Topbar */}
        <div style={{
          background: '#fff', borderBottom: '1px solid #e8edf3', padding: '0 28px',
          height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          position: 'sticky', top: 0, zIndex: 50, boxShadow: '0 1px 4px rgba(26,60,110,.06)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: '#f4f7fb', borderRadius: 10, padding: '8px 16px', width: 280 }}>
            <Search size={16} color="#94a3b8" />
            <input
              placeholder="Buscar transacciones..."
              style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: 14, color: '#475569', fontFamily: 'DM Sans,sans-serif', width: '100%' }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
              <Bell size={16} color="#64748b" />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: BRAND }}>{displayName}</div>
                <div style={{ fontSize: 11, color: '#94a3b8' }}>{displayRole}</div>
              </div>
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: `linear-gradient(135deg,${BRAND2},${SUCCESS})`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700, fontSize: 12 }}>
                {initials}
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div style={{ padding: 28, flex: 1 }}>

          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 24 }}>
            <div>
              <h1 style={{ fontFamily: 'Sora,sans-serif', fontSize: 22, fontWeight: 800, color: BRAND, marginBottom: 4 }}>
                Panel de Control
              </h1>
              <p style={{ color: '#64748b', fontSize: 14 }}>Monitoreo de transacciones y detección de fraude</p>
            </div>
            <div style={{ fontSize: 13, color: '#94a3b8', background: '#fff', padding: '8px 14px', borderRadius: 10, border: '1px solid #e8edf3' }}>
              {new Date().toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
            </div>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: 100, color: '#64748b' }}>
              <Activity size={40} style={{ margin: '0 auto 16px', display: 'block', color: BRAND2 }} />
              <div style={{ fontFamily: 'Sora,sans-serif', fontWeight: 600 }}>Cargando datos del servidor...</div>
            </div>
          ) : error ? (
            <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', padding: '16px 20px', borderRadius: 12, fontSize: 14 }}>
              ⚠️ {error}
            </div>
          ) : (
            <>
              {/* ── Métricas ── */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 16, marginBottom: 24 }}>
                {metrics.map((m, i) => (
                  <div key={i} style={{
                    background: '#fff', borderRadius: 14, padding: '18px 20px',
                    border: '1px solid #e8edf3', borderTop: `3px solid ${m.border}`,
                    boxShadow: '0 1px 4px rgba(26,60,110,.05)',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                      <div style={{ width: 38, height: 38, borderRadius: 10, background: m.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {m.icon}
                      </div>
                    </div>
                    <div style={{ fontFamily: 'Sora,sans-serif', fontSize: 24, fontWeight: 800, color: BRAND, marginBottom: 2 }}>
                      {m.val}
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 2 }}>{m.label}</div>
                    <div style={{ fontSize: 11, color: '#94a3b8' }}>{m.sub}</div>
                  </div>
                ))}
              </div>

              {/* ── Fila 1: Área + Gauge ── */}
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20, marginBottom: 20 }}>

                {/* Gráfica de área — Volumen diario de dinero */}
                <Card>
                  <CardTitle>Volumen de Dinero Procesado</CardTitle>
                  <p style={{ fontSize: 12, color: '#94a3b8', marginTop: -14, marginBottom: 16 }}>
                    Monto total vs monto fraudulento por día
                  </p>
                  {volumeByDate.length > 0 ? (
                    <ResponsiveContainer width="100%" height={220}>
                      <AreaChart data={volumeByDate} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                        <defs>
                          <linearGradient id="gradTotal" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={BRAND2} stopOpacity={0.15}/>
                            <stop offset="95%" stopColor={BRAND2} stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="gradFraude" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={DANGER} stopOpacity={0.15}/>
                            <stop offset="95%" stopColor={DANGER} stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1f70c0" />
                        <XAxis dataKey="fecha" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                        <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false}
                          tickFormatter={v => `$${(v/1000).toFixed(0)}K`} />
                        <Tooltip content={<BankTooltip />} />
                        <Legend iconType="circle" iconSize={8}
                          formatter={v => <span style={{ fontSize: 12, color: '#64748b' }}>{v === 'total' ? 'Volumen total' : 'Fraude detectado'}</span>} />
                        <Area type="monotone" dataKey="total" name="total" stroke={BRAND2} strokeWidth={2.5}
                          fill="url(#gradTotal)" dot={false} activeDot={{ r: 5, fill: BRAND2 }} />
                        <Area type="monotone" dataKey="fraudes" name="fraudes" stroke={DANGER} strokeWidth={2}
                          fill="url(#gradFraude)" dot={false} activeDot={{ r: 5, fill: DANGER }} />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8', fontSize: 13 }}>
                      Sin datos suficientes para graficar
                    </div>
                  )}
                </Card>

                {/* Gauge — Score de riesgo promedio */}
                <Card style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <CardTitle style={{ textAlign: 'center' }}>Índice de Riesgo Promedio</CardTitle>
                  <RiskGauge value={avgRiskScore} label="Basado en risk_score de transacciones" />
                  <div style={{ marginTop: 20, width: '100%' }}>
                    {[
                      { label: 'Bajo riesgo',  color: SUCCESS, pct: stats?.risk_distribution?.bajo  || 0 },
                      { label: 'Riesgo medio', color: WARN,    pct: stats?.risk_distribution?.medio || 0 },
                      { label: 'Alto riesgo',  color: DANGER,  pct: stats?.risk_distribution?.alto  || 0 },
                    ].map((r, i) => (
                      <div key={i} style={{ marginBottom: 8 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#64748b', marginBottom: 4 }}>
                          <span>{r.label}</span><strong style={{ color: r.color }}>{r.pct}%</strong>
                        </div>
                        <div style={{ height: 6, background: '#f1f5f9', borderRadius: 4, overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${r.pct}%`, background: r.color, borderRadius: 4, transition: 'width 1s ease' }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              {/* ── Fila 2: Donut + Barras horizontales ── */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: 20, marginBottom: 20 }}>

                {/* Donut — tipo de transacción */}
                <Card>
                  <CardTitle>Distribución por Tipo</CardTitle>
                  <p style={{ fontSize: 12, color: '#94a3b8', marginTop: -14, marginBottom: 12 }}>
                    Cantidad de operaciones por categoría
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
                    <ResponsiveContainer width={160} height={160}>
                      <PieChart>
                        <Pie
                          data={byType} cx="50%" cy="50%"
                          innerRadius={45} outerRadius={75}
                          dataKey="value" paddingAngle={3}
                        >
                          {byType.map((_, i) => (
                            <Cell key={i} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip
                          formatter={(val, name) => [val, typeLabels[name] || name]}
                          contentStyle={{ borderRadius: 10, fontSize: 12, border: '1px solid #e2e8f0' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div style={{ flex: 1 }}>
                      {byType.map((d, i) => {
                        const total = byType.reduce((s, x) => s + x.value, 0)
                        return (
                          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                            <div style={{ width: 10, height: 10, borderRadius: 2, background: DONUT_COLORS[i % DONUT_COLORS.length], flexShrink: 0 }} />
                            <div style={{ flex: 1 }}>
                              <div style={{ fontSize: 12, color: '#374151', fontWeight: 600 }}>
                                {typeLabels[d.name] || d.name}
                              </div>
                              <div style={{ fontSize: 11, color: '#94a3b8' }}>
                                {d.value} ops · {total ? ((d.value / total) * 100).toFixed(0) : 0}%
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </Card>

                {/* Barras horizontales — monto por categoría de comercio */}
                <Card>
                  <CardTitle>Monto por Categoría de Comercio</CardTitle>
                  <p style={{ fontSize: 12, color: '#94a3b8', marginTop: -14, marginBottom: 16 }}>
                    Top 6 categorías con mayor volumen procesado
                  </p>
                  <div>
                    {(() => {
                      const maxMonto = byCategory[0]?.monto || 1
                      return byCategory.map((d, i) => (
                        <div key={i} style={{ marginBottom: 14 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 5 }}>
                            <span style={{ color: '#374151', fontWeight: 600 }}>{d.categoria}</span>
                            <span style={{ color: BRAND, fontWeight: 700 }}>
                              ${Number(d.monto).toLocaleString('es', { maximumFractionDigits: 0 })}
                            </span>
                          </div>
                          <div style={{ height: 8, background: '#f1f5f9', borderRadius: 4, overflow: 'hidden' }}>
                            <div style={{
                              height: '100%',
                              width: `${(d.monto / maxMonto) * 100}%`,
                              background: `linear-gradient(90deg, ${BRAND2}, ${SUCCESS})`,
                              borderRadius: 4,
                              transition: 'width 1s ease',
                            }} />
                          </div>
                        </div>
                      ))
                    })()}
                  </div>
                </Card>
              </div>

              {/* ── Tabla transacciones recientes ── */}
              <Card style={{ padding: 0, overflow: 'hidden' }}>
                <div style={{ padding: '18px 24px', borderBottom: '1px solid #e8edf3', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 15, color: BRAND }}>
                      Transacciones Recientes
                    </span>
                    <span style={{ fontSize: 12, color: '#94a3b8', marginLeft: 10 }}>{transactions.length} registros</span>
                  </div>
                </div>

                <div style={{
                  display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 1.2fr',
                  padding: '10px 24px', background: '#f8fafc', borderBottom: '1px solid #e8edf3',
                  fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: .6,
                }}>
                  <span>ID / Comercio</span><span>Monto</span><span>Tipo</span>
                  <span>Estado</span><span>Riesgo</span><span>Fecha</span>
                </div>

                {transactions.slice(0, 10).map(tx => (
                  <div
                    key={tx.transaction_id}
                    style={{
                      display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 1.2fr',
                      padding: '13px 24px', borderBottom: '1px solid #f4f7fb',
                      alignItems: 'center', fontSize: 13, transition: 'background .15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = '#f8fafc'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 700, color: BRAND, fontFamily: 'monospace' }}>
                        {tx.transaction_id.slice(0, 8).toUpperCase()}...
                      </div>
                      <div style={{ fontSize: 11, color: '#94a3b8' }}>{tx.destination_merchant || 'Sin comercio'}</div>
                    </div>
                    <div style={{ fontWeight: 700, color: BRAND }}>
                      ${Number(tx.amount).toLocaleString('es', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      <span style={{ fontSize: 10, color: '#94a3b8', marginLeft: 2 }}>{tx.currency}</span>
                    </div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>{typeLabels[tx.transaction_type] || tx.transaction_type}</div>
                    <StatusBadge status={tx.status} />
                    <RiskBadge risk={tx.risk_level} />
                    <div style={{ fontSize: 11, color: '#64748b' }}>
                      {new Date(tx.created_at).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}
                    </div>
                  </div>
                ))}
              </Card>
            </>
          )}
        </div>
      </main>
    </div>
  )
}
