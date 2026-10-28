
from mcp_servers.job_discovery_server import _get_json

def main():
    print("Testing The Muse provider adapter directly...")

    data = _get_json("/jobs", {"page": 0})

    print("Provider request successful")
    print("Total jobs reported:", data.get("total"))
    print("Jobs on this page:", len(data.get("results", [])))

    for job in data.get("results", [])[:5]:
        company = job.get("company") or {}
        print(
            "-",
            job.get("name"),
            "|",
            company.get("name"),
            "|",
            job.get("publication_date"),
        )


if __name__ == "__main__":
    main()
