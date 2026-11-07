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

Despliegue en contenedores con Podman (`podman compose`).

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

## Estado

Proyecto en etapa inicial de scaffold: la estructura de dominios y de capas ya está definida, sin implementación de negocio todavía.
