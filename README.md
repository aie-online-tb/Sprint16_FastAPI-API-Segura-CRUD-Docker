![Cabecera](../../../../../Sprint_15/assets/cabecera_mlops.png)

# Workout:API segura (CRUD) + Docker

**La API ya está dada:** CRUD de ítems en memoria + API key, rate limit y CORS. Aquí el foco es **empaquetarla en un contenedor** y probarla en local. Posteriormente se puede subir a la nube.

```text
cliente → /items?api_key=... → rate limit → CRUD
                ↓
        /health y /docs sin clave
```

## Estructura

```text
.
├── app.py             # Rutas + /health + CRUD + CORS
├── schemas.py         # Item (Pydantic)
├── config.py          # API_KEY, rate limit, CORS_ORIGINS
├── security.py        # require_api_key (?api_key=)
├── rate_limit.py      # Contador en memoria → 429
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── .dockerignore
└── README.md
```

---

## 1) Arranque local (sin Docker)

Útil para comprobar que el código responde antes del build.

```bash
python -m venv .venv
source .venv/bin/activate          # Git Bash / macOS / Linux
# .venv\Scripts\Activate.ps1       # Windows PowerShell

pip install -r requirements.txt
cp .env.example .env               # editamos API_KEY
uvicorn app:app --reload --port 8000
```

- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)  
- Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

En Swagger, en cada ruta protegida: *Try it out* → query **`api_key`** = valor del `.env`.

---

## 2) Docker — build y run

Desde esta carpeta (donde está el `Dockerfile`). Si aún no tenéis `.env`:

```bash
cp .env.example .env               # editamos API_KEY
```

```bash
docker build -t api-segura-crud .
docker run --rm --name api-segura -p 8000:8000 --env-file .env api-segura-crud
```

| Pieza | Por qué |
|-------|---------|
| `--name api-segura` | Nombre fijo del **contenedor** (si no, Docker inventa uno) |
| `-p 8000:8000` | Publicamos el puerto del contenedor en el host |
| `--env-file .env` | Secretos en **runtime** (mismo fichero que en local); no van dentro de la imagen |
| `.dockerignore` | Evita meter `.env`, `.venv`, `.git` en el build |

El `CMD` del Dockerfile usa `${PORT:-8000}`: puerto **8000** por defecto; si existe la variable `PORT`, se usa esa.

### Alternativa: `-e` una a una

```bash
docker run --rm --name api-segura -p 8000:8000 \
  -e API_KEY=cambia-esta-clave \
  -e RATE_LIMIT_PER_MINUTE=10 \
  -e CORS_ORIGINS=http://127.0.0.1:8501,http://localhost:8501 \
  api-segura-crud
```

### Comandos útiles (terminal y Docker Desktop)

También podéis usar **Docker Desktop**: pestaña *Containers* / *Images* → Stop, Start (Play), Delete.

En terminal podéis usar el **nombre** (`api-segura`, `api-segura-crud`) **o el ID**. El ID lo veis con `docker ps` / `docker images`. Basta el **prefijo** del ID (p. ej. las 3 primeras cifras) **si es único** entre lo que tenéis listado; si hay ambigüedad, Docker se queja y hay que poner más caracteres.

```bash
# Listar contenedores en marcha
docker ps

# Listar todos (también parados)
docker ps -a

# Parar el contenedor (nombre, ID completo o prefijo)
docker stop api-segura
# docker stop a1b3c4d5e6f7
# docker stop a1b

# Arrancar un contenedor que está parado
docker start api-segura
# docker start a1b3c4d5e6f7
# docker start a1b

# Borrar el contenedor (tiene que estar parado)
docker rm api-segura
# docker rm a1b3c4d5e6f7
# docker rm a1b

# Listar imágenes
docker images

# Borrar la imagen (nombre:tag, ID completo o prefijo)
docker rmi api-segura-crud
# docker rmi c3d4e5f6a7b8
# docker rmi c3d
```

**Nota sobre `--rm`:** en el `docker run` de arriba usamos `--rm`. Al hacer `docker stop`, Docker **borra** el contenedor solo. En ese caso no hay `docker start`: hay que volver a `docker run`.  
Si queréis practicar stop → start, lanzad **sin** `--rm`:

```bash
docker run --name api-segura -p 8000:8000 --env-file .env api-segura-crud
```

---

## Rutas

| Método | Ruta | ¿Clave? | Qué hace |
|--------|------|---------|----------|
| GET | `/health` | No | Pulso |
| GET | `/docs` | No | Swagger |
| GET/POST/PUT/DELETE | `/items…` | **Sí** (`?api_key=`) | CRUD (listado con `skip`/`limit`) |

---

## Pruebas a realizar

Sustituimos `<CLAVE>` por el valor de `API_KEY` (la del `.env` o la de `-e`).

1. `GET /health` → **200** `{"status":"ok"}` (sin clave)
2. `GET /items` → **401**
3. `GET /items?api_key=<CLAVE>` → **200** (8 ítems)
4. `GET /items?api_key=<CLAVE>&skip=0&limit=3` → primer trozo

---

## Cómo leer el Dockerfile

```dockerfile
# Imagen base oficial de Python (ligera)
FROM python:3.12-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar requirements.txt dentro del contenedor
COPY requirements.txt .

# Instalar las dependencias
RUN pip install -r requirements.txt

# Copiar el código de la API dentro del contenedor
COPY . .

# Puerto documentado (hay que publicarlo con -p al hacer run)
EXPOSE 8000

# Puerto 8000 por defecto; si existe la variable PORT, se usa esa
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
```

- `--host 0.0.0.0` → accesible desde fuera del contenedor.
- `${PORT:-8000}` → usa `PORT` si está definida; si no, 8000.
- `.dockerignore` → no metemos `.env`, `.venv`, `.git` en la imagen.

---

## Render (opcional)

1. Repo con esta carpeta como raíz del servicio (o monorepo apuntando aquí).
2. Web Service → **Docker**.
3. Environment: `API_KEY` (obligatoria); opcional `RATE_LIMIT_PER_MINUTE`, `CORS_ORIGINS`.
4. El hosting puede inyectar `PORT`; nuestro Dockerfile ya lo respeta.

Nunca subáis `.env` con secretos reales.

---

## Checklist

- [ ] Arranque local con uvicorn OK (`/health`, `/docs`)
- [ ] `docker build` OK
- [ ] Contenedor: `/health` → 200
- [ ] `/items` sin `api_key` → 401; con `?api_key=` → 200
- [ ] Secretos por `-e` / panel; `.env` en `.dockerignore`
- [ ] (Opcional) Deploy en la nube con `API_KEY` en el panel
