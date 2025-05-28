from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import models, schemas, crud, auth, database, email_utils

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)

@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    user_db = crud.authenticate_user(db, user.email, user.password)
    if not user_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = auth.create_access_token({"sub": user_db.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/request-reset")
async def request_reset(data: schemas.RequestReset, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")
    code = crud.set_reset_code(db, user)
    await email_utils.send_email(
        "Código de recuperación",
        user.email,
        f"Tu código de recuperación es: {code}"
    )
    return {"msg": "Código enviado al email"}

@app.post("/verify-code")
def verify_code(data: schemas.VerifyCode, db: Session = Depends(get_db)):
    if not crud.verify_reset_code(db, data.email, data.code):
        raise HTTPException(status_code=400, detail="Código inválido o expirado")
    return {"msg": "Código válido"}

@app.post("/reset-password")
def reset_password(data: schemas.ResetPassword, db: Session = Depends(get_db)):
    if not crud.reset_password(db, data.email, data.code, data.new_password):
        raise HTTPException(status_code=400, detail="Código inválido o expirado")
    return {"msg": "Contraseña actualizada"}
