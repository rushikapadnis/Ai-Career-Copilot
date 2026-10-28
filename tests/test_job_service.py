
from app.db.session import SessionLocal
from app.services.job_service import save_discovered_jobs


def main():
    # Read real listings already saved from the previous
    # Job Discovery Agent run, if you have them available.
    print(
        "Job persistence service imported successfully. "
        "Next, call save_discovered_jobs(db, jobs) "
        "with the actual jobs returned by the MCP tool."
    )


if __name__ == "__main__":
    main()
