# Mueblería Plaza Reforma API - Guía de ejecución

## Prerrequisitos
- MySQL en ejecución (localhost por defecto).
- Python 3.10+.
- `.env` con estas variables (ya incluido): MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, y las de email si usas envío de correos.
- Este proyecto ya incluye un entorno virtual `.venv` (opcionalmente puedes usar uno nuevo).

## 1) Verificar MySQL
- Inicia el servicio MySQL:
  - Windows: Servicios -> MySQL -> Iniciar (o `net start MySQL` según tu instalación).
  - macOS/Linux (Homebrew/systemd): `brew services start mysql` o `sudo systemctl starlst mysql`.
- Asegúrate de que las credenciales del archivo `.env` sean válidas. La app intentará crear la base de datos automáticamente si no existe.

## 2) Activar el entorno virtual
- Windows (PowerShell):
  ```
  .\.venv\Scripts\Activate
  ```
- macOS/Linux (bash/zsh):
  ```
  source .venv/bin/activate
  ```

Si no tienes dependencias instaladas en este venv, instala (opcional):

# Mueblería Plaza Reforma API - Guía de ejecución

## Prerrequisitos
- MySQL en ejecución (localhost por defecto).
- Python 3.10+.
- `.env` con estas variables (ya incluido): MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, y las de email si usas envío de correos.
- Este proyecto ya incluye un entorno virtual `.venv` (opcionalmente puedes usar uno nuevo).

## 1) Verificar MySQL
- Inicia el servicio MySQL:
  - Windows: Servicios -> MySQL -> Iniciar (o `net start MySQL` según tu instalación).
  - macOS/Linux (Homebrew/systemd): `brew services start mysql` o `sudo systemctl starlst mysql`.
- Asegúrate de que las credenciales del archivo `.env` sean válidas. La app intentará crear la base de datos automáticamente si no existe.

## 2) Activar el entorno virtual
- Windows (PowerShell):
  ```
  .\.venv\Scripts\Activate
  ```
- macOS/Linux (bash/zsh):
  ```
  source .venv/bin/activate
  ```

Si no tienes dependencias instaladas en este venv, instala (opcional):


---

# CRUD de Publicaciones (Posts)

Esta sección documenta cómo funciona el CRUD de publicaciones y cómo consumirlo desde el frontend.

## Modelo y relaciones
- Tabla `furniture` (muebles) y tabla `posts` (publicaciones).
- Relación 1:N (un mueble puede tener varias publicaciones):
  - En SQLAlchemy: `Furniture.posts` y `Post.furniture` (back_populates).
  - Borrado en cascada: si eliminas un mueble, se eliminan sus publicaciones (`cascade="all, delete-orphan"`).
- Campos clave de `posts`:
  - `id`, `title`, `content`, `publication_date`, `furniture_id`, `created_at`, `updated_at`, `is_active`.
  - Borrado lógico: `is_active` controla si una publicación está visible.

Archivos relevantes:
- `app/models.py` → definiciones de modelos.
- `app/schemas.py` → Pydantic (validación I/O).
- `app/crud_post.py` → operaciones con la BD.
- `app/post_router.py` → endpoints FastAPI.
- `app/main.py` → incluye el router de posts.

## Autenticación y roles
- Crear, actualizar y eliminar publicaciones requiere usuario administrador.
- Endpoints protegidos usan `Depends(auth.get_admin_user)`.
- Para loguearte: `POST /login` → devuelve `access_token`.
- En llamadas protegidas agrega header: `Authorization: Bearer <access_token>`.

## Esquemas (schemas) de entrada/salida
- Entrada creación (`PostCreate`):
  - `title: str`, `content: str`, `furniture_id: int`.
- Entrada actualización (`PostUpdate`):
  - Parcial: `title?: str`, `content?: str`, `is_active?: bool`.
- Salida (`PostOut`):
  - `id, title, content, furniture_id, publication_date, created_at, updated_at, is_active`.

## Endpoints
Base: `/posts`

- POST `/` (admin) → Crear publicación
  - Body: `PostCreate`
  - Respuesta: `PostOut` (201)
- GET `/` → Listar publicaciones activas
  - Query: `skip`, `limit`
  - Respuesta: `PostOut[]`
- GET `/furniture/{furniture_id}` → Listar por mueble
  - Query: `skip`, `limit`
  - Respuesta: `PostOut[]`
- GET `/{post_id}` → Obtener una publicación por id
  - Respuesta: `PostOut` (404 si no existe o inactiva)
- PUT `/{post_id}` (admin) → Actualizar publicación
  - Body: `PostUpdate`
  - Respuesta: `PostOut`
- DELETE `/{post_id}` (admin) → Borrado lógico (soft delete)
  - Respuesta: 204 (no contenido)
- DELETE `/{post_id}/hard` (admin) → Borrado físico (hard delete)
  - Respuesta: 204 (no contenido)
