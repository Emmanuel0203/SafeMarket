/**
 * SafeMarket SDK v1.0.0
 * Sistema de detección de fraude embebible
 * 
 * USO:
 * <script src="https://safemarket.co/widget.js" data-api-key="sm_live_xxx"></script>
 * 
 * O via NPM:
 * import SafeMarket from 'safemarket-sdk'
 * const sm = new SafeMarket({ apiKey: 'sm_live_xxx' })
 */

(function (global) {
  'use strict';

  // ── Configuración base ─────────────────────────────────────────────────
  const DEFAULT_CONFIG = {
    apiUrl:   'http://localhost:8000',   // En producción: https://api.safemarket.co
    position: 'bottom-right',            // Posición del panel de alertas
    theme:    'light',                   // light | dark
    language: 'es',                      // es | en
    autoInit: true,                      // Iniciar automáticamente al cargar
  };

  // ── Estilos del SDK ────────────────────────────────────────────────────
  const STYLES = `
    /* ── Reset base ── */
    .sm-widget * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; }

    /* ── Badge de riesgo ── */
    .sm-badge {
      display: inline-flex; align-items: center; gap: 6px;
      padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 700;
      cursor: default; transition: all 0.2s; border: none; vertical-align: middle;
    }
    .sm-badge-low    { background: #dcfce7; color: #16a34a; }
    .sm-badge-medium { background: #fef9c3; color: #ca8a04; }
    .sm-badge-high   { background: #fee2e2; color: #dc2626; }
    .sm-badge-loading { background: #f1f5f9; color: #94a3b8; }
    .sm-badge-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
    .sm-badge:hover { opacity: 0.85; transform: scale(1.03); }

    /* ── Panel de alertas flotante ── */
    .sm-panel {
      position: fixed; z-index: 999999;
      width: 340px; max-height: 480px;
      background: #fff; border-radius: 16px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.15);
      border: 1px solid #e2e8f0;
      display: flex; flex-direction: column;
      transition: all 0.3s ease; overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
    }
    .sm-panel.sm-bottom-right { bottom: 20px; right: 20px; }
    .sm-panel.sm-bottom-left  { bottom: 20px; left: 20px; }
    .sm-panel.sm-top-right    { top: 20px; right: 20px; }
    .sm-panel.sm-top-left     { top: 20px; left: 20px; }
    .sm-panel.sm-collapsed { height: 56px !important; max-height: 56px; }

    .sm-panel-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 14px 16px; background: #1a3c6e; color: #fff;
      cursor: pointer; user-select: none; flex-shrink: 0;
    }
    .sm-panel-header-left { display: flex; align-items: center; gap: 10px; }
    .sm-panel-logo { width: 22px; height: 22px; background: linear-gradient(135deg, #2563eb, #0d9488); border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; }
    .sm-panel-title { font-size: 14px; font-weight: 700; }
    .sm-panel-badge-count {
      background: #ef4444; color: #fff; border-radius: 10px;
      padding: 2px 7px; font-size: 11px; font-weight: 700; min-width: 20px; text-align: center;
    }
    .sm-panel-toggle { background: none; border: none; color: rgba(255,255,255,0.8); cursor: pointer; font-size: 16px; padding: 2px 6px; border-radius: 6px; }
    .sm-panel-toggle:hover { background: rgba(255,255,255,0.15); }

    .sm-panel-body { overflow-y: auto; flex: 1; }

    .sm-alert-item {
      padding: 12px 16px; border-bottom: 1px solid #f1f5f9;
      display: flex; gap: 12px; align-items: flex-start;
      transition: background 0.15s; cursor: default;
    }
    .sm-alert-item:hover { background: #f8fafc; }
    .sm-alert-item:last-child { border-bottom: none; }
    .sm-alert-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
    .sm-alert-icon-high   { background: #fee2e2; }
    .sm-alert-icon-medium { background: #fef9c3; }
    .sm-alert-icon-low    { background: #dcfce7; }
    .sm-alert-info { flex: 1; min-width: 0; }
    .sm-alert-title { font-size: 13px; font-weight: 600; color: #0f172a; margin-bottom: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .sm-alert-desc  { font-size: 12px; color: #64748b; line-height: 1.4; }
    .sm-alert-time  { font-size: 11px; color: #94a3b8; margin-top: 4px; }
    .sm-alert-score { font-size: 12px; font-weight: 700; padding: 2px 8px; border-radius: 6px; flex-shrink: 0; }

    .sm-panel-empty { padding: 32px 16px; text-align: center; color: #94a3b8; font-size: 13px; }
    .sm-panel-empty-icon { font-size: 32px; margin-bottom: 8px; }

    .sm-fab {
      position: fixed; z-index: 999998;
      width: 52px; height: 52px; border-radius: 50%;
      background: linear-gradient(135deg, #1a3c6e, #2563eb);
      color: #fff; border: none; cursor: pointer;
      box-shadow: 0 4px 20px rgba(26,60,110,0.4);
      display: flex; align-items: center; justify-content: center;
      font-size: 20px; transition: all 0.2s;
    }
    .sm-fab:hover { transform: scale(1.1); box-shadow: 0 6px 28px rgba(26,60,110,0.5); }
    .sm-fab.sm-bottom-right { bottom: 20px; right: 20px; }
    .sm-fab.sm-bottom-left  { bottom: 20px; left: 20px; }
    .sm-fab-dot {
      position: absolute; top: -2px; right: -2px;
      width: 16px; height: 16px; background: #ef4444;
      border-radius: 50%; border: 2px solid #fff;
      font-size: 9px; font-weight: 700; display: flex; align-items: center; justify-content: center;
    }

    /* ── Modal de verificación ── */
    .sm-modal-overlay {
      position: fixed; inset: 0; z-index: 9999999;
      background: rgba(0,0,0,0.5); display: flex;
      align-items: center; justify-content: center;
      padding: 20px; animation: sm-fade-in 0.2s ease;
    }
    .sm-modal {
      background: #fff; border-radius: 20px; padding: 32px;
      width: 100%; max-width: 420px;
      box-shadow: 0 25px 80px rgba(0,0,0,0.2);
      animation: sm-slide-up 0.25s ease;
    }
    .sm-modal-icon { font-size: 48px; text-align: center; margin-bottom: 16px; }
    .sm-modal-title { font-size: 20px; font-weight: 700; color: #0f172a; text-align: center; margin-bottom: 8px; }
    .sm-modal-desc  { font-size: 14px; color: #64748b; text-align: center; line-height: 1.6; margin-bottom: 24px; }
    .sm-modal-score-box {
      background: #f8fafc; border-radius: 12px; padding: 16px;
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 24px; border: 1px solid #e2e8f0;
    }
    .sm-modal-score-label { font-size: 13px; color: #64748b; }
    .sm-modal-score-value { font-size: 22px; font-weight: 800; color: #ca8a04; }
    .sm-modal-actions { display: flex; gap: 12px; }
    .sm-modal-btn {
      flex: 1; padding: 12px; border-radius: 10px; font-size: 14px;
      font-weight: 700; cursor: pointer; border: none; transition: all 0.2s;
    }
    .sm-modal-btn-confirm { background: #1a3c6e; color: #fff; }
    .sm-modal-btn-confirm:hover { background: #2563eb; }
    .sm-modal-btn-cancel { background: #f1f5f9; color: #64748b; }
    .sm-modal-btn-cancel:hover { background: #e2e8f0; }

    @keyframes sm-fade-in  { from { opacity: 0; } to { opacity: 1; } }
    @keyframes sm-slide-up { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

    /* ── Pulse animación para alertas nuevas ── */
    @keyframes sm-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.6; } }
    .sm-pulse { animation: sm-pulse 1.5s infinite; }
  `;

  // ── Clase principal SafeMarket ─────────────────────────────────────────
  class SafeMarket {
    constructor(config = {}) {
      this.config   = { ...DEFAULT_CONFIG, ...config };
      this.apiKey   = config.apiKey || this._getApiKeyFromScript();
      this.alerts   = [];
      this.panel    = null;
      this.fab      = null;
      this.isOpen   = false;
      this._injectStyles();

      if (this.config.autoInit) this.init();
    }

    // ── Inicialización ───────────────────────────────────────────────────
    init() {
      if (!this.apiKey) {
        console.warn('[SafeMarket] No se encontró API Key. Usa data-api-key en el script tag.');
        return;
      }
      this._renderFab();
      this._renderPanel();
      console.log('[SafeMarket] SDK inicializado correctamente ✅');
    }

    // ── API pública ──────────────────────────────────────────────────────

    /**
     * Analiza una transacción y retorna el resultado de riesgo.
     * 
     * @param {Object} transaction - Datos de la transacción
     * @param {number} transaction.amount - Monto
     * @param {string} transaction.transaction_type - PURCHASE|TRANSFER|WITHDRAWAL|DEPOSIT
     * @param {string} transaction.user_id - ID del usuario
     * @param {number} [transaction.old_balance_orig] - Saldo origen antes
     * @param {number} [transaction.new_balance_orig] - Saldo origen después
     * @returns {Promise<Object>} Resultado del análisis
     */
    async scoreTransaction(transaction) {
      try {
        const response = await fetch(`${this.config.apiUrl}/ml/score`, {
          method:  'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key':    this.apiKey,
          },
          body: JSON.stringify(transaction),
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const result = await response.json();

        // Si es REVIEW o DECLINE, agregar al panel de alertas
        if (result.decision !== 'APPROVE') {
          this._addAlert({
            id:          Date.now(),
            decision:    result.decision,
            risk_level:  result.risk_level,
            score:       result.overall_score,
            probability: result.fraud_probability,
            amount:      transaction.amount,
            type:        transaction.transaction_type,
            rules:       result.triggered_rules || [],
            time:        new Date(),
          });
        }

        return result;

      } catch (err) {
        console.error('[SafeMarket] Error al analizar transacción:', err);
        throw err;
      }
    }

    /**
     * Crea un badge de riesgo para mostrar junto a una transacción.
     * 
     * @param {Object} transaction - Datos de la transacción
     * @param {HTMLElement} [container] - Elemento donde insertar el badge
     * @returns {Promise<HTMLElement>} El badge creado
     */
    async createBadge(transaction, container = null) {
      const badge = document.createElement('span');
      badge.className = 'sm-widget sm-badge sm-badge-loading';
      badge.innerHTML = '<span class="sm-badge-dot"></span> Analizando...';

      if (container) container.appendChild(badge);

      try {
        const result = await this.scoreTransaction(transaction);
        this._updateBadge(badge, result);
      } catch {
        badge.className = 'sm-widget sm-badge sm-badge-loading';
        badge.innerHTML = '<span class="sm-badge-dot"></span> Error';
      }

      return badge;
    }

    /**
     * Muestra un modal de verificación cuando la transacción está en REVIEW.
     * 
     * @param {Object} scoreResult - Resultado de scoreTransaction()
     * @param {Function} onConfirm - Callback si el usuario confirma
     * @param {Function} onCancel  - Callback si el usuario cancela
     */
    showVerificationModal(scoreResult, onConfirm, onCancel) {
      const overlay = document.createElement('div');
      overlay.className = 'sm-widget sm-modal-overlay';

      const riskPct  = scoreResult.fraud_probability?.toFixed(1) || '50.0';
      const riskText = scoreResult.risk_level === 'medium'
        ? 'Esta transacción tiene indicadores de riesgo moderado.'
        : 'Esta transacción fue bloqueada preventivamente por alto riesgo.';

      overlay.innerHTML = `
        <div class="sm-modal">
          <div class="sm-modal-icon">⚠️</div>
          <div class="sm-modal-title">Verificación Requerida</div>
          <div class="sm-modal-desc">${riskText} Por favor confirma si deseas proceder.</div>
          <div class="sm-modal-score-box">
            <span class="sm-modal-score-label">Probabilidad de fraude</span>
            <span class="sm-modal-score-value">${riskPct}%</span>
          </div>
          <div class="sm-modal-actions">
            <button class="sm-modal-btn sm-modal-btn-cancel" id="sm-cancel">Cancelar</button>
            <button class="sm-modal-btn sm-modal-btn-confirm" id="sm-confirm">Confirmar</button>
          </div>
        </div>
      `;

      document.body.appendChild(overlay);

      overlay.querySelector('#sm-confirm').addEventListener('click', () => {
        document.body.removeChild(overlay);
        if (onConfirm) onConfirm(scoreResult);
      });

      overlay.querySelector('#sm-cancel').addEventListener('click', () => {
        document.body.removeChild(overlay);
        if (onCancel) onCancel(scoreResult);
      });

      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
          document.body.removeChild(overlay);
          if (onCancel) onCancel(scoreResult);
        }
      });
    }

    // ── Métodos internos ─────────────────────────────────────────────────

    _getApiKeyFromScript() {
      const script = document.currentScript ||
        document.querySelector('script[data-api-key]');
      return script?.getAttribute('data-api-key') || null;
    }

    _injectStyles() {
      if (document.getElementById('sm-styles')) return;
      const style = document.createElement('style');
      style.id = 'sm-styles';
      style.textContent = STYLES;
      document.head.appendChild(style);
    }

    _updateBadge(badge, result) {
      const level = result.risk_level || 'low';
      const map   = {
        low:    { cls: 'sm-badge-low',    icon: '✅', label: 'Bajo riesgo' },
        medium: { cls: 'sm-badge-medium', icon: '⚠️', label: 'Riesgo medio' },
        high:   { cls: 'sm-badge-high',   icon: '🚫', label: 'Alto riesgo' },
      };
      const { cls, icon, label } = map[level] || map.low;
      badge.className = `sm-widget sm-badge ${cls}`;
      badge.innerHTML = `<span class="sm-badge-dot"></span>${icon} ${label} · ${(result.overall_score * 100).toFixed(0)}%`;
      badge.title     = result.explanation
        ? `Decisión: ${result.decision}\n${result.triggered_rules?.join(', ')}`
        : result.decision;
    }

    _addAlert(alert) {
      this.alerts.unshift(alert);
      if (this.alerts.length > 50) this.alerts.pop();
      this._refreshPanel();
      this._shakeFab();
    }

    _renderFab() {
      this.fab = document.createElement('button');
      this.fab.className = `sm-widget sm-fab sm-${this.config.position}`;
      this.fab.innerHTML = '🛡️';
      this.fab.title = 'SafeMarket - Panel de Alertas';
      this.fab.addEventListener('click', () => this._togglePanel());
      document.body.appendChild(this.fab);
    }

    _renderPanel() {
      this.panel = document.createElement('div');
      this.panel.className = `sm-widget sm-panel sm-${this.config.position} sm-collapsed`;
      this.panel.style.display = 'none';
      this._refreshPanel();
      document.body.appendChild(this.panel);
    }

    _refreshPanel() {
      if (!this.panel) return;

      const count = this.alerts.filter(a => a.decision !== 'APPROVE').length;

      // Actualizar contador del FAB
      if (this.fab) {
        const existingDot = this.fab.querySelector('.sm-fab-dot');
        if (existingDot) existingDot.remove();
        if (count > 0) {
          const dot = document.createElement('span');
          dot.className = 'sm-fab-dot';
          dot.textContent = count > 9 ? '9+' : count;
          this.fab.appendChild(dot);
        }
      }

      const alertsHTML = this.alerts.length === 0
        ? `<div class="sm-panel-empty">
             <div class="sm-panel-empty-icon">✅</div>
             Sin alertas de fraude
           </div>`
        : this.alerts.map(a => {
            const riskMap = {
              high:   { icon: '🚫', cls: 'sm-alert-icon-high',   scoreCls: 'color:#dc2626' },
              medium: { icon: '⚠️', cls: 'sm-alert-icon-medium', scoreCls: 'color:#ca8a04' },
              low:    { icon: '✅', cls: 'sm-alert-icon-low',     scoreCls: 'color:#16a34a' },
            };
            const r    = riskMap[a.risk_level] || riskMap.low;
            const time = a.time ? new Date(a.time).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }) : '';
            const amt  = a.amount ? `$${Number(a.amount).toLocaleString('es')}` : '';
            return `
              <div class="sm-alert-item">
                <div class="sm-alert-icon ${r.cls}">${r.icon}</div>
                <div class="sm-alert-info">
                  <div class="sm-alert-title">${a.decision} · ${a.type || 'Transacción'}</div>
                  <div class="sm-alert-desc">${amt} · ${a.rules?.slice(0,2).join(', ') || 'Sin reglas'}</div>
                  <div class="sm-alert-time">${time}</div>
                </div>
                <div class="sm-alert-score" style="${r.scoreCls}">${(a.score * 100).toFixed(0)}%</div>
              </div>
            `;
          }).join('');

      this.panel.innerHTML = `
        <div class="sm-panel-header" id="sm-panel-toggle">
          <div class="sm-panel-header-left">
            <div class="sm-panel-logo">S</div>
            <span class="sm-panel-title">SafeMarket</span>
            ${count > 0 ? `<span class="sm-panel-badge-count">${count}</span>` : ''}
          </div>
          <button class="sm-panel-toggle">${this.isOpen ? '▼' : '▲'}</button>
        </div>
        <div class="sm-panel-body">${alertsHTML}</div>
      `;

      this.panel.querySelector('#sm-panel-toggle')
        .addEventListener('click', () => this._togglePanel());
    }

    _togglePanel() {
      this.isOpen = !this.isOpen;
      if (this.isOpen) {
        this.panel.style.display = 'flex';
        this.fab.style.display   = 'none';
        setTimeout(() => this.panel.classList.remove('sm-collapsed'), 10);
      } else {
        this.panel.classList.add('sm-collapsed');
        setTimeout(() => {
          this.panel.style.display = 'none';
          this.fab.style.display   = 'flex';
        }, 300);
      }
      this._refreshPanel();
    }

    _shakeFab() {
      if (!this.fab) return;
      this.fab.style.transform = 'scale(1.2)';
      setTimeout(() => { this.fab.style.transform = 'scale(1)'; }, 200);
    }
  }

  // ── Exposición global ────────────────────────────────────────────────────
  global.SafeMarket = SafeMarket;

  // Auto-inicializar si hay data-api-key en el script tag
  if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
      const script = document.querySelector('script[data-api-key]');
      if (script) {
        global._safemarket = new SafeMarket({
          apiKey: script.getAttribute('data-api-key'),
          position: script.getAttribute('data-position') || 'bottom-right',
          theme:    script.getAttribute('data-theme')    || 'light',
        });
      }
    });
  }

  // ── Soporte CommonJS / ESM (NPM) ───────────────────────────────────────
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = SafeMarket;
  }

})(typeof window !== 'undefined' ? window : global);
