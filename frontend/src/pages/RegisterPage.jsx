import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Shield, Mail, Lock, Building2, Eye, EyeOff, ArrowLeft } from 'lucide-react'

export default function RegisterPage() {
  const nav = useNavigate()
  const { register, loading } = useAuth()
  // ✅ Quitado 'name' porque la tabla users no tiene ese campo
  const [form, setForm] = useState({ email: '', password: '', company: '', plan: 'Starter' })
  const [showPass, setShowPass] = useState(false)
  const [error, setError] = useState('')

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))
  const focus = e => e.target.style.borderColor = '#2563eb'
  const blur  = e => e.target.style.borderColor = '#e2e8f0'

  const submit = async e => {
    e.preventDefault()
    setError('')
    const r = await register(form)
    if (r.success) nav('/dashboard')
    else setError(r.error)
  }

  const base = {
    width: '100%', padding: '12px 16px 12px 44px',
    border: '1.5px solid #e2e8f0', borderRadius: 12, fontSize: 15,
    outline: 'none', fontFamily: 'DM Sans,sans-serif',
    transition: 'border-color .2s', boxSizing: 'border-box',
  }
  const label = { display: 'block', fontSize: 14, fontWeight: 600, color: '#374151', marginBottom: 6 }
  const wrap  = { position: 'relative', marginBottom: 18 }
  const ic    = { position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }

  return (
    <div style={{
      minHeight: '100vh', background: 'linear-gradient(135deg,#eff6ff,#f0fdf9)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, fontFamily: 'DM Sans,sans-serif'
    }}>
      <div style={{
        background: '#fff', borderRadius: 24, padding: '48px 40px', width: '100%',
        maxWidth: 480, boxShadow: '0 20px 60px rgba(0,0,0,.08)'
      }}>

        <button onClick={() => nav('/')} style={{
          background: 'none', border: 'none',
          display: 'flex', alignItems: 'center', gap: 6, color: '#64748b', fontSize: 14,
          cursor: 'pointer', marginBottom: 28, padding: 0, fontFamily: 'DM Sans,sans-serif'
        }}>
          <ArrowLeft size={16} /> Volver al inicio
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, justifyContent: 'center', marginBottom: 28 }}>
          <div style={{
            width: 40, height: 40, background: 'linear-gradient(135deg,#2563eb,#0d9488)',
            borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Shield size={22} color="#fff" />
          </div>
          <span style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 20, color: '#0f172a' }}>SafeMarket</span>
        </div>

        <h1 style={{
          fontFamily: 'Sora,sans-serif', fontSize: 26, fontWeight: 700, color: '#0f172a',
          textAlign: 'center', marginBottom: 8
        }}>Crear Cuenta</h1>
        <p style={{ color: '#64748b', textAlign: 'center', marginBottom: 32, fontSize: 15 }}>
          Comienza tu prueba gratuita hoy
        </p>

        {error && (
          <div style={{
            background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626',
            padding: '12px 16px', borderRadius: 10, fontSize: 14, marginBottom: 20
          }}>{error}</div>
        )}

        <form onSubmit={submit}>
          {/* ✅ Campo 'Nombre completo' eliminado — no existe en la BD */}

          <label style={label}>Correo electrónico</label>
          <div style={wrap}>
            <Mail size={18} style={ic} />
            <input
              style={base} type="email" placeholder="tu@empresa.com"
              value={form.email} onChange={set('email')} onFocus={focus} onBlur={blur} required
            />
          </div>

          <label style={label}>Empresa</label>
          <div style={wrap}>
            <Building2 size={18} style={ic} />
            <input
              style={base} type="text" placeholder="Mi Empresa S.A.S"
              value={form.company} onChange={set('company')} onFocus={focus} onBlur={blur}
            />
          </div>

          <label style={label}>Plan</label>
          <select
            style={{ ...base, padding: '12px 16px', marginBottom: 18 }}
            value={form.plan} onChange={set('plan')} onFocus={focus} onBlur={blur}
          >
            <option value="Starter">Starter – $299/mes</option>
            <option value="Growth">Growth – $799/mes</option>
            <option value="Enterprise">Enterprise – Personalizado</option>
          </select>

          <label style={label}>Contraseña</label>
          {/* ✅ Mensaje actualizado: el backend exige mín. 8 chars, 1 mayúscula y 1 número */}
          <div style={{ ...wrap, marginBottom: 8 }}>
            <Lock size={18} style={ic} />
            <input
              style={base}
              type={showPass ? 'text' : 'password'}
              placeholder="Mín. 8 caracteres"
              value={form.password} onChange={set('password')} onFocus={focus} onBlur={blur}
              required minLength={8}
            />
            <button
              type="button" onClick={() => setShowPass(v => !v)}
              style={{
                position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 0
              }}
            >
              {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          {/* ✅ Hint visible con los requisitos reales del backend */}
          <p style={{ fontSize: 12, color: '#94a3b8', marginBottom: 24, marginTop: 0 }}>
            Debe contener al menos 1 mayúscula y 1 número.
          </p>

          <button
            type="submit" disabled={loading}
            style={{
              width: '100%', background: 'linear-gradient(135deg,#2563eb,#1d4ed8)',
              color: '#fff', padding: '14px', borderRadius: 12, fontSize: 16, fontWeight: 700,
              fontFamily: 'Sora,sans-serif', border: 'none', cursor: 'pointer',
              opacity: loading ? 0.7 : 1, transition: 'opacity .2s'
            }}
          >
            {loading ? 'Creando cuenta...' : 'Crear Cuenta Gratis'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 24, fontSize: 14, color: '#64748b' }}>
          ¿Ya tienes cuenta?{' '}
          <Link to="/login" style={{ color: '#2563eb', fontWeight: 600 }}>Iniciar sesión</Link>
        </p>
      </div>
    </div>
  )
}
