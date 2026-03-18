from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import MetaData
import uuid

class Base(DeclarativeBase):
    metadata = MetaData()

    # Common columns can be added here, e.g., id, created_at, updated_at
    # We'll let each model define its own id type for flexibility