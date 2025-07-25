import os
from sqlmodel import SQLModel, create_engine

engine = create_engine(
    f"sqlite+{os.getenv("TURSO_DATABASE_URL")}?secure=true",
    connect_args={
        "auth_token": os.getenv("TURSO_AUTH_TOKEN"),
    },
)

def create_tables():
    SQLModel.metadata.create_all(engine)
