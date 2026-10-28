from sqlalchemy import text

from app.db.session import engine


def test_database_connection():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), version()")
        )
        database_name, version = result.one()

        print(f"Database: {database_name}")
        print(f"PostgreSQL: {version}")

        assert database_name == "career_copilot"


if __name__ == "__main__":
    test_database_connection()
    print("Database connection successful!")