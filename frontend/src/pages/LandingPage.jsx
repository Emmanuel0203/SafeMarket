import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Shield, ShoppingBag, TrendingUp, Package, Truck,
  Brain, CheckCircle, Star, AlertTriangle, ChevronRight,
  Play, Twitter, Linkedin, Github, Facebook
} from 'lucide-react'

function DemoModal({ onClose }) {
  const nav = useNavigate()
  const [count, setCount] = useState(3)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(p => {
        const next = p + (100 / 30)
        if (next >= 100) {
          clearInterval(interval)
          setTimeout(() => nav('/register'), 200)
        }
        return next
      })
    }, 100)
    const timer = setInterval(() => setCount(c => c > 1 ? c - 1 : c), 1000)
    return () => { clearInterval(interval); clearInterval(timer) }
  }, [])

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: 'rgba(15,23,42,.85)', backdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <div style={{
        background: '#fff', borderRadius: 24, padding: '52px 48px',
        maxWidth: 460, width: '90%', textAlign: 'center',
        boxShadow: '0 40px 100px rgba(0,0,0,.3)',
      }}>
        <div style={{
          width: 72, height: 72, background: 'linear-gradient(135deg,#2563eb,#0d9488)',
          borderRadius: 20, display: 'flex', alignItems: 'center',
          justifyContent: 'center', margin: '0 auto 24px',
        }}>
          <Shield size={36} color="#fff" />
        </div>
        <h2 style={{ fontFamily: 'Sora,sans-serif', fontSize: 24, fontWeight: 800,
          color: '#0f172a', marginBottom: 10 }}>
          Preparando tu Demo
        </h2>
        <p style={{ color: '#64748b', fontSize: 15, marginBottom: 36, lineHeight: 1.6 }}>
          Estamos configurando tu entorno de demostración con datos reales de SafeMarket.
        </p>

        {/* Progress bar */}
        <div style={{ background: '#f1f5f9', borderRadius: 999, height: 8, marginBottom: 16, overflow: 'hidden' }}>
          <div style={{
            height: '100%', borderRadius: 999,
            background: 'linear-gradient(90deg,#2563eb,#0d9488)',
            width: `${progress}%`, transition: 'width .1s linear',
          }} />
        </div>

        <p style={{ color: '#94a3b8', fontSize: 13 }}>
          Redirigiendo en <strong style={{ color: '#2563eb' }}>{count}</strong> segundos...
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 24, marginTop: 28 }}>
          {['✓ Sin tarjeta de crédito', '✓ Acceso inmediato', '✓ Datos de prueba incluidos'].map(t => (
            <span key={t} style={{ fontSize: 12, color: '#10b981', fontWeight: 600 }}>{t}</span>
          ))}
        </div>

        <button onClick={onClose} style={{
          marginTop: 24, background: 'none', border: 'none',
          color: '#94a3b8', fontSize: 13, cursor: 'pointer',
          fontFamily: 'DM Sans,sans-serif',
        }}>Cancelar</button>
      </div>
    </div>
  )
}

const btn = {
  primary: {
    background: 'linear-gradient(135deg,#2563eb,#1d4ed8)',
    color: '#fff', padding: '12px 26px', borderRadius: 12,
    fontSize: 15, fontWeight: 700, fontFamily: 'Sora,sans-serif',
    border: 'none', cursor: 'pointer', display: 'inline-flex',
    alignItems: 'center', gap: 8,
  },
  outline: {
    background: 'transparent', color: '#2563eb',
    padding: '12px 26px', borderRadius: 12, fontSize: 15,
    fontWeight: 700, fontFamily: 'Sora,sans-serif',
    border: '2px solid #2563eb', cursor: 'pointer',
    display: 'inline-flex', alignItems: 'center', gap: 8,
  },
  outlineWhite: {
    background: 'transparent', color: '#fff',
    padding: '14px 30px', borderRadius: 12, fontSize: 16,
    fontWeight: 700, fontFamily: 'Sora,sans-serif',
    border: '2px solid rgba(255,255,255,.5)', cursor: 'pointer',
  },
}

