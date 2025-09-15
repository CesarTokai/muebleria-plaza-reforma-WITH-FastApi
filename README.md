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
