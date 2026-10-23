from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models import User, Collection, Resource
from app.schemas import CollectionOut, CollectionCreate, CollectionUpdate
from app.services.extractor import ensure_default_collections
from app.api.deps import get_current_user

router = APIRouter(prefix="/collections", tags=["Collections"])

@router.get("", response_model=List[CollectionOut])
def list_collections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ensure_default_collections(db, current_user.id)
    collections = db.query(Collection).filter(Collection.user_id == current_user.id).all()
    results = []
    for c in collections:
        count = len(c.resources)
        co = CollectionOut.from_orm(c)
        co.resource_count = count
        results.append(co)
    return results

@router.post("", response_model=CollectionOut)
def create_collection(
    payload: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    col = Collection(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description or "",
        color=payload.color or "blue",
        icon=payload.icon or "folder",
        is_smart=payload.is_smart or False,
        rules=payload.rules or {},
        is_system=False
    )
    db.add(col)
    db.commit()
    db.refresh(col)
    co = CollectionOut.from_orm(col)
    co.resource_count = 0
    return co

@router.get("/{collection_id}", response_model=CollectionOut)
def get_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    col = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found.")
    co = CollectionOut.from_orm(col)
    co.resource_count = len(col.resources)
    return co

@router.patch("/{collection_id}", response_model=CollectionOut)
def update_collection(
    collection_id: int,
    payload: CollectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    col = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found.")

    for k, v in payload.dict(exclude_unset=True).items():
        setattr(col, k, v)

    db.commit()
    db.refresh(col)
    co = CollectionOut.from_orm(col)
    co.resource_count = len(col.resources)
    return co

@router.delete("/{collection_id}")
def delete_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    col = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found.")

    # Remove associations without deleting the resources
    col.resources.clear()
    db.delete(col)
    db.commit()
    return {"status": "success", "message": "Collection deleted successfully. Saved resources remain safe."}

@router.post("/{collection_id}/resources/{resource_id}")
def add_resource_to_collection(
    collection_id: int,
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    col = db.query(Collection).filter(Collection.id == collection_id, Collection.user_id == current_user.id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found.")
    res = db.query(Resource).filter(Resource.id == resource_id, Resource.user_id == current_user.id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found.")

    if res not in col.resources:
        col.resources.append(res)
        db.commit()

    return {"status": "success", "message": "Resource added to collection."}

@router.delete("/{collection_id}/resources/{resource_id}")
def remove_resource_from_collection(
    collection_id: int,
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    col = db.query(Collection).filter(Collection.id == collection_id, Collection.user_id == current_user.id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found.")
    res = db.query(Resource).filter(Resource.id == resource_id, Resource.user_id == current_user.id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found.")

    if res in col.resources:
        col.resources.remove(res)
        db.commit()

    return {"status": "success", "message": "Resource removed from collection."}