const NetworkSVG = () => (
  <svg width="100%" height="100%" viewBox="0 0 500 380"
    style={{ position: 'absolute', inset: 0, opacity: .55 }}>
    {[[60,80],[180,40],[300,90],[420,60],[70,190],[200,160],[340,180],[450,200],
      [100,300],[230,270],[370,310],[460,290]].map(([x,y],i)=>(
      <circle key={i} cx={x} cy={y} r={5} fill="#60a5fa" />
    ))}
    {[[0,1],[1,2],[2,3],[4,5],[5,6],[6,7],[8,9],[9,10],[10,11],
      [0,4],[1,5],[2,6],[3,7],[4,8],[5,9],[6,10],[7,11],[1,6],[5,10]].map(([a,b],i)=>{
      const pts=[[60,80],[180,40],[300,90],[420,60],[70,190],[200,160],[340,180],
                 [450,200],[100,300],[230,270],[370,310],[460,290]]
      return <line key={i} x1={pts[a][0]} y1={pts[a][1]} x2={pts[b][0]} y2={pts[b][1]}
        stroke="#60a5fa" strokeWidth={1} opacity={.3}/>
    })}
  </svg>
)

export default function LandingPage() {
  const nav = useNavigate()
  const [showDemo, setShowDemo] = useState(false)
  const scrollTo = id => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })

  return (
    <div style={{ fontFamily: 'DM Sans,sans-serif' }}>
      {showDemo && <DemoModal onClose={() => setShowDemo(false)} />}

      {/* ── NAV ─────────────────────────────────────────────────────────── */}
      <nav style={{
        position:'fixed',top:0,left:0,right:0,zIndex:1000,
        background:'rgba(255,255,255,.96)',backdropFilter:'blur(14px)',
        borderBottom:'1px solid #e2e8f0',
      }}>
        <div style={{ maxWidth:1200,margin:'0 auto',padding:'0 24px',height:64,
          display:'flex',alignItems:'center',justifyContent:'space-between' }}>
          <div style={{ display:'flex',alignItems:'center',gap:10,
            fontFamily:'Sora,sans-serif',fontWeight:700,fontSize:20,color:'#0f172a' }}>
            <div style={{ width:36,height:36,background:'linear-gradient(135deg,#2563eb,#0d9488)',
              borderRadius:10,display:'flex',alignItems:'center',justifyContent:'center' }}>
              <Shield size={18} color="#fff" />
            </div>
            SafeMarket
          </div>
          <ul style={{ display:'flex',gap:28,listStyle:'none' }}>
            {[['Inicio','inicio'],['Soluciones','soluciones'],['Clientes','clientes'],
              ['Precios','precios'],['Acerca de','acerca'],['Contacto','contacto']].map(([l,id])=>(
              <li key={id}>
                <span onClick={()=>scrollTo(id)}
                  style={{ fontSize:15,color:'#475569',fontWeight:500,cursor:'pointer' }}>{l}</span>
              </li>
            ))}
          </ul>
          <button style={btn.primary} onClick={()=>nav('/login')}>Iniciar sesión</button>
        </div>
      </nav>

      {/* ── HERO ────────────────────────────────────────────────────────── */}
      <section id="inicio" style={{
        minHeight:'100vh',paddingTop:64,
        background:'linear-gradient(135deg,#f0fdf9 0%,#eff6ff 50%,#f0fdf4 100%)',
        display:'flex',alignItems:'center',
      }}>
        <div style={{ maxWidth:1200,margin:'0 auto',padding:'80px 24px',
          display:'grid',gridTemplateColumns:'1fr 1fr',gap:60,alignItems:'center' }}>
          <div>
            <h1 style={{ fontFamily:'Sora,sans-serif',
              fontSize:'clamp(38px,5vw,58px)',fontWeight:800,
              lineHeight:1.1,color:'#0f172a',marginBottom:24 }}>
              Comercio Digital Seguro para la Era Moderna
            </h1>
            <p style={{ fontSize:18,color:'#475569',lineHeight:1.75,marginBottom:40 }}>
              Potencia tu marketplace con prevención de fraude impulsada por IA,
              transacciones verificadas y detección de riesgos en tiempo real.
              Confiado por más de 500 empresas en todo el mundo.
            </p>
            <div style={{ display:'flex',gap:16,flexWrap:'wrap' }}>
              <button style={btn.primary} onClick={() => setShowDemo(true)}>
                Registrate <ChevronRight size={16}/>
              </button>
              <button style={btn.outline} onClick={()=>scrollTo('precios')}>
                <Play size={15}/> Ver Planes
              </button>
            </div>
          </div>
          <div style={{ position:'relative' }}>
            <div style={{
              height:420,background:'linear-gradient(135deg,#1e293b,#0f172a 60%,#1e3a5f)',
              borderRadius:20,overflow:'hidden',position:'relative',
              boxShadow:'0 30px 80px rgba(0,0,0,.25)',
            }}>
              <NetworkSVG/>
              <div style={{ position:'absolute',inset:0,
                background:'radial-gradient(circle at 50% 50%,rgba(37,99,235,.2),transparent 70%)' }}/>
            </div>
            {/* Badge disponibilidad */}
            <div style={{
              position:'absolute',top:20,right:20,background:'#fff',borderRadius:12,
              padding:'10px 16px',display:'flex',alignItems:'center',gap:8,
              boxShadow:'0 4px 20px rgba(0,0,0,.15)',fontSize:14,fontWeight:600,
            }}>
              <span style={{ width:10,height:10,background:'#10b981',borderRadius:'50%',flexShrink:0 }}/>
              99.9% Disponibilidad
            </div>
            {/* Badge transacciones */}
            <div style={{
              position:'absolute',bottom:30,left:30,background:'#fff',borderRadius:16,
              padding:'16px 22px',boxShadow:'0 8px 30px rgba(0,0,0,.18)',
            }}>
              <div style={{ fontFamily:'Sora,sans-serif',fontSize:30,fontWeight:800,color:'#2563eb' }}>+1M</div>
              <div style={{ fontSize:13,color:'#64748b',marginTop:4 }}>Transacciones Seguras</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── INDUSTRIAS ──────────────────────────────────────────────────── */}
      <section id="soluciones" style={{ padding:'100px 24px' }}>
        <div style={{ maxWidth:1200,margin:'0 auto' }}>
          <h2 style={{ fontFamily:'Sora,sans-serif',fontSize:'clamp(26px,4vw,40px)',
            fontWeight:700,textAlign:'center',color:'#0f172a',marginBottom:16 }}>
            Industrias que Protegemos
          </h2>
          <p style={{ fontSize:18,color:'#64748b',textAlign:'center',marginBottom:64 }}>
            Soluciones de seguridad confiables para diversos sectores empresariales
          </p>
          <div style={{ display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:40 }}>
            {[
              { icon:<ShoppingBag size={32} color="#2563eb"/>, bg:'#eff6ff',
                title:'Plataformas E-commerce', desc:'Procesamiento seguro de pagos para minoristas online' },
              { icon:<TrendingUp size={32} color="#10b981"/>, bg:'#f0fdf4',
                title:'Startups Fintech', desc:'Detección de fraude para servicios financieros' },
              { icon:<Package size={32} color="#8b5cf6"/>, bg:'#f5f3ff',
                title:'Marketplaces Online', desc:'Transacciones verificadas para plataformas P2P' },
              { icon:<Truck size={32} color="#f59e0b"/>, bg:'#fffbeb',
                title:'Empresas de Logística', desc:'Soluciones de pago y seguimiento seguras' },
            ].map((item,i)=>(
              <div key={i} style={{ textAlign:'center' }}>
                <div style={{ width:72,height:72,borderRadius:20,background:item.bg,
                  display:'flex',alignItems:'center',justifyContent:'center',margin:'0 auto 20px' }}>
                  {item.icon}
                </div>
                <h3 style={{ fontFamily:'Sora,sans-serif',fontWeight:700,fontSize:16,marginBottom:10 }}>
                  {item.title}
                </h3>
                <p style={{ color:'#64748b',fontSize:14,lineHeight:1.65 }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── LOGOS ───────────────────────────────────────────────────────── */}
      <div id="clientes" style={{ padding:'44px 24px',borderTop:'1px solid #e2e8f0',borderBottom:'1px solid #e2e8f0' }}>
        <p style={{ textAlign:'center',fontSize:11,letterSpacing:2,color:'#94a3b8',
          fontWeight:700,textTransform:'uppercase',marginBottom:28 }}>
          Confiado por Empresas Líderes
        </p>
        <div style={{ maxWidth:1100,margin:'0 auto',display:'flex',
          justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:24 }}>
          {['TECHCORP','NEXUS','DIGITAL','QUANTUM','VERTEX','SYNERGY'].map(n=>(
            <span key={n} style={{ fontFamily:'Sora,sans-serif',fontWeight:700,
              fontSize:18,color:'#cbd5e1',letterSpacing:1 }}>{n}</span>
          ))}
        </div>
      </div>

      {/* ── FEATURES ────────────────────────────────────────────────────── */}
      <section id="acerca" style={{ padding:'100px 24px',background:'#f8fafc' }}>
        <div style={{ maxWidth:1200,margin:'0 auto' }}>
          <h2 style={{ fontFamily:'Sora,sans-serif',fontSize:'clamp(26px,4vw,40px)',
            fontWeight:700,textAlign:'center',color:'#0f172a',marginBottom:16 }}>
            Qué Nos Hace Diferentes
          </h2>
          <p style={{ fontSize:18,color:'#64748b',textAlign:'center',marginBottom:60 }}>
            Funciones de seguridad líderes en la industria diseñadas para proteger su negocio
            y generar confianza con los clientes
          </p>
          <div style={{ display:'grid',gridTemplateColumns:'1fr 1fr',gap:24 }}>
            {[
              { icon:<Brain size={26} color="#fff"/>, bg:'#2563eb',
                title:'Detección de Riesgos con IA',
                desc:'Algoritmos avanzados de aprendizaje automático analizan patrones de transacciones en tiempo real para identificar y prevenir actividades fraudulentas antes de que ocurran.' },
              { icon:<CheckCircle size={26} color="#fff"/>, bg:'#10b981',
                title:'Transacciones Verificadas',
                desc:'Sistema de verificación multicapa que garantiza que cada transacción sea autenticada, brindando tranquilidad tanto a compradores como vendedores.' },
              { icon:<Star size={26} color="#fff"/>, bg:'#8b5cf6',
                title:'Puntuación de Reputación',
                desc:'Sistema integral de reputación que rastrea el comportamiento del usuario y el historial de transacciones para generar confianza en todo su marketplace.' },
              { icon:<Shield size={26} color="#fff"/>, bg:'#0d9488',
                title:'Prevención de Fraude',
                desc:'Monitoreo 24/7 con alertas instantáneas y respuestas automatizadas a actividades sospechosas, reduciendo el fraude en un 99.9%.' },
            ].map((f,i)=>(
              <div key={i} style={{
                background:'#fff',borderRadius:20,padding:'36px 40px',
                boxShadow:'0 2px 16px rgba(0,0,0,.06)',transition:'all .25s',
              }}
                onMouseEnter={e=>{e.currentTarget.style.transform='translateY(-5px)';e.currentTarget.style.boxShadow='0 16px 48px rgba(0,0,0,.12)'}}
                onMouseLeave={e=>{e.currentTarget.style.transform='';e.currentTarget.style.boxShadow='0 2px 16px rgba(0,0,0,.06)'}}>
                <div style={{ width:54,height:54,borderRadius:15,background:f.bg,
                  display:'flex',alignItems:'center',justifyContent:'center',marginBottom:20 }}>
                  {f.icon}
                </div>
                <h3 style={{ fontFamily:'Sora,sans-serif',fontWeight:700,fontSize:20,
                  color:'#0f172a',marginBottom:14 }}>{f.title}</h3>
                <p style={{ color:'#64748b',lineHeight:1.75,fontSize:15 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── STATS ───────────────────────────────────────────────────────── */}
      <section style={{ padding:'100px 24px',background:'linear-gradient(135deg,#2563eb,#0d9488)' }}>
        <div style={{ maxWidth:1200,margin:'0 auto' }}>
          <h2 style={{ fontFamily:'Sora,sans-serif',fontSize:'clamp(26px,4vw,40px)',
            fontWeight:700,textAlign:'center',color:'#fff',marginBottom:14 }}>
            Confiado por Líderes de la Industria
          </h2>
          <p style={{ fontSize:18,color:'rgba(255,255,255,.8)',textAlign:'center',marginBottom:60 }}>
            Nuestra plataforma ofrece resultados medibles para empresas en todo el mundo
          </p>
          <div style={{ display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:20 }}>
            {[
              { icon:<Shield size={28}/>, val:'+1M', label:'Transacciones Seguras', sub:'Procesadas mensualmente' },
              { icon:<CheckCircle size={28}/>, val:'+500', label:'Empresas Protegidas', sub:'En 40 países' },
              { icon:<TrendingUp size={28}/>, val:'99.9%', label:'Reducción de Fraude', sub:'Mejora promedio del cliente' },
              { icon:<AlertTriangle size={28}/>, val:'<50ms', label:'Tiempo de Respuesta', sub:'Verificación en tiempo real' },
            ].map((s,i)=>(
              <div key={i} style={{
                background:'rgba(255,255,255,.15)',backdropFilter:'blur(10px)',
                borderRadius:20,padding:'32px 24px',textAlign:'center',
                border:'1px solid rgba(255,255,255,.2)',
              }}>
                <div style={{ color:'rgba(255,255,255,.8)',marginBottom:16 }}>{s.icon}</div>
                <div style={{ fontFamily:'Sora,sans-serif',fontSize:38,fontWeight:800,
                  color:'#fff',marginBottom:8 }}>{s.val}</div>
                <div style={{ color:'rgba(255,255,255,.95)',fontWeight:600,marginBottom:6 }}>{s.label}</div>
                <div style={{ color:'rgba(255,255,255,.6)',fontSize:13 }}>{s.sub}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── PRICING ─────────────────────────────────────────────────────── */}
      <section id="precios" style={{ padding:'100px 24px' }}>
        <div style={{ maxWidth:1200,margin:'0 auto' }}>
          <h2 style={{ fontFamily:'Sora,sans-serif',fontSize:'clamp(26px,4vw,40px)',
            fontWeight:700,textAlign:'center',color:'#0f172a',marginBottom:16 }}>
            Precios Flexibles para Cada Negocio
          </h2>
          <p style={{ fontSize:18,color:'#64748b',textAlign:'center',marginBottom:60 }}>
            Elija el plan que se ajuste a sus necesidades. Actualice o reduzca en cualquier momento.
          </p>
          <div style={{ display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:24,maxWidth:1100,margin:'0 auto' }}>

            {/* Starter */}
            <div style={{ border:'1px solid #e2e8f0',borderRadius:20,padding:40 }}>
              <h3 style={{ fontFamily:'Sora,sans-serif',fontWeight:700,fontSize:22,marginBottom:8 }}>Starter</h3>
              <p style={{ color:'#64748b',fontSize:14,marginBottom:28 }}>Perfecto para pequeñas empresas y startups</p>
              <div style={{ fontFamily:'Sora,sans-serif',fontSize:40,fontWeight:800,color:'#0f172a',marginBottom:28 }}>
                $299<span style={{ fontSize:16,fontWeight:400,color:'#64748b' }}>/mes</span>
              </div>
              <button style={{ ...btn.primary,width:'100%',justifyContent:'center',padding:'14px',borderRadius:12,marginBottom:28 }}
                onClick={()=>nav('/register')}>
                Comenzar Prueba Gratis →
              </button>
              {['Hasta 10,000 transacciones/mes','Detección básica de fraude','Soporte por email','Acceso al dashboard'].map(f=>(
                <div key={f} style={{ display:'flex',alignItems:'center',gap:10,marginBottom:14 }}>
                  <CheckCircle size={16} color="#10b981"/> <span style={{ fontSize:14,color:'#475569' }}>{f}</span>
                </div>
              ))}
            </div>

            {/* Growth - Featured */}
            <div style={{
              background:'linear-gradient(135deg,#2563eb,#1d4ed8)',borderRadius:20,
              padding:40,transform:'scale(1.04)',boxShadow:'0 20px 60px rgba(37,99,235,.4)',color:'#fff',
            }}>
              <h3 style={{ fontFamily:'Sora,sans-serif',fontWeight:700,fontSize:22,marginBottom:8 }}>Growth</h3>
              <p style={{ color:'rgba(255,255,255,.8)',fontSize:14,marginBottom:28 }}>Ideal para empresas en crecimiento</p>
              <div style={{ fontFamily:'Sora,sans-serif',fontSize:40,fontWeight:800,marginBottom:28 }}>
                $799<span style={{ fontSize:16,fontWeight:400,opacity:.7 }}>/mes</span>
              </div>
              <button style={{ background:'#fff',color:'#2563eb',padding:'14px',borderRadius:12,
                width:'100%',fontWeight:700,fontSize:15,fontFamily:'Sora,sans-serif',marginBottom:28 }}
                onClick={()=>nav('/register')}>
                Comenzar Ahora →
              </button>
              {['Hasta 100,000 transacciones/mes','Detección avanzada de riesgos con IA',
                'Soporte prioritario','Dashboard personalizado','Integraciones API'].map(f=>(
                <div key={f} style={{ display:'flex',alignItems:'center',gap:10,marginBottom:14 }}>
                  <CheckCircle size={16} color="rgba(255,255,255,.8)"/>
                  <span style={{ fontSize:14,color:'rgba(255,255,255,.9)' }}>{f}</span>
                </div>
              ))}
            </div>

            {/* Enterprise */}
            <div style={{ border:'1px solid #e2e8f0',borderRadius:20,padding:40 }}>
              <h3 style={{ fontFamily:'Sora,sans-serif',fontWeight:700,fontSize:22,marginBottom:8 }}>Enterprise</h3>
              <p style={{ color:'#64748b',fontSize:14,marginBottom:28 }}>Para operaciones a gran escala</p>
              <div style={{ fontFamily:'Sora,sans-serif',fontSize:36,fontWeight:800,color:'#0f172a',marginBottom:28 }}>
                Personalizado
              </div>
              <button style={{ ...btn.primary,width:'100%',justifyContent:'center',padding:'14px',borderRadius:12,marginBottom:28 }}
                onClick={()=>scrollTo('contacto')}>
                Contactar Ventas →
              </button>
              {['Transacciones ilimitadas','Suite completa de IA','Soporte dedicado 24/7',
                'Integraciones personalizadas','SLA garantizado'].map(f=>(
                <div key={f} style={{ display:'flex',alignItems:'center',gap:10,marginBottom:14 }}>
                  <CheckCircle size={16} color="#10b981"/> <span style={{ fontSize:14,color:'#475569' }}>{f}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────────────────── */}
      <section id="contacto" style={{
        padding:'100px 24px',textAlign:'center',
        background:'linear-gradient(135deg,#2563eb 0%,#0d9488 100%)',
      }}>
        <div style={{ maxWidth:760,margin:'0 auto' }}>
          <h2 style={{ fontFamily:'Sora,sans-serif',fontSize:'clamp(30px,5vw,52px)',
            fontWeight:800,color:'#fff',marginBottom:20 }}>
            ¿Listo para Asegurar su Marketplace?
          </h2>
          <p style={{ color:'rgba(255,255,255,.85)',fontSize:18,lineHeight:1.7,marginBottom:40 }}>
            Únase a cientos de empresas que protegen a sus clientes con la plataforma
            de seguridad líder en la industria de SafeMarket
          </p>
          <div style={{ display:'flex',gap:16,justifyContent:'center',flexWrap:'wrap',marginBottom:48 }}>
            <button style={{ background:'#fff',color:'#2563eb',padding:'16px 34px',
              borderRadius:12,fontWeight:700,fontSize:16,fontFamily:'Sora,sans-serif' }}
              onClick={()=>nav('/register')}>
              Comenzar Prueba Gratis →
            </button>
            <button style={btn.outlineWhite} onClick={()=>nav('/register')}>
              Programar una Demo
            </button>
          </div>
          <div style={{ display:'flex',justifyContent:'center',gap:32,flexWrap:'wrap' }}>
            {['Comience a proteger su negocio en minutos',
              'No se requiere tarjeta de crédito para la prueba',
              'Acceda a su dashboard personalizado',
              'Únase a más de 500 empresas protegidas'].map(t=>(
              <div key={t} style={{ display:'flex',alignItems:'center',gap:8,
                color:'rgba(255,255,255,.9)',fontSize:14 }}>
                <CheckCircle size={16} color="#10b981"/> {t}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FOOTER ──────────────────────────────────────────────────────── */}
      <footer style={{ background:'#0f172a',color:'#94a3b8',padding:'64px 24px 32px' }}>
        <div style={{ maxWidth:1200,margin:'0 auto' }}>
          <div style={{ display:'grid',gridTemplateColumns:'2fr 1fr 1fr 1fr 1fr',gap:48,marginBottom:48 }}>
            <div>
              <div style={{ display:'flex',alignItems:'center',gap:10,marginBottom:16,
                color:'#fff',fontFamily:'Sora,sans-serif',fontWeight:700,fontSize:18 }}>
                <div style={{ width:32,height:32,background:'linear-gradient(135deg,#2563eb,#0d9488)',
                  borderRadius:9,display:'flex',alignItems:'center',justifyContent:'center' }}>
                  <Shield size={16} color="#fff"/>
                </div>
                SafeMarket
              </div>
              <p style={{ fontSize:14,lineHeight:1.7,maxWidth:260 }}>
                Protegiendo el comercio digital con soluciones de seguridad impulsadas por IA,
                confiadas por empresas en todo el mundo.
              </p>
              <div style={{ display:'flex',gap:12,marginTop:24 }}>
                {[<Twitter size={16}/>,<Linkedin size={16}/>,<Github size={16}/>,<Facebook size={16}/>].map((icon,i)=>(
                  <div key={i} style={{ width:38,height:38,background:'rgba(255,255,255,.08)',
                    borderRadius:10,display:'flex',alignItems:'center',justifyContent:'center',cursor:'pointer' }}
                    onMouseEnter={e=>e.currentTarget.style.background='rgba(255,255,255,.16)'}
                    onMouseLeave={e=>e.currentTarget.style.background='rgba(255,255,255,.08)'}>
                    {icon}
                  </div>
                ))}
              </div>
            </div>
            {[
              { title:'Producto', links:['Características','Precios','Seguridad','Enterprise','Documentación API','Integraciones'] },
              { title:'Empresa', links:['Acerca de','Carreras','Blog','Prensa','Socios','Contacto'] },
              { title:'Recursos', links:['Centro de Ayuda','Casos de Estudio','Docs para Desarrolladores','Webinars','Comunidad','Estado'] },
              { title:'Legal', links:['Privacidad','Términos de Servicio','Cookies','GDPR','Cumplimiento','Licencias'] },
            ].map(col=>(
              <div key={col.title}>
                <div style={{ color:'#fff',fontWeight:600,fontSize:15,marginBottom:20,fontFamily:'Sora,sans-serif' }}>
                  {col.title}
                </div>
                {col.links.map(l=>(
                  <span key={l} style={{ display:'block',fontSize:14,color:'#94a3b8',marginBottom:12,cursor:'pointer' }}
                    onMouseEnter={e=>e.currentTarget.style.color='#fff'}
                    onMouseLeave={e=>e.currentTarget.style.color='#94a3b8'}>{l}</span>
                ))}
              </div>
            ))}
          </div>
          <div style={{ borderTop:'1px solid rgba(255,255,255,.08)',paddingTop:28,
            display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:16 }}>
            <span style={{ fontSize:14 }}>© 2026 SafeMarket. Todos los derechos reservados.</span>
            <div style={{ display:'flex',gap:24,fontSize:14 }}>
              {['Privacidad','Términos','Cookies'].map(l=>(
                <span key={l} style={{ cursor:'pointer' }}>{l}</span>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
