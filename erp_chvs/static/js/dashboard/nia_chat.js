'use strict';

class NiaChatManager {
    constructor() {
        this.form = document.getElementById('niaChatForm');
        this.input = document.getElementById('niaMensajeInput');
        this.mensajesEl = document.getElementById('niaMensajes');
        this.btnEnviar = document.getElementById('niaBtnEnviar');
        this.btnReset = document.getElementById('niaBtnReset');
        this.enviando = false;
    }

    init() {
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            const texto = this.input.value.trim();
            if (texto) this.enviarMensaje(texto);
        });

        this.btnReset.addEventListener('click', () => this.resetear());
    }

    async enviarMensaje(texto) {
        if (this.enviando) return;
        this.enviando = true;
        this._setEstadoEnviando(true);

        this.renderMensaje('usuario', texto);
        this.input.value = '';

        const indicador = this.renderIndicadorEscribiendo();

        try {
            const resp = await fetch(NIA_CHAT_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN,
                },
                body: JSON.stringify({ mensaje: texto }),
            });

            const datos = await resp.json();
            indicador.remove();

            if (datos.tipo === 'listo') {
                this.renderMensaje('nia', datos.mensaje);
                this.renderDescarga(datos.url_descarga, datos.label_descarga);
            } else if (datos.tipo === 'error') {
                this.renderMensaje('nia', datos.mensaje, 'error');
            } else if (datos.tipo === 'info') {
                this.renderMensaje('nia', datos.mensaje, 'info');
            } else {
                this.renderMensaje('nia', datos.mensaje);
            }
        } catch {
            indicador.remove();
            this.renderMensaje('nia', 'Error de conexión. Intenta de nuevo.', 'error');
        } finally {
            this.enviando = false;
            this._setEstadoEnviando(false);
            this.input.focus();
        }
    }

    renderMensaje(autor, texto, tipo) {
        const burbuja = document.createElement('div');
        const esNia = autor === 'nia';
        let claseExtra = '';
        if (tipo === 'error') claseExtra = ' nia-bubble--error';
        else if (tipo === 'info') claseExtra = ' nia-bubble--info';
        burbuja.className = `nia-bubble nia-bubble--${esNia ? 'nia' : 'usuario'}${claseExtra}`;
        burbuja.innerHTML = `<p>${this._escaparHtml(texto)}</p>`;
        this.mensajesEl.appendChild(burbuja);
        this._scrollAbajo();
        return burbuja;
    }

    renderDescarga(url, label) {
        const contenedor = document.createElement('div');
        contenedor.className = 'nia-bubble nia-bubble--nia nia-bubble--descarga';
        contenedor.innerHTML = `
            <a href="${url}" class="nia-download-btn" target="_blank" rel="noopener noreferrer">
                <i class="fas fa-file-download"></i>
                <span>${this._escaparHtml(label)}</span>
            </a>
            <p class="nia-hint">¿Necesitas más planillas? Escribe otra solicitud.</p>
        `;
        this.mensajesEl.appendChild(contenedor);
        this._scrollAbajo();
    }

    renderIndicadorEscribiendo() {
        const burbuja = document.createElement('div');
        burbuja.className = 'nia-bubble nia-bubble--nia nia-bubble--typing';
        burbuja.innerHTML = `
            <span class="nia-dot"></span>
            <span class="nia-dot"></span>
            <span class="nia-dot"></span>
        `;
        this.mensajesEl.appendChild(burbuja);
        this._scrollAbajo();
        return burbuja;
    }

    async resetear() {
        try {
            await fetch(NIA_RESET_URL, {
                method: 'POST',
                headers: { 'X-CSRFToken': CSRF_TOKEN },
            });
        } catch { /* silenciar */ }

        // Limpiar UI conservando solo el mensaje inicial
        const burbujas = this.mensajesEl.querySelectorAll('.nia-bubble:not(:first-child)');
        burbujas.forEach(b => b.remove());
        this.input.value = '';
        this.input.focus();
    }

    _setEstadoEnviando(activo) {
        this.btnEnviar.disabled = activo;
        this.input.disabled = activo;
        this.btnEnviar.innerHTML = activo
            ? '<i class="fas fa-circle-notch fa-spin"></i>'
            : '<i class="fas fa-paper-plane"></i>';
    }

    _scrollAbajo() {
        this.mensajesEl.scrollTop = this.mensajesEl.scrollHeight;
    }

    _escaparHtml(texto) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(texto));
        return div.innerHTML;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const manager = new NiaChatManager();
    manager.init();
});
