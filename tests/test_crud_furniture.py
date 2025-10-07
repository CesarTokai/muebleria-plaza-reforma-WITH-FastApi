from decimal import Decimal
import pytest
from fastapi import HTTPException

import app.crud_furniture as crud_furniture
import app.crud_category as crud_category
import app.schemas as schemas
import app.models as models


def test_create_furniture(db):
    # crear categoría primero
    cat = schemas.CategoryCreate(name="sala", description="Muebles de sala")
    cat_obj = crud_category.create_category(db, cat)

    f = schemas.FurnitureCreate(name="Sillon Test", description="Desc", price=1234.56, category_id=cat_obj.id)
    created = crud_furniture.create_furniture(db, f)

    assert created.id is not None
    assert created.name == "Sillon Test"
    # price stored como Decimal
    assert isinstance(created.price, Decimal)
    assert created.price == Decimal("1234.56")


def test_update_furniture_price(db):
    cat = schemas.CategoryCreate(name="comedor", description="Muebles de comedor")
    cat_obj = crud_category.create_category(db, cat)

    f = schemas.FurnitureCreate(name="Mesa Test", description="Desc", price=100.00, category_id=cat_obj.id)
    created = crud_furniture.create_furniture(db, f)

    update = schemas.FurnitureUpdate(price=150.25)
    updated = crud_furniture.update_furniture(db, created.id, update)

    assert isinstance(updated.price, Decimal)
    assert updated.price == Decimal("150.25")


def test_create_furniture_batch_rollback(db):
    # crear categoria y un mueble base
    cat = schemas.CategoryCreate(name="oficina", description="Muebles oficina")
    cat_obj = crud_category.create_category(db, cat)

    base = schemas.FurnitureCreate(name="ListaTest", description="Base", price=50.00, category_id=cat_obj.id)
    base_created = crud_furniture.create_furniture(db, base)

    # intentar crear batch donde uno es duplicado (mismo nombre+categoria) -> debe fallar y no crear el otro
    batch = [
        schemas.FurnitureCreate(name="ListaTest", description="Dup", price=10.00, category_id=cat_obj.id),
        schemas.FurnitureCreate(name="NuevoBatch", description="Ok", price=20.00, category_id=cat_obj.id),
    ]

    with pytest.raises(HTTPException):
        crud_furniture.create_furniture_batch(db, batch)

    # comprobar que no se creó 'NuevoBatch'
    q = db.query(models.Furniture).filter(models.Furniture.name == "NuevoBatch").all()
    assert len(q) == 0

    q2 = db.query(models.Furniture).filter(models.Furniture.name == "ListaTest").all()
    assert len(q2) == 1
