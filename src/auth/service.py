from src.config import SUPER_USER_EMAIL, SUPER_USER_PASSWORD
from src.utils.unitofwork import IUnitOfWork
from src.utils.utils import get_password_hash, verify_password
from .exceptions import (
    validate_user_existence,
    validate_user_authentication,
    credentials_exception,
    user_already_exists_exception,
)
from .jwt import create_access_token, decode_token
from .schemas import UserCreate, UserUpdate, PasswordChange, SuperUser


class UserService:
    async def create_user(self, uow: IUnitOfWork, user: UserCreate,  role: str = "подписчик"):
        user_dict = user.model_dump()
        async with uow:
            hashed_password = get_password_hash(user.password)

            user_dict["hashed_password"] = hashed_password
            user_dict["role"] = role
            del user_dict["password"]

            existing_user = await uow.users.find_one(email=user.email)
            if existing_user:
                raise user_already_exists_exception

            user_id = await uow.users.add_one(user_dict)
            await uow.commit()
            return {
                "access_token": create_access_token({"sub": str(user_id)}),
                # "refresh_token": create_refresh_token({"sub": str(user_id)}),
            }
    async def create_superuser(self, uow: IUnitOfWork, user):
        user_dict = user.model_dump()
        async with uow:
            hashed_password = get_password_hash(user.password)

            user_dict["hashed_password"] = hashed_password
            user_dict["is_superuser"] = True
            del user_dict["password"]

            existing_user = await uow.users.find_one(email=user.email)
            if existing_user:
                raise user_already_exists_exception

            user_id = await uow.users.add_one(user_dict)
            await uow.commit()
            return {
                "access_token": create_access_token({"sub": str(user_id)}),
                # "refresh_token": create_refresh_token({"sub": str(user_id)}),
            }

    async def update_superuser(self, uow: IUnitOfWork, user: SuperUser):
        user_dict = user.model_dump()
        async with uow:
            hashed_password = get_password_hash(user.password)
            user_dict["hashed_password"] = hashed_password
            user_dict["is_superuser"] = True
            del user_dict["password"]

            existing_user = await uow.users.find_one(email=user.email)
            if existing_user:
                await uow.users.edit_one(existing_user.id, user_dict)
                user_id = existing_user.id
            else:
                user_id = await uow.users.add_one(user_dict)

            await uow.commit()
            return {
                "access_token": create_access_token({"sub": str(user_id)}),
                # "refresh_token": create_refresh_token({"sub": str(user_id)}),
            }

    async def create_default_superuser(self, uow: IUnitOfWork):
        superuser_data = SuperUser(
            email=SUPER_USER_EMAIL,
            password=SUPER_USER_PASSWORD,
            is_superuser=True
        )
        await self.update_superuser(uow, superuser_data)


    async def authenticate_user(self, uow: IUnitOfWork, email: str, password: str):
        async with uow:
            user = await uow.users.find_one(email=email)
            validate_user_authentication(user)

            user.is_verified = True
            await uow.users.edit_one(user.id, {"is_verified": True})
            await uow.commit()
            return {
                "access_token": create_access_token({"sub": str(user.id)}),
                # "refresh_token": create_refresh_token({"sub": str(user.id)}),
            }

    async def get_user(self, uow: IUnitOfWork, user_id: int):
        async with uow:
            user = await uow.users.find_one(id=user_id)
            validate_user_existence(user)
            return user.to_read_model()

    async def get_all_users(self, uow: IUnitOfWork):
        async with uow:
            users = await uow.users.find_all()
            return users

    async def update_user(self, uow: IUnitOfWork, user_id: int, user: UserUpdate):
        user_data = user.model_dump()
        async with uow:
            existing_user = await uow.users.find_one(id=user_id)
            validate_user_existence(existing_user)
            await uow.users.edit_one(user_id, user_data)
            await uow.commit()

    async def delete_user(self, uow: IUnitOfWork, user_id: int):
        async with uow:
            user = await uow.users.find_one(id=user_id)
            validate_user_existence(user)
            await uow.users.delete_one(id=user_id)
            await uow.commit()

    async def change_password(self, uow: IUnitOfWork, user_id: int, password_data: PasswordChange):
        async with uow:
            user = await uow.users.find_one(id=user_id)
            validate_user_existence(user)
            if not verify_password(password_data.old_password, user.hashed_password):
                validate_user_authentication(None)
            user.hashed_password = get_password_hash(password_data.new_password)
            await uow.users.edit_one(user_id, {"hashed_password": user.hashed_password})
            await uow.commit()

    async def refresh_access_token(self, refresh_token: str):
        payload = decode_token(refresh_token)
        if not payload:
            raise credentials_exception
        user_id = payload.get("sub")
        return create_access_token({"sub": user_id})

    async def logout(self, refresh_token: str):
        pass
