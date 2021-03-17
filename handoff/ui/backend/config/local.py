import os

DATABASE_URL = "sqlite:///./handoff.db"
# DATABASE_URL = "sqlite+pysqlcipher://:" + os.environ.get("SQLITE_ENCRYPTION_KEY", "") +"@/./handoff.db"
# DATABASE_URL = "postgresql://user:password@postgresserver/db"

# CORS
cors_origins = [
        "http://localhost",
        "http://localhost:8000",
]
