// --- 1. VARIABLES GLOBALES DE SESIÓN ---
const userId = localStorage.getItem('sgcat_user_id');
const userName = localStorage.getItem('sgcat_user_name');
const userRole = localStorage.getItem('sgcat_user_role');
let vistaActual = userRole === 'Usuario' ? 'mis-tickets' : 'todos';

// --- 2. LÓGICA GLOBAL Y DE SEGURIDAD ---
function validarSesion() {
    if (window.location.pathname.includes('login.html')) return;
    if (!userId) window.location.href = 'login.html';
}

function renderizarInterfazGlobal() {
    const elNombre = document.getElementById('sesion-nombre');
    const elRol = document.getElementById('sesion-role');
    const elMovilRol = document.getElementById('movil-role');
    
    if (elNombre) elNombre.textContent = userName;
    if (elRol) elRol.textContent = userRole;
    if (elMovilRol) elMovilRol.textContent = userRole;

    if (userRole === 'Usuario') {
        const btnPanelGlobal = document.getElementById('btn-panel-principal');
        if (btnPanelGlobal) btnPanelGlobal.classList.add('hidden');
    }
}

function cerrarSesion() {
    localStorage.clear();
    window.location.href = 'login.html';
}

function obtenerClaseBadge(categoria) {
    if (categoria === 'Hardware') return 'badge-hardware';
    if (categoria === 'Software') return 'badge-software';
    if (categoria === 'Redes') return 'badge-redes';
    return 'badge-manual';
}

// --- 3. LÓGICA DEL LOGIN  ---
function inicializarLogin() {
    const formLogin = document.getElementById('form-login');
    if (!formLogin) return; // Si no estamos en el login, ignorar

    formLogin.addEventListener('submit', async (e) => {
        e.preventDefault();
        const credentials = {
            correo: document.getElementById('correo').value,
            contrasena: document.getElementById('contrasena').value
        };
        try {
            const res = await fetch('http://localhost:8000/login/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(credentials)
            });
            if(res.ok) {
                const user = await res.json();
                localStorage.setItem('sgcat_user_id', user.id_usuario);
                localStorage.setItem('sgcat_user_name', user.nombre_completo);
                localStorage.setItem('sgcat_user_role', user.nombre_rol);
                window.location.href = 'dashboard.html';
            } else { 
                alert('Credenciales incorrectas.'); 
            }
        } catch { alert('Error de red al conectar con FastAPI.'); }
    });
}

// --- 4. LÓGICA DEL DASHBOARD  ---
async function cargarTickets() {
    const tabla = document.getElementById('tabla-tickets');
    if (!tabla) return; // Si no estamos en el dashboard, ignorar

    let url = vistaActual === 'mis-tickets' 
        ? `http://localhost:8000/tickets/usuario/${userId}` 
        : 'http://localhost:8000/tickets/';
    
    // Actualizar botones de navegación
    if (vistaActual === 'mis-tickets') {
        document.getElementById('titulo-vista').textContent = "Mis Tickets Reportados";
        document.getElementById('btn-mis-tickets').className = "nav-item active";
        if (userRole !== 'Usuario') document.getElementById('btn-panel-principal').className = "nav-item";
    } else {
        document.getElementById('titulo-vista').textContent = "Todos los Tickets del Sistema";
        document.getElementById('btn-panel-principal').className = "nav-item active";
        document.getElementById('btn-mis-tickets').className = "nav-item";
    }

    try {
        const respuesta = await fetch(url);
        const tickets = await respuesta.json();
        tabla.innerHTML = ''; 

        if (tickets.length === 0) {
            tabla.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 32px; color: var(--text-muted);">No hay tickets registrados.</td></tr>`;
            return;
        }

        tickets.forEach(ticket => {
            const claseBadge = obtenerClaseBadge(ticket.clasificacion_ia);
            const catTexto = ticket.clasificacion_ia || 'Revisión Manual';
            const claseEstado = ticket.estado === 'Resuelto' ? 'status-tag resuelto' : 'status-tag';

            tabla.innerHTML += `
            <tr onclick="window.location.href='ver_ticket.html?id=${ticket.id_ticket}'">
                <td class="ticket-id">#${ticket.id_ticket}</td>
                <td class="ticket-title">${ticket.titulo}</td>
                <td>${ticket.creador}</td>
                <td>${ticket.afectado}</td>
                <td><span class="badge ${claseBadge}">${catTexto}</span></td>
                <td><span class="${claseEstado}">${ticket.estado}</span></td>
            </tr>`;
        });
    } catch (error) {
        tabla.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #ef4444; padding: 20px;">Error de conexión.</td></tr>`;
    }
}

function cambiarVista(nuevaVista) {
    vistaActual = nuevaVista;
    cargarTickets();
}