- GET `/inactive` (admin) → Listar publicaciones inactivas (papelera)
  - Query: `skip`, `limit`
  - Respuesta: `PostOut[]`
- POST `/{post_id}/restore` (admin) → Restaurar una publicación (deshacer soft delete)
  - Respuesta: `PostOut`

## Comportamiento clave (backend)
- `create_post` verifica que `furniture_id` exista; si no, 404.
- `get_all_posts` solo devuelve `is_active == true` ordenado por `publication_date DESC`.
- `delete_post` marca `is_active = false` (no elimina de la BD).
- `hard_delete_post` elimina permanentemente el registro.

## Ejemplos de consumo

Curl (Windows PowerShell puede requerir comillas dobles):

1) Login y token
```
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@site.com\",\"password\":\"password123\"}"
```

2) Crear publicación (admin)
```
curl -X POST http://localhost:8000/posts/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Promo sofá\",\"content\":\"20% de descuento\",\"furniture_id\":1}"
```

3) Listar publicaciones
```
curl http://localhost:8000/posts?skip=0&limit=20
```

4) Publicaciones por mueble
```
curl http://localhost:8000/posts/furniture/1
```

5) Actualizar publicación (admin)
```
curl -X PUT http://localhost:8000/posts/5 \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Nuevo título\"}"
```

6) Soft delete (admin)
```
curl -X DELETE http://localhost:8000/posts/5 \
  -H "Authorization: Bearer <TOKEN>"
```

7) Hard delete (admin)
```
curl -X DELETE http://localhost:8000/posts/5/hard \
  -H "Authorization: Bearer <TOKEN>"
```

## Guía para el frontend (ejemplo con React)

Estructura típica de UI:
- Vista de lista: `/admin/posts` muestra tabla de publicaciones activas.
- Filtro por mueble: selector que pega a `/posts/furniture/{id}`.
- Formulario crear/editar: `/admin/posts/new` y `/admin/posts/:id/edit`.
- Acciones: Crear, Editar, Soft Delete, Hard Delete (esta última opcional, solo si se necesita limpiar definitivamente).

Flujos:
- Crear:
  1. Obtener token al login y guardarlo en `localStorage`.
  2. En el form, cargar lista de muebles para elegir `furniture_id` (GET `/furniture?limit=...`).
  3. Enviar POST `/posts/` con `Authorization: Bearer`.
- Editar:
  1. Cargar datos con GET `/posts/{id}`.
  2. Enviar PUT `/posts/{id}` con solo los campos cambiados.
- Eliminar (soft):
  1. Enviar DELETE `/posts/{id}` y actualizar la lista local filtrando `is_active`.

Ejemplo Axios (crear):
```js
import axios from 'axios';

const API = 'http://localhost:8000';
const token = localStorage.getItem('token');

export async function createPost(data) {
  const res = await axios.post(`${API}/posts/`, data, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data; // PostOut
}
```

Validaciones de UI:
- Título requerido y <= 255 chars.
- Contenido requerido.
- `furniture_id` debe existir (maneja 404 del backend mostrando mensaje tipo "El mueble no existe").

Manejo de errores comunes:
- 401/403: token ausente o no admin → redirigir a login o mostrar "No autorizado".
- 404: publicación o mueble no encontrado.
- 500: error de servidor → mostrar alerta genérica.

## Notas de diseño
- Usa paginación con `skip` y `limit` en listados largos.
- Para SEO o blog público, usa GET `/posts` (solo activos) y muestra `publication_date`.
- Para un panel de admin, considera vista de "Papelera" listando `is_active=false` si implementas un endpoint adicional de administración.


---

# Resumen de todas las APIs para desarrollo web

Además del CRUD de publicaciones, a continuación está la documentación completa de las APIs disponibles para construir el frontend.

- Base URL (local): http://localhost:8000
- Documentación interactiva: http://localhost:8000/docs
- Autenticación: Bearer token JWT en header Authorization: `Authorization: Bearer <token>`
- CORS: habilitado para `http://localhost:5173` y `http://127.0.0.1:5173`

## 1) Usuarios y Autenticación

### POST /register
- Crea usuario normal.
- Body (JSON): `{ "email": string, "password": string }`
- Respuesta: `UserOut` `{ id, email, is_active, created_at, is_admin }`
- Errores: 400 email en uso o password débil.

### POST /login
- Autentica y devuelve token.
- Body: `{ "email": string, "password": string }`
- Respuesta: `{ access_token, token_type: "bearer", user_id, is_admin }`
- Errores: 401 credenciales inválidas; 400 usuario inactivo.

### POST /request-reset
- Envía código de recuperación al email registrado.
- Body: `{ "email": string }`
- Respuesta: `{ msg }`

### POST /verify-code
- Verifica código de recuperación.
- Body: `{ "email": string, "code": string }`
- Respuesta: `{ msg }` (400 si inválido/expirado)

### POST /reset-password
- Cambia contraseña con código válido.
- Body: `{ "email": string, "code": string, "new_password": string }`
- Respuesta: `{ msg }`

