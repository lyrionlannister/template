# Pulso

SaaS multi-tenant de comunicaciones para empresas de habla hispana, orientado a PyMEs y agencias de cobranza pequeñas. Lanzamiento inicial en Colombia.

## Qué hace

1. El cliente se registra y vincula su WhatsApp Business API mediante Embedded Signup.
2. Carga sus contactos, cada uno con variables propias en formato JSON.
3. Crea Audiencias: filtros dinámicos o estáticos sobre esos contactos.
4. Crea plantillas y campañas, y programa o automatiza los envíos.
5. Consume su suscripción y su saldo utilizable según canal y categoría de mensaje.

Canales soportados: WhatsApp (directo por Meta Cloud API, con las credenciales del propio tenant) y SMS/RCS (vía Sent.dm con token de plataforma). Pagos y suscripciones solo a través de Wompi Colombia (tarjeta, PSE, Nequi).

Interfaz, textos y documentación de usuario en español.

## Arquitectura

Monolito modular multi-tenant, con aislamiento por tenant en cada tabla y cada operación. Dos aplicaciones de código independientes:

- `api/` — backend FastAPI (async) + SQLAlchemy (async) sobre PostgreSQL, migraciones con Alembic, sesión y caché en Valkey.
- `client/` — frontend Vite + React + TypeScript + Tailwind, con sistema de diseño propio.

Despliegue en contenedores con Podman (`podman compose`). En desarrollo local, nginx termina TLS (certificados locales de mkcert) y enruta a `client` y `api` — necesario porque Meta exige origen https hasta para el Embedded Signup de WhatsApp en localhost.

## Stack

**Backend:** Python ≥3.14, FastAPI, SQLAlchemy (postgresql-asyncpg), Uvicorn, PostgreSQL, Alembic, Valkey, gestionado con `uv`.

**Frontend:** Vite, React, TypeScript, Tailwind, Lucide.

## Estructura del repositorio

```
.
├── api/      backend (FastAPI, por dominio de negocio)
├── client/   frontend (React, por área funcional)
└── infra/    volúmenes locales de infraestructura
```

### Lo compartido

- `api/app/core/`: infraestructura transversal sin reglas de negocio de un dominio concreto — config (`settings.py`), base de datos (`base.py`, `session.py`, mixins, aislamiento por tenant), cliente de Valkey, seguridad (hash de password, JWT, cookies, cifrado de credenciales) y los middlewares de la app. Cualquier dominio puede importar de `core`; `core` nunca importa de un dominio.
- `client/src/shared/`: lo que no es de autenticación (`auth/`) ni del sistema de diseño (`ui/`), pero varias áreas necesitan igual — hoy el cliente HTTP único (`use-api-client.ts`) y utilidades genéricas.
- `client/src/ui/`: el sistema de diseño propio (componentes visuales, `AppShell`, tokens). Ningún dominio de negocio vive aquí, solo piezas reutilizables sin lógica de negocio.

Un dominio nunca importa el repository ni el model de otro dominio directamente — solo su service, sus schemas o sus clients (verificado por `api/.importlinter` + `api/scripts/check_architecture.py`).

### Estructura de un módulo de dominio

Backend (`api/app/<dominio>/`):

```
<dominio>/
├── models/        tablas SQLAlchemy
├── repositories/  acceso a datos (SQL), nunca reglas de negocio
├── services/      reglas de negocio, orquesta repositories/clients
├── schemas/       Pydantic de entrada/salida de la API
├── controllers/   rutas FastAPI, delgadas: validan y llaman al service
├── exceptions.py  errores propios del dominio
├── dependencies.py  wiring de FastAPI (Depends) hacia services/repositories
└── clients/       integraciones externas (ej. Meta Cloud API), si el dominio las necesita
```

Frontend (`client/src/<área>/`):

```
<área>/
├── components/  piezas visuales propias del área
├── const/       constantes (labels, mapeos fijos)
├── hooks/       un hook por recurso, llama a use-api-client
├── pages/       una página por vista, monta su propio AppShell
├── props/       tipos de las props de los componentes del área
├── types/       tipos del dominio/API (lo que devuelve el backend)
└── utils/       funciones puras sin estado
```

Ambas estructuras son fijas por convención del proyecto: no se crea una carpeta nueva en un dominio o área sin que ya exista un archivo real que la necesite.

## Estado

Backend: auth con sesión en Valkey y MFA/OTP obligatorio, administrador del sistema (planes, parámetros comerciales, costos por canal, tipo de cambio) con identidad real de superadmin, billing con Wompi (onboarding, suscripción recurrente, saldo, webhooks), contactos, audiencias, plantillas, y mensajería de WhatsApp (conexión por Embedded Signup, envío de plantillas por Meta Cloud API, OTP de login real por WhatsApp con identidad de plataforma).

Frontend: páginas de todas las áreas anteriores, incluido el panel de administrador del sistema, gateado por sesión real.

Pendiente: SMS/RCS vía Sent.dm, campañas y dashboards. El Embedded Signup real de WhatsApp queda bloqueado hasta que Meta apruebe la cuenta de negocio como BSP/Tech Provider — bloqueo externo, no de código.
