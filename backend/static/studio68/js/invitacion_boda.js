/**
 * Lógica interactiva de la Invitación Digital de Boda - Maxwell & Zahilin
 * Tendencias 2026: Audio respetuoso con autoplay, RSVP dinámico por WhatsApp,
 * cronómetro circular en tiempo real y copiado rápido de Sinpe Móvil.
 */

document.addEventListener('DOMContentLoaded', function() {
    // --- 1. CONFIGURACIÓN DE ELEMENTOS Y ESTADO ---
    const audio = document.getElementById('weddingAudio');
    const audioWidget = document.getElementById('audioWidget');
    const vinylDisc = document.getElementById('vinylDisc');
    const audioStateText = document.getElementById('audioStateText');
    const welcomeModalEl = document.getElementById('welcomeWeddingModal');
    const btnEnterMusic = document.getElementById('btnEnterMusic');
    const btnEnterQuiet = document.getElementById('btnEnterQuiet');
    const toast = document.getElementById('invitationToast');

    let sugerenciaActual = JSON.parse(localStorage.getItem('sugerenciaBoda_studio68')) || null;

    // Toast de notificación suave
    function showToast(mensaje, duracion = 3500) {
        if (!toast) return;
        toast.innerHTML = `<i class="bi bi-stars me-2 text-warning"></i>${mensaje}`;
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, duracion);
    }

    // --- 2. CONTROL DE AUDIO INTELIGENTE ---
    function updateAudioUI(isPlaying) {
        if (!vinylDisc || !audioStateText) return;
        if (isPlaying) {
            vinylDisc.classList.add('spinning');
            vinylDisc.innerHTML = '<i class="bi bi-pause-fill"></i>';
            audioStateText.innerHTML = 'Música nupcial<small>Tocando</small>';
        } else {
            vinylDisc.classList.remove('spinning');
            vinylDisc.innerHTML = '<i class="bi bi-play-fill"></i>';
            audioStateText.innerHTML = 'Música nupcial<small>Pausada</small>';
        }
    }

    if (audioWidget && audio) {
        audioWidget.addEventListener('click', function() {
            if (audio.paused) {
                audio.play().then(() => {
                    updateAudioUI(true);
                    showToast('Reproduciendo melodía nupcial');
                }).catch(e => console.log('Audio error:', e));
            } else {
                audio.pause();
                updateAudioUI(false);
                showToast('Música pausada');
            }
        });

        audio.addEventListener('play', () => updateAudioUI(true));
        audio.addEventListener('pause', () => updateAudioUI(false));
    }

    // Modal de bienvenida para respetar la política de autoplay
    if (welcomeModalEl) {
        const welcomeModal = new bootstrap.Modal(welcomeModalEl);
        welcomeModal.show();

        if (btnEnterMusic) {
            btnEnterMusic.addEventListener('click', function() {
                welcomeModal.hide();
                if (audio) {
                    audio.play().then(() => {
                        updateAudioUI(true);
                        showToast('¡Bienvenidos a nuestro primer aniversario!');
                    }).catch(err => {
                        console.log('Autoplay bloqueado:', err);
                    });
                }
            });
        }

        if (btnEnterQuiet) {
            btnEnterQuiet.addEventListener('click', function() {
                welcomeModal.hide();
                updateAudioUI(false);
            });
        }
    }

    // --- 3. CUENTA REGRESIVA CIRCULAR PRECISA ---
    const targetDateStr = document.getElementById('cuenta-regresiva')?.dataset?.date || '2026-12-06T15:30:00';
    const countdownDate = new Date(targetDateStr).getTime();

    function updateCountdown() {
        const now = new Date().getTime();
        const difference = countdownDate - now;
        const countdownEl = document.getElementById('countdown');

        if (!countdownEl) return;

        if (difference <= 0) {
            countdownEl.innerText = '00 : 00 : 00 : 00';
            return;
        }

        const days = Math.floor(difference / (1000 * 60 * 60 * 24));
        const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((difference % (1000 * 60)) / 1000);

        const formatTime = (time) => time < 10 ? '0' + time : time;
        countdownEl.innerText = `${formatTime(days)} : ${formatTime(hours)} : ${formatTime(minutes)} : ${formatTime(seconds)}`;
    }

    setInterval(updateCountdown, 1000);
    updateCountdown();

    // --- 4. SUGERENCIA DE CANCIÓN PARA EL DJ ---
    const formCancion = document.getElementById('formCancionDJ');
    const badgeSugerencia = document.getElementById('badgeSugerenciaGuardada');

    function actualizarBadgeSugerencia() {
        if (!badgeSugerencia) return;
        if (sugerenciaActual) {
            badgeSugerencia.innerHTML = `
                <div class="alert alert-warning py-2 px-3 small border-0 rounded-pill d-inline-flex align-items-center mb-3 shadow-sm">
                    <i class="bi bi-disc-fill me-2 text-dark"></i>
                    Canción para el DJ: <strong>${sugerenciaActual.cancion}</strong> (de ${sugerenciaActual.nombre})
                </div>
            `;
            badgeSugerencia.classList.remove('d-none');
        } else {
            badgeSugerencia.classList.add('d-none');
        }
    }

    if (formCancion) {
        formCancion.addEventListener('submit', function(e) {
            e.preventDefault();
            const nombre = document.getElementById('invitadoNombre')?.value.trim();
            const cancion = document.getElementById('invitadoCancion')?.value.trim();

            if (!nombre || !cancion) return;

            sugerenciaActual = { nombre, cancion };
            localStorage.setItem('sugerenciaBoda_studio68', JSON.stringify(sugerenciaActual));

            formCancion.reset();
            actualizarBadgeSugerencia();
            showToast('¡Canción guardada! La incluiremos en tu confirmación al final de la página.');

            // Scroll suave hacia la confirmación al final
            const rsvpSection = document.getElementById('seccionRSVP');
            if (rsvpSection) {
                setTimeout(() => {
                    rsvpSection.scrollIntoView({ behavior: 'smooth' });
                }, 800);
            }
        });
    }

    actualizarBadgeSugerencia();

    // --- 5. CONFIRMACIÓN RSVP POR WHATSAPP (Última sección) ---
    window.confirmarAsistenciaWhatsApp = function(telefono) {
        let texto = '¡Hola Maxwell y Zahilin! ✨ Confirmo con mucha alegría mi asistencia a su celebración el 6 de Diciembre.';
        if (sugerenciaActual) {
            texto += ` Además, me encantaría escuchar en la fiesta: "${sugerenciaActual.cancion}" (de parte de ${sugerenciaActual.nombre}).`;
        }
        texto += ' ¡Nos vemos pronto!';

        const url = `https://wa.me/${telefono}?text=${encodeURIComponent(texto)}`;
        window.open(url, '_blank');
    };

    window.declinarAsistenciaWhatsApp = function(telefono) {
        let texto = '¡Hola Maxwell y Zahilin! Lamentablemente no podré acompañarlos físicamente en esta ocasión, pero les deseo el mayor de los éxitos y bendiciones en su primer aniversario. ¡Muchas felicidades!';
        const url = `https://wa.me/${telefono}?text=${encodeURIComponent(texto)}`;
        window.open(url, '_blank');
    };

    // --- 6. COPIAR SINPE MÓVIL AL PORTAPAPELES ---
    window.copiarSinpe = function(numero) {
        navigator.clipboard.writeText(numero).then(() => {
            showToast(`¡Número Sinpe Móvil (${numero}) copiado exitosamente!`);
        }).catch(() => {
            prompt('Copia el número Sinpe Móvil manualmente:', numero);
        });
    };

    window.copiarDireccion = function(direccion) {
        navigator.clipboard.writeText(direccion).then(() => {
            showToast('¡Dirección copiada al portapapeles!');
        }).catch(() => {
            prompt('Copia la dirección manualmente:', direccion);
        });
    };
});