// --- 5. LÓGICA DE NUEVO TICKET  ---
async function inicializarNuevoTicket() {
    const formTicket = document.getElementById('form-ticket');
    if (!formTicket) return;

    // Cargar usuarios en el select
    try {
        const respuesta = await fetch('http://localhost:8000/usuarios/');
        const usuarios = await respuesta.json();
        const selectAfectado = document.getElementById('afectado');
        selectAfectado.innerHTML = `<option value="${userId}">A mí (${userName})</option>`;
        
        usuarios.forEach(user => {
            if (user.id_usuario.toString() !== userId) {
                selectAfectado.innerHTML += `<option value="${user.id_usuario}">A un compañero: ${user.nombre_completo}</option>`;
            }
        });
    } catch (error) { console.error(error); }

    // Manejar envío
    formTicket.addEventListener('submit', async (e) => {
        e.preventDefault(); 
        const datos = {
            titulo: document.getElementById('titulo').value,
            descripcion: document.getElementById('descripcion').value,
            id_usuario_creador: parseInt(userId),
            id_usuario_afectado: parseInt(document.getElementById('afectado').value)
        };

        try {
            const res = await fetch('http://localhost:8000/tickets/', {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(datos)
            });
            if (res.ok) {
                const data = await res.json();
                document.getElementById('contenedor-formulario').innerHTML = `
                    <div class="success-alert">
                        <h3>¡Ticket #${data.id_ticket} Registrado Exitosamente!</h3>
                        <p>Clasificación preliminar: <strong>${data.clasificacion_ia}</strong></p>
                        <div class="ai-suggestion-inner"><strong>Recomendación:</strong><br>${data.recomendacion_usuario}</div>
                    </div>
                    <div style="text-align: center;"><a href="dashboard.html" class="btn-primary">Volver al Panel</a></div>
                `;
            } else { alert('Error al guardar el ticket.'); }
        } catch { alert('Error de red.'); }
    });
}

// --- 6. LÓGICA DE VER TICKET ---
async function inicializarVerTicket() {
    const contenedorTicket = document.getElementById('contenedor-ticket');
    if (!contenedorTicket) return;

    const parametrosURL = new URLSearchParams(window.location.search);
    const idTicket = parametrosURL.get('id');
    window.idTicketGlobal = idTicket; // Guardamos para usar en los modales

    const RECOMENDACIONES = {
        "HARDWARE": "Verifique conexiones físicas y suministro eléctrico.",
        "SOFTWARE": "Intente guardar su trabajo y reinicie el equipo.",
        "REDES": "Compruebe su cable de red o conexión Wi-Fi.",
        "REVISIÓN MANUAL": "Un técnico evaluará este caso."
    };

    try {
        const res = await fetch(`http://localhost:8000/tickets/${idTicket}`);
        if (!res.ok) throw new Error("No existe");
        const ticket = await res.json();
        
        document.getElementById('vista-titulo').textContent = ticket.titulo;
        document.getElementById('vista-id').textContent = `#${ticket.id_ticket}`;
        document.getElementById('vista-creador').textContent = ticket.creador;
        document.getElementById('vista-afectado').textContent = ticket.afectado;
        document.getElementById('vista-descripcion').textContent = ticket.descripcion;
        
        const elEstado = document.getElementById('vista-estado');
        elEstado.textContent = ticket.estado;
        if (ticket.estado === 'Resuelto') {
            elEstado.className = 'status-tag resuelto';
            document.getElementById('btn-accion-resolver').style.display = 'none';
        }
        
        const catTexto = ticket.clasificacion_ia || 'Revisión Manual';
        const elCat = document.getElementById('vista-categoria');
        elCat.textContent = catTexto.toUpperCase();
        elCat.className = `badge ${obtenerClaseBadge(catTexto)}`;
        document.getElementById('vista-sugerencia').textContent = RECOMENDACIONES[catTexto.toUpperCase()] || RECOMENDACIONES["REVISIÓN MANUAL"];

        contenedorTicket.classList.remove('hidden');
    } catch {
        window.location.href = "dashboard.html";
    }
}

// Modales de Ver Ticket
function iniciarResolucion() {
    document.getElementById('confirm-ticket-id').textContent = `#${window.idTicketGlobal}`;
    document.getElementById('modal-confirmacion').classList.add('active');
}

function cerrarModalConfirmacion() { document.getElementById('modal-confirmacion').classList.remove('active'); }

async function ejecutarResolucion() {
    cerrarModalConfirmacion();
    try {
        const res = await fetch(`http://localhost:8000/tickets/${window.idTicketGlobal}/resolver`, { method: 'PUT' });
        if (res.ok) document.getElementById('modal-exito').classList.add('active');
        else alert("Error al intentar actualizar.");
    } catch { alert("Error de red."); }
}

function cerrarModalYVolver() { window.location.href = 'dashboard.html'; }

// --- 7. ARRANQUE DEL SISTEMA ---
document.addEventListener('DOMContentLoaded', () => {
    validarSesion();
    renderizarInterfazGlobal();
    
    // Disparadores automáticos por pantalla
    inicializarLogin();
    cargarTickets();
    inicializarNuevoTicket();
    inicializarVerTicket();
});

// --- 8. MODO OSCURO / CLARO ---
function inicializarTema() {
    const temaGuardado = localStorage.getItem('sgcat_theme');
    if (temaGuardado === 'dark') {
        document.body.classList.add('dark-theme');
    }
}

function alternarTema() {
    document.body.classList.toggle('dark-theme');
    if (document.body.classList.contains('dark-theme')) {
        localStorage.setItem('sgcat_theme', 'dark');
    } else {
        localStorage.setItem('sgcat_theme', 'light');
    }
}

// Ejecutar al cargar la página
document.addEventListener('DOMContentLoaded', inicializarTema);