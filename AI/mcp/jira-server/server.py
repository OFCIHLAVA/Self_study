import os
from dotenv import load_dotenv
import httpx
from mcp.server.fastmcp import FastMCP

load_dotenv()

JIRA_URL = os.environ["JIRA_URL"].rstrip("/")
JIRA_TOKEN = os.environ["JIRA_TOKEN"]
JIRA_USERNAME = os.environ.get("JIRA_USERNAME", "")

HEADERS = {"Authorization": f"Bearer {JIRA_TOKEN}", "Content-Type": "application/json"}

mcp = FastMCP("jira")


def _get(path: str, params: dict | None = None) -> dict:
    r = httpx.get(
        f"{JIRA_URL}/rest/api/2{path}",
        headers=HEADERS,
        params=params,
        verify=False,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def _post(path: str, json: dict) -> dict:
    r = httpx.post(
        f"{JIRA_URL}/rest/api/2{path}",
        headers=HEADERS,
        json=json,
        verify=False,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def _put(path: str, json: dict) -> httpx.Response:
    r = httpx.put(
        f"{JIRA_URL}/rest/api/2{path}",
        headers=HEADERS,
        json=json,
        verify=False,
        timeout=30,
    )
    r.raise_for_status()
    return r


def _delete(path: str) -> httpx.Response:
    r = httpx.delete(
        f"{JIRA_URL}/rest/api/2{path}", headers=HEADERS, verify=False, timeout=30
    )
    r.raise_for_status()
    return r


@mcp.tool()
def get_current_user() -> str:
    """Get the configured Jira username for the current user."""
    return JIRA_USERNAME or "No JIRA_USERNAME configured."


@mcp.tool()
def get_issue(issue_key: str) -> str:
    """Get a Jira issue by key (e.g. PROJ-123). Returns summary, status, assignee, description, and comments."""
    data = _get(f"/issue/{issue_key}", {"expand": "renderedFields"})
    f = data["fields"]
    parts = [
        f"**{issue_key}: {f.get('summary', '')}**",
        f"Status: {f.get('status', {}).get('name', '?')}",
        f"Type: {f.get('issuetype', {}).get('name', '?')}",
        f"Assignee: {(f.get('assignee') or {}).get('displayName', 'Unassigned')}",
        f"Priority: {(f.get('priority') or {}).get('name', '?')}",
        f"\n## Description\n{f.get('description') or 'No description'}",
    ]
    comments = (f.get("comment") or {}).get("comments", [])
    if comments:
        parts.append(f"\n## Comments ({len(comments)})")
        for c in comments[-10:]:
            parts.append(f"- **{c['author']['displayName']}**: {c.get('body', '')}")
    return "\n".join(parts)


@mcp.tool()
def search_issues(jql: str, max_results: int = 10) -> str:
    """Search Jira issues using JQL. Example: 'project = PROJ AND status = Open'"""
    data = _get(
        "/search",
        {
            "jql": jql,
            "maxResults": max_results,
            "fields": "summary,status,assignee,priority",
        },
    )
    if not data.get("issues"):
        return "No issues found."
    lines = [f"Found {data['total']} issues (showing {len(data['issues'])}):\n"]
    for issue in data["issues"]:
        f = issue["fields"]
        assignee = (f.get("assignee") or {}).get("displayName", "Unassigned")
        lines.append(
            f"- **{issue['key']}**: {f['summary']} [{f['status']['name']}] ({assignee})"
        )
    return "\n".join(lines)


@mcp.tool()
def get_transitions(issue_key: str) -> str:
    """Get available status transitions for an issue."""
    data = _get(f"/issue/{issue_key}/transitions")
    if not data.get("transitions"):
        return "No transitions available."
    return "\n".join(f"- {t['name']} (id: {t['id']})" for t in data["transitions"])


@mcp.tool()
def create_issue(
    project_key: str,
    summary: str,
    issue_type: str = "Task",
    description: str = "",
    components: list[str] | None = None,
    epic_link: str | None = None,
) -> str:
    """Create a new Jira issue. Returns the created issue key.

    Args:
        project_key: Jira project key (e.g. "INFR")
        summary: Issue summary/title
        issue_type: Issue type name (default "Task")
        description: Issue description
        components: List of component names
        epic_link: Epic issue key to link this issue to (e.g. "PROJ-100"). Uses customfield_10005 (Epic Link).
    """
    fields = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": issue_type},
    }
    if description:
        fields["description"] = description
    if components:
        fields["components"] = [{"name": c} for c in components]
    if epic_link:
        fields["customfield_10005"] = epic_link
    data = _post("/issue", {"fields": fields})
    return f"Created {data['key']}: {summary}"


@mcp.tool()
def add_issue_link(
    inward_issue: str, outward_issue: str, link_type: str = "Relates"
) -> str:
    """Add a link between two Jira issues.

    Args:
        inward_issue: The issue key for the inward side (e.g. "PROJ-1")
        outward_issue: The issue key for the outward side (e.g. "PROJ-2")
        link_type: Link type name. Common values: "Relates", "Blocks", "Cloners", "Duplicate", "Epic-Story Link".
                   For "Blocks": inward_issue "is blocked by" outward_issue, outward_issue "blocks" inward_issue.
    """
    payload = {
        "type": {"name": link_type},
        "inwardIssue": {"key": inward_issue},
        "outwardIssue": {"key": outward_issue},
    }
    r = httpx.post(
        f"{JIRA_URL}/rest/api/2/issueLink",
        headers=HEADERS,
        json=payload,
        verify=False,
        timeout=30,
    )
    r.raise_for_status()
    return f"Linked {inward_issue} <-> {outward_issue} (type: {link_type})"


@mcp.tool()
def update_issue(
    issue_key: str,
    summary: str | None = None,
    description: str | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    components: list[str] | None = None,
    epic_link: str | None = None,
    labels: list[str] | None = None,
) -> str:
    """Update fields on an existing Jira issue. Only provided fields are changed.

    Args:
        issue_key: Issue key (e.g. "PROJ-123")
        summary: New summary/title
        description: New description
        assignee: Username to assign (use "" to unassign)
        priority: Priority name (e.g. "High", "Medium")
        components: Replace components list (component names)
        epic_link: Epic issue key (customfield_10005)
        labels: Replace labels list
    """
    fields: dict = {}
    if summary is not None:
        fields["summary"] = summary
    if description is not None:
        fields["description"] = description
    if assignee is not None:
        fields["assignee"] = {"name": assignee} if assignee else None
    if priority is not None:
        fields["priority"] = {"name": priority}
    if components is not None:
        fields["components"] = [{"name": c} for c in components]
    if epic_link is not None:
        fields["customfield_10005"] = epic_link or None
    if labels is not None:
        fields["labels"] = labels
    if not fields:
        return "No fields to update."
    _put(f"/issue/{issue_key}", {"fields": fields})
    return f"Updated {issue_key}"


@mcp.tool()
def delete_issue(issue_key: str, delete_subtasks: bool = False) -> str:
    """Delete a Jira issue.

    Args:
        issue_key: Issue key to delete (e.g. "PROJ-123")
        delete_subtasks: Also delete subtasks (default False)
    """
    path = f"/issue/{issue_key}?deleteSubtasks={'true' if delete_subtasks else 'false'}"
    _delete(path)
    return f"Deleted {issue_key}"


if __name__ == "__main__":
    mcp.run()
