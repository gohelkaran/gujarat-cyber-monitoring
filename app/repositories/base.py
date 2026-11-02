"""
Generic Base Repository
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Provides parameterized queries via SQLAlchemy 2.0 ORM,
enforcing soft-deletion checks and avoiding SQL injection vulnerabilities.
"""

from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from app.core.database import Base
from app.utils.time_utils import utc_now

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic repository pattern ensuring data abstraction and standard security filters.
    """
    def __init__(self, model: Type[ModelT], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: Any, include_deleted: bool = False) -> Optional[ModelT]:
        """Fetches a single record by primary key."""
        stmt = select(self.model).where(self.model.id == id)
        if not include_deleted and hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[ModelT]:
        """Lists records with pagination constraints."""
        limit = min(limit, 500)  # Defense in depth against unbounded memory consumption
        stmt = select(self.model)
        if not include_deleted and hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted.is_(False))
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, instance: ModelT) -> ModelT:
        """Persists a new entity instance."""
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(self, id: Any, values: Dict[str, Any], updated_by: Optional[str] = None) -> Optional[ModelT]:
        """Safely updates fields on an existing record using parameterized statements."""
        instance = self.get_by_id(id)
        if not instance:
            return None

        if hasattr(self.model, "updated_at"):
            values["updated_at"] = utc_now()
        if updated_by and hasattr(self.model, "updated_by"):
            values["updated_by"] = updated_by

        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**values)
            .execution_options(synchronize_session="fetch")
        )
        self.db.execute(stmt)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def soft_delete(self, id: Any, deleted_by: Optional[str] = None) -> bool:
        """
        Marks an entity as soft-deleted to preserve forensic evidence integrity.
        Physical deletion should be reserved for strict data retention purge workers.
        """
        instance = self.get_by_id(id)
        if not instance:
            return False

        if hasattr(instance, "is_deleted"):
            instance.is_deleted = True
            if hasattr(instance, "deleted_at"):
                instance.deleted_at = utc_now()
            if deleted_by and hasattr(instance, "deleted_by"):
                instance.deleted_by = deleted_by
            self.db.commit()
            return True

        # Fallback to physical deletion if model doesn't support soft delete
        self.db.delete(instance)
        self.db.commit()
        return True