### POST /admin (protegido, admin)
- Crea un usuario administrador.
- Header: `Authorization: Bearer <token>` (de un admin)
- Body: `{ "email": string, "password": string }`
- Respuesta: `UserOut`

Ejemplos cURL
```
# Registro
curl -X POST http://localhost:8000/register -H "Content-Type: application/json" -d "{\"email\":\"user@site.com\",\"password\":\"Pass1234\"}"

# Login
curl -X POST http://localhost:8000/login -H "Content-Type: application/json" -d "{\"email\":\"user@site.com\",\"password\":\"Pass1234\"}"

# Solicitar reset
curl -X POST http://localhost:8000/request-reset -H "Content-Type: application/json" -d "{\"email\":\"user@site.com\"}"
```

## 2) Muebles (Furniture)

Ruta base: `/furniture`

Esquemas
- FurnitureCreate: `{ name, description?, price>0, category, img_base64?, stock>=0?, brand?, color?, material?, dimensions? }`
- FurnitureUpdate: iguales pero opcionales
- FurnitureOut: FurnitureCreate + `{ id, created_at, updated_at, posts: PostOut[] }`

### POST /furniture/ (protegido, admin)
- Crea un mueble.
- Body: `FurnitureCreate`
- Respuesta: `FurnitureOut` (201)

### POST /furniture/batch (protegido, admin)
- Crea varios muebles en una sola llamada.
- Body: `FurnitureCreate[]`
- Respuesta: `FurnitureOut[]` (201)

### GET /furniture/
- Lista muebles con paginación y filtro por categoría.
- Query: `skip=0`, `limit=100`, `category?`
- Respuesta: `FurnitureOut[]`

### GET /furniture/search
- Búsqueda avanzada.
- Query: `term?` (coincide en nombre/descripcion), `category?`, `min_price?`, `max_price?`, `skip=0`, `limit=100`
- Respuesta: `FurnitureOut[]`

### GET /furniture/categories
- Devuelve categorías disponibles.
- Respuesta: `string[]`

### GET /furniture/{furniture_id}
- Obtiene un mueble por id.
- Respuesta: `FurnitureOut` (404 si no existe)

### PUT /furniture/{furniture_id} (protegido, admin)
- Actualiza parcialmente un mueble.
- Body: `FurnitureUpdate`
- Respuesta: `FurnitureOut`

### DELETE /furniture/{furniture_id} (protegido, admin)
- Elimina un mueble. También elimina en cascada sus publicaciones.
- Respuesta: 204

### Publicaciones anidadas bajo muebles

- GET /furniture/{furniture_id}/posts → Lista publicaciones activas de ese mueble. Query: `skip`, `limit`.
- POST /furniture/{furniture_id}/posts (admin) → Crea publicación para ese mueble. Body: `PostCreate` (se ignora si el `furniture_id` del body no coincide con la ruta).

Ejemplos cURL
```
# Crear mueble
curl -X POST http://localhost:8000/furniture/ -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d "{\"name\":\"Sofá\",\"price\":8999.99,\"category\":\"sala\"}"

# Buscar muebles palabra clave + rango de precio
curl "http://localhost:8000/furniture/search?term=sofa&min_price=5000&max_price=12000&limit=20"

# Posts de un mueble
curl http://localhost:8000/furniture/1/posts
```

## 3) Publicaciones (Posts)

Ya documentadas más arriba. Recordatorio rápido:
- Base: `/posts`
- Solo activos en listados; soft delete via DELETE `/posts/{id}`; hard delete via DELETE `/posts/{id}/hard`.
- Validaciones de título/contenido vía schemas Pydantic.

## 4) Consejos de integración Frontend

### Interceptor de Axios para token
```js
import axios from 'axios';

export const api = axios.create({ baseURL: 'http://localhost:8000' });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

### Flujo de auth en UI
- Registro → Login → Guardar `access_token` en `localStorage`.
- Mostrar/ocultar vistas admin según `is_admin` devuelto por /login.

### Manejo de imágenes base64
- `img_base64` acepta solo base64 válido. Puedes enviar string puro base64 o data URL (`data:image/png;base64,...`).
- Mantén tamaños razonables para no saturar la base de datos.

### Paginación y búsqueda
- Usa `skip` y `limit` en listados extensos.
- Para buscadores, debounced inputs y sincronizar querystring con la URL.

### Errores a contemplar en UI
- 401/403: Falta token o no admin → redirigir a login/mostrar mensaje.
- 404: Recurso no encontrado.
- 400: Validaciones de formulario (mensajes del backend).
- 500: Error general.

## 5) Notas de despliegue
- Cambia `allow_origins` de CORS en `app/main.py` para tu dominio en producción.
- Ajusta `ACCESS_TOKEN_EXPIRE_MINUTES` y `SECRET_KEY` en variables de entorno.
- Considera CDN/objeto de almacenamiento para imágenes en lugar de base64 en BD si el volumen crece.
