from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import models, schemas, crud, auth, database, email_utils
from .furniture_router import router as furniture_router
from .post_router import router as post_router

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Mueblería Plaza Reforma API", 
              description="API para gestión de muebles y publicaciones",
              version="2.0")


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",  "http://127.0.0.1:5173"],  # o ["*"] para todos los orígenes (no recomendado en producción)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", response_model=schemas.UserOut, tags=["usuarios"])
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario en el sistema.
    """
    return crud.create_user(db, user)

@app.post("/login", tags=["usuarios"])
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Autentica un usuario y devuelve un token de acceso.
    """
    user_db = crud.authenticate_user(db, user.email, user.password)
    if not user_db:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    access_token = auth.create_access_token({"sub": user_db.email})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user_db.id, "is_admin": user_db.is_admin}

@app.post("/request-reset", tags=["usuarios"])
async def request_reset(data: schemas.RequestReset, db: Session = Depends(get_db)):
    """
    Solicita un código de recuperación de contraseña que será enviado por email.
    """
    user = crud.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="Email no encontrado")
    code = crud.set_reset_code(db, user)
    await email_utils.send_reset_code_email(user.email, code)
    return {"msg": "Código enviado al email"}

@app.post("/verify-code", tags=["usuarios"])
def verify_code(data: schemas.VerifyCode, db: Session = Depends(get_db)):
    """
    Verifica que el código de recuperación proporcionado sea válido.
    """
    if not crud.verify_reset_code(db, data.email, data.code):
        raise HTTPException(status_code=400, detail="Código inválido o expirado")
    return {"msg": "Código válido"}

@app.post("/reset-password", tags=["usuarios"])
def reset_password(data: schemas.ResetPassword, db: Session = Depends(get_db)):
    """
    Restablece la contraseña usando el código de recuperación.
    """
    if not crud.reset_password(db, data.email, data.code, data.new_password):
        raise HTTPException(status_code=400, detail="Código inválido o expirado")
    return {"msg": "Contraseña actualizada"}

@app.post("/admin", response_model=schemas.UserOut, tags=["admin"])
def create_admin(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: dict = Depends(auth.get_admin_user)):
    """
    Crea un nuevo usuario administrador (solo otros administradores pueden hacerlo).
    """
    return crud.create_admin_user(db, user)

@app.get("/", tags=["general"])
def read_root():
    """
    Endpoint raíz que muestra información básica de la API.
    """
    return {"message": "Bienvenido a la API de Mueblería Plaza Reforma", 
            "version": "2.0",
            "docs": "/docs"}

# Incluir routers
app.include_router(furniture_router)
app.include_router(post_router)
