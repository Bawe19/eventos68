# Eventos68 — Plataforma Integral de Catering y Gestión de Eventos

Bienvenido a **Eventos68**, una plataforma moderna, escalable y diseñada para operar **100% gratis en la nube** sin costos fijos de servidores ni licencias.

Este proyecto es la evolución y modernización integral del sistema original de *La Parrillita de Ron*, migrado de .NET Framework/SQL Server hacia un stack de alta demanda profesional: **Python 3 (Django REST Framework)**, **PostgreSQL en la Nube (Neon / Supabase)** y **Flutter (Móvil y Web)**.

---

## 🌟 Características Principales

1. **Cotizador Público Inteligente:**
   - Permite a los clientes seleccionar tipo de evento, fecha, número de comensales y menú personalizado.
   - **Automatizaciones de Menaje y Mobiliario:** Cálculo automático de platos, cubiertos, servilletas, copas, vasos, sillas, mesas (redondas de 10 pax, rectangulares de 8 y 12 pax) y mantelería de gala según la cantidad de invitados.
   - **Cálculo Logístico:** Tarifado de transporte por distancia (km) y carga de imágenes de referencia para decoración.
2. **Motor Financiero Riguroso:**
   - Subtotal de Servicios + Gastos Directos + Margen de Ganancia Configurable (ej. 30%) + Impuesto IVA (13%) = Total General.
   - Cálculo automático de costo por comensal y pago inicial mínimo (adelanto configurable, ej. 10%).
3. **Reglas de Negocio Estrictas:**
   - **Exclusividad de Fecha:** Garantiza que no se puedan contratar dos eventos en la misma fecha (1 evento por día).
   - Conversión de Solicitud $\rightarrow$ Cotización Formal $\rightarrow$ Evento Contratado mediante comprobante de adelanto.
4. **Generador de Presupuestos en PDF (ReportLab):**
   - Generación nativa y ultrarrápida de presupuestos en PDF con branding elegante de Eventos68, sin dependencias complejas.
5. **Notificaciones Automáticas por Correo:**
   - Envío automático del presupuesto en PDF al cliente.
   - Confirmación inmediata de abonos con saldo restante y cuenta regresiva de días faltantes para el evento.
6. **Panel Administrativo Completo:**
   - Panel web Django Admin enriquecido con filtros, badges y acciones masivas.
7. **Aplicación Flutter (Android, iOS y Web):**
   - Dashboard ejecutivo con indicadores en tiempo real (solicitudes, ingresos, balance operativo).
   - Lista y filtrado de cotizaciones con descarga de PDF.
   - Módulo de eventos contratados con registro rápido de abonos y saldos pendientes.

---

## 🏗️ Arquitectura del Proyecto

```text
Eventos68/
├── backend/                  # API REST y Servidor Web Django
│   ├── config/               # Configuración central (settings, urls, wsgi)
│   ├── core/                 # Modelos relacionales, motor financiero y PDFs
│   ├── api/                  # Endpoints REST (DRF) para Flutter
│   ├── web/                  # Vistas web públicas y formulario de cotización
│   ├── templates/            # Plantillas HTML5 responsivas con Bootstrap 5
│   ├── seed_eventos68.py     # Script con catálogo inicial (37 componentes cargados)
│   ├── Dockerfile            # Contenedor para despliegue en Render/Railway
│   ├── render.yaml           # Despliegue en 1 clic para Render.com
│   └── requirements.txt      # Dependencias Python
└── flutter_app/              # Aplicación Móvil y Web en Flutter
    ├── lib/
    │   ├── models/           # Modelos Dart (Cotización, Evento, Stats)
    │   ├── services/         # Cliente HTTP hacia Django API
    │   ├── screens/          # Dashboard, Cotizaciones, Eventos y Abonos
    │   └── main.dart         # Punto de entrada de Flutter
    └── pubspec.yaml          # Dependencias Flutter
```

---

## 🚀 Guía de Puesta en Marcha Local

### 1. Iniciar el Backend (Django)
Abre una terminal PowerShell y navega a la carpeta del backend:

```powershell
cd c:\Users\maxwe\.gemini\antigravity\scratch\Eventos68\backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

El servidor web estará disponible en:
* **Web Pública / Cotizador:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Panel Administrativo:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
  * **Usuario:** `admin`
  * **Contraseña:** `admin12345`
* **Explorador de la API REST:** [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)

### 2. Ejecutar Pruebas Automatizadas
Para verificar que las fórmulas financieras, validaciones de fechas y generación de PDFs funcionen a la perfección:

```powershell
python manage.py test core
python manage.py test api
```

---

## ☁️ Despliegue 100% Gratuito y Sostenible en la Nube

### Paso 1: Base de Datos PostgreSQL Gratuita en Neon.tech
1. Entra a [Neon.tech](https://neon.tech/) y crea una cuenta gratuita con GitHub o Google.
2. Crea un proyecto llamado `eventos68-db`.
3. Copia tu cadena de conexión PostgreSQL (ejemplo: `postgresql://neondb_owner:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require`).
4. Pega esa cadena en la variable `DATABASE_URL` de tu archivo `.env` o en las variables de entorno de Render. ¡Listo! Django detectará PostgreSQL automáticamente y ejecutará las migraciones.

### Paso 2: Servidor Web Gratuito en Render.com
1. Sube tu carpeta `backend` a un repositorio en GitHub.
2. Entra a [Render.com](https://render.com/) y crea un nuevo **Web Service**.
3. Conecta tu repositorio de GitHub.
4. Render detectará automáticamente el archivo `render.yaml` o `Dockerfile`.
5. En la sección **Environment Variables**, agrega:
   * `DATABASE_URL`: Tu URL de Neon.tech copiada en el Paso 1.
   * `DEBUG`: `False`
   * `ALLOWED_HOSTS`: `*`
6. Haz clic en **Deploy**. Tendrás tu backend y formulario web funcionando en la nube con dominio SSL HTTPS gratuito de por vida (ej: `https://eventos68.onrender.com`).

---

## 📱 Ejecutar la Aplicación en Flutter

Una vez que tengas instalado el SDK de Flutter en tu equipo:

```bash
cd c:\Users\maxwe\.gemini\antigravity\scratch\Eventos68\flutter_app
flutter pub get
flutter run -d chrome      # Para abrir en el navegador
# o
flutter run                # Para abrir en emulador Android o dispositivo físico
```
