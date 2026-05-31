from fastapi import HTTPException, Depends
from sqlmodel import Session, select
from DormShareAPI.application.Services.Auth import get_current_user
from DormShareAPI.application.Data.DataBase import get_session
from DormShareAPI.application.Data.models import Item, User
from DormShareAPI.application.Data.PydenticModels import ItemCreate, ItemUpdate
from DormShareAPI.application.Data.models import UserRole
from sqlalchemy import select as sa_select
from sqlalchemy.orm import selectinload



async def create_item(item_data: ItemCreate, session: Session = Depends(get_session),
                      current_user: User = Depends(get_current_user)):
   try:
       db_item = Item(
           **item_data.model_dump(),
           owner_id=current_user.id
       )
       session.add(db_item)
       session.commit()
       session.refresh(db_item)
       return {
           "status" : "success",
           "item_id" : db_item.id
       }

   except Exception as e:
       session.rollback()
       print(f"Error: {e}")
       raise  HTTPException(status_code=500, detail="Can't save item to db")



async def get_items(session, current_user):
    try:
        statement = sa_select(Item).join(User, Item.owner_id == User.id).where(
            User.university == current_user.university
        ).options(
            selectinload(Item.images),
            selectinload(Item.reviews),
            selectinload(Item.owner)
        )



        items = session.execute(statement).scalars().all()
        return [
            {**item.__dict__, "owner_username": item.owner.username}
            for item in items
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {e}")



async def get_item_by_id(item_id, session, current_user):
    try:
        statement = sa_select(Item).where(Item.id == item_id).options(
            selectinload(Item.images),
            selectinload(Item.reviews),
            selectinload(Item.owner)
        )
        item = session.execute(statement).scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail=f"No item found by id: {item_id}")

        if item.owner.university != current_user.university:
            raise HTTPException(status_code=403, detail="Can't get info about an item from another university")

        return {**item.__dict__, "owner_username": item.owner.username}
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail="Problem occurred while ordering user by id")



async def get_items_by_category(category, session, current_user):
    try:
        statement = sa_select(Item).join(User, Item.owner_id == User.id).where(
            Item.category == category,
            User.university == current_user.university
        ).options(
            selectinload(Item.images),
            selectinload(Item.reviews),
            selectinload(Item.owner)
        )

        items = session.execute(statement).scalars().all()
        return [
            {**item.__dict__, "owner_username": item.owner.username}
            for item in items
        ]
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")



async def change_item_status(itemId, session, current_user):
    try:
        item = session.exec(select(Item).where(Item.id == itemId)).first()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        if item.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not enough permissions")


        item.is_available = not item.is_available

        session.add(item)
        session.commit()
        session.refresh(item)
        return item

    except HTTPException:
        raise

    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


async def delete_item(itemId, session, current_user):
    try:
        item = session.get(Item, itemId)

        if item is None:
            raise HTTPException(status_code=404, detail="item not found")


        if item.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        session.delete(item)
        session.commit()
    except HTTPException:
        raise

    except Exception as e:
        print(f"Something went wrong while deleting item: {e}")
        raise HTTPException(status_code=500, detail=f"Something went wrong while deleting item: {e}")


async def update_item(item_id, item_data: ItemUpdate, session, current_user):
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    if db_item.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")


    update_data = item_data.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(db_item, k, v)

    session.add(db_item)
    session.commit()
    session.refresh(db_item)

    return db_item