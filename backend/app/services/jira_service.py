"""
Jira integration service using atlassian-python-api / jira library.
Creates Jira issues from approved Gherkin test cases.
"""
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from jira import JIRA, JIRAError

logger = logging.getLogger(__name__)


def get_jira_client(base_url: str, email: str, api_token: str) -> JIRA:
    return JIRA(
        server=base_url,
        basic_auth=(email, api_token),
    )


def test_connection(base_url: str, email: str, api_token: str) -> dict:
    """Test Jira connection and return available projects."""
    try:
        client = get_jira_client(base_url, email, api_token)
        projects = client.projects()
        project_keys = [p.key for p in projects[:20]]
        return {"success": True, "message": "Connected successfully", "projects": project_keys}
    except JIRAError as e:
        return {"success": False, "message": f"Jira error: {e.text or str(e)}", "projects": None}
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {str(e)}", "projects": None}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def create_jira_issue(
    client: JIRA,
    project_key: str,
    issue_type: str,
    summary: str,
    description: str,
    labels: list[str],
    domain: str,
) -> dict:
    """Create a single Jira issue for a test case. Retries up to 3 times."""
    all_labels = list(set(labels + ["auto-generated", domain.lower()]))
    issue_dict = {
        "project": {"key": project_key},
        "summary": summary[:255],
        "description": description,
        "issuetype": {"name": issue_type},
        "labels": all_labels,
    }
    issue = client.create_issue(fields=issue_dict)
    server = client.server_url.rstrip("/")
    return {
        "jira_key": issue.key,
        "url": f"{server}/browse/{issue.key}",
    }


def inject_test_cases(
    test_cases: list[dict],
    base_url: str,
    email: str,
    api_token: str,
    project_key: str,
    issue_type: str,
    labels: list[str],
) -> dict:
    """
    Inject a list of approved test cases into Jira.
    Returns {injected: [...], failed: [...]}.
    """
    try:
        client = get_jira_client(base_url, email, api_token)
    except Exception as e:
        return {"injected": [], "failed": [{"error": str(e)}]}

    injected = []
    failed = []

    for tc in test_cases:
        try:
            result = create_jira_issue(
                client=client,
                project_key=project_key,
                issue_type=issue_type,
                summary=f"[{tc['domain']}] {tc['scenario']}",
                description=f"*Feature:* {tc['feature']}\n\n{{code:gherkin}}\n{tc['gherkin_text']}\n{{code}}",
                labels=labels,
                domain=tc.get("domain", "web"),
            )
            injected.append({"id": tc["id"], **result})
        except Exception as e:
            logger.error(f"Failed to create Jira issue for test case {tc['id']}: {e}")
            failed.append({"id": tc["id"], "error": str(e)})

    return {"injected": injected, "failed": failed}
