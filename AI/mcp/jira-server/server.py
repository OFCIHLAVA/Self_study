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
    """Get the configured Jira username for the current session.

    Returns the JIRA_USERNAME from the server's environment configuration.
    Use this to identify who will be the actor for issue assignments, comments,
    and audit trails. Useful before calling update_issue with an assignee.

    Returns:
        The Jira username string, or a message indicating no username is configured.

    Example:
        >>> get_current_user()
        "john.doe"
    """
    return JIRA_USERNAME or "No JIRA_USERNAME configured."


def _format_links(fields: dict) -> list[str]:
    """Extract epic link and issue links from fields."""
    parts = []
    epic = fields.get("customfield_10005")
    if epic:
        parts.append(f"Epic Link: {epic}")
    links = fields.get("issuelinks") or []
    if links:
        parts.append(f"\n## Linked Issues ({len(links)})")
        for link in links:
            if "inwardIssue" in link:
                i = link["inwardIssue"]
                direction = link["type"]["inward"]
                parts.append(f"- {direction} **{i['key']}**: {i['fields']['summary']} [{i['fields']['status']['name']}]")
            elif "outwardIssue" in link:
                o = link["outwardIssue"]
                direction = link["type"]["outward"]
                parts.append(f"- {direction} **{o['key']}**: {o['fields']['summary']} [{o['fields']['status']['name']}]")
    return parts


@mcp.tool()
def get_issue(issue_key: str) -> str:
    """Retrieve full details of a single Jira issue by its key.

    Fetches comprehensive issue data including summary, status, type, assignee,
    priority, epic link, all linked issues (with their statuses), the full
    description, and the last 10 comments. This is the primary tool for
    inspecting an issue's current state.

    Args:
        issue_key: The Jira issue key, e.g. "PROJ-123" or "INFR-42".

    Returns:
        A formatted markdown string containing:
        - Title line: **PROJ-123: Issue summary**
        - Status, Type, Assignee, Priority fields
        - Epic Link (if set) and Linked Issues section
        - Full description text
        - Last 10 comments with author names

    Example:
        >>> get_issue("PROJ-123")
        "**PROJ-123: Fix login bug**\\nStatus: In Progress\\nType: Bug\\n..."
    """
    data = _get(f"/issue/{issue_key}", {"expand": "renderedFields"})
    f = data["fields"]
    parts = [
        f"**{issue_key}: {f.get('summary', '')}**",
        f"Status: {f.get('status', {}).get('name', '?')}",
        f"Type: {f.get('issuetype', {}).get('name', '?')}",
        f"Assignee: {(f.get('assignee') or {}).get('displayName', 'Unassigned')}",
        f"Priority: {(f.get('priority') or {}).get('name', '?')}",
    ]
    parts.extend(_format_links(f))
    parts.append(f"\n## Description\n{f.get('description') or 'No description'}")
    comments = (f.get("comment") or {}).get("comments", [])
    if comments:
        parts.append(f"\n## Comments ({len(comments)})")
        for c in comments[-10:]:
            parts.append(f"- **{c['author']['displayName']}**: {c.get('body', '')}")
    return "\n".join(parts)


@mcp.tool()
def get_issue_links(issue_key: str) -> str:
    """Retrieve only the epic link and linked issues for a Jira issue.

    A lightweight alternative to get_issue when you only need relationship
    data. Returns the epic this issue belongs to (via customfield_10005)
    and all issue links (blocks, relates to, duplicates, etc.) with their
    summaries and statuses.

    Args:
        issue_key: The Jira issue key, e.g. "PROJ-123".

    Returns:
        A formatted markdown string with the issue title, epic link (if any),
        and a list of linked issues grouped by link direction. Returns
        "No epic link or linked issues." if none exist.

    Example:
        >>> get_issue_links("PROJ-123")
        "**PROJ-123: Fix login bug**\\nEpic Link: PROJ-100\\n\\n## Linked Issues (2)\\n- blocks **PROJ-124**: Deploy fix [Open]\\n- is blocked by **PROJ-122**: Auth refactor [Done]"
    """
    data = _get(f"/issue/{issue_key}", {"fields": "customfield_10005,issuelinks,summary"})
    f = data["fields"]
    parts = [f"**{issue_key}: {f.get('summary', '')}**"]
    link_parts = _format_links(f)
    if link_parts:
        parts.extend(link_parts)
    else:
        parts.append("No epic link or linked issues.")
    return "\n".join(parts)


@mcp.tool()
def search_issues(jql: str, max_results: int = 10) -> str:
    """Search for Jira issues using JQL (Jira Query Language).

    Executes a JQL query and returns a summary list of matching issues.
    Each result includes the issue key, summary, status, and assignee.
    Use this to find issues by project, status, assignee, labels, or any
    JQL-supported criteria.

    Args:
        jql: A valid JQL query string. Supports all standard JQL operators
             and fields (project, status, assignee, priority, labels, etc.).
        max_results: Maximum number of issues to return (default 10, max
                     depends on Jira server config, typically 1000).

    Returns:
        A formatted markdown string showing total match count and a bullet
        list of issues with key, summary, status, and assignee. Returns
        "No issues found." if the query matches nothing.

    Example:
        >>> search_issues("project = INFR AND status = Open", max_results=5)
        "Found 42 issues (showing 5):\\n\\n- **INFR-10**: Setup CI pipeline [Open] (john.doe)\\n..."

        >>> search_issues("assignee = currentUser() AND status != Done")
        "Found 3 issues (showing 3):\\n\\n- **PROJ-5**: Review PR [In Review] (jane.smith)\\n..."
    """
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
    """Get the available workflow transitions for a Jira issue.

    Returns the list of status transitions that can be performed on the
    issue in its current state. Each transition includes its name and ID.
    Use the transition IDs with the Jira API to move issues through the
    workflow (e.g. "To Do" -> "In Progress" -> "Done").

    Note: Available transitions depend on the issue's current status and
    the project's workflow configuration.

    Args:
        issue_key: The Jira issue key, e.g. "PROJ-123".

    Returns:
        A newline-separated list of transitions in the format
        "- TransitionName (id: 123)", or "No transitions available."
        if the issue has no valid transitions from its current state.

    Example:
        >>> get_transitions("PROJ-123")
        "- Start Progress (id: 21)\\n- Done (id: 31)\\n- Won't Fix (id: 41)"
    """
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
    """Create a new Jira issue in the specified project.

    Creates an issue with the given fields and returns the newly created
    issue key. Supports setting the issue type, description, components,
    and epic link at creation time. For additional fields (assignee, priority,
    labels), use update_issue after creation.

    Args:
        project_key: The Jira project key where the issue will be created,
                     e.g. "INFR", "PROJ".
        summary: The issue title/summary. Keep it concise and descriptive.
        issue_type: The issue type name (default "Task"). Common values:
                    "Task", "Bug", "Story", "Epic", "Sub-task".
                    Must match an issue type configured in the target project.
        description: Plain-text issue description body. Supports Jira wiki
                     markup for formatting.
        components: Optional list of component names to assign, e.g.
                    ["Backend", "API"]. Components must already exist in
                    the project.
        epic_link: Optional epic issue key to link this issue under, e.g.
                   "PROJ-100". Sets the Epic Link field (customfield_10005).

    Returns:
        A confirmation string with the created issue key and summary,
        e.g. "Created PROJ-456: Implement caching layer".

    Example:
        >>> create_issue("INFR", "Setup monitoring dashboard", issue_type="Task",
        ...              description="Deploy Grafana dashboards for prod",
        ...              components=["Monitoring"], epic_link="INFR-10")
        "Created INFR-55: Setup monitoring dashboard"
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
    """Create a link between two existing Jira issues.

    Establishes a typed relationship between two issues. The link direction
    matters — for directional link types like "Blocks", the inward_issue
    receives the inward label and the outward_issue receives the outward label.

    Common link types and their semantics:
    - "Relates": inward_issue "relates to" outward_issue (symmetric).
    - "Blocks": outward_issue "blocks" inward_issue; inward_issue "is blocked by" outward_issue.
    - "Cloners": inward_issue "is cloned by" outward_issue.
    - "Duplicate": inward_issue "is duplicated by" outward_issue.

    Args:
        inward_issue: The issue key for the inward side of the link, e.g. "PROJ-1".
        outward_issue: The issue key for the outward side of the link, e.g. "PROJ-2".
        link_type: The link type name (default "Relates"). Must match a link type
                   configured in the Jira instance. Use get_issue_links to see
                   existing link types on issues.

    Returns:
        A confirmation string, e.g. "Linked PROJ-1 <-> PROJ-2 (type: Blocks)".

    Example:
        >>> add_issue_link("PROJ-2", "PROJ-1", link_type="Blocks")
        "Linked PROJ-2 <-> PROJ-1 (type: Blocks)"
        # Result: PROJ-1 "blocks" PROJ-2; PROJ-2 "is blocked by" PROJ-1
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
    """Update one or more fields on an existing Jira issue.

    Only the fields you provide will be modified — all other fields remain
    unchanged. Pass an empty string for assignee to unassign, or an empty
    string for epic_link to remove the epic association.

    Note: This does NOT change issue status. Use get_transitions to find
    available transitions and the Jira transition API to move issues through
    the workflow.

    Args:
        issue_key: The Jira issue key to update, e.g. "PROJ-123".
        summary: New issue title/summary. None to leave unchanged.
        description: New description body (Jira wiki markup). None to leave unchanged.
        assignee: Jira username to assign. Use "" (empty string) to unassign.
                  None to leave unchanged. Use get_current_user to get your username.
        priority: Priority name, e.g. "Highest", "High", "Medium", "Low", "Lowest".
                  None to leave unchanged.
        components: Full replacement list of component names, e.g. ["Backend", "API"].
                    This replaces all existing components. None to leave unchanged.
        epic_link: Epic issue key to set (customfield_10005), e.g. "PROJ-100".
                   Use "" (empty string) to remove the epic link. None to leave unchanged.
        labels: Full replacement list of labels, e.g. ["urgent", "backend"].
                This replaces all existing labels. None to leave unchanged.

    Returns:
        A confirmation string "Updated PROJ-123", or "No fields to update."
        if all arguments are None.

    Example:
        >>> update_issue("PROJ-123", assignee="john.doe", priority="High",
        ...              labels=["urgent", "backend"])
        "Updated PROJ-123"

        >>> update_issue("PROJ-123", assignee="")  # unassign
        "Updated PROJ-123"
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
    """Permanently delete a Jira issue.

    WARNING: This action is irreversible. The issue and all its data
    (comments, attachments, worklogs) will be permanently removed.
    If the issue has subtasks, you must set delete_subtasks=True or
    the deletion will fail.

    Args:
        issue_key: The Jira issue key to delete, e.g. "PROJ-123".
        delete_subtasks: If True, also delete all subtasks of this issue.
                         If False (default) and the issue has subtasks,
                         the Jira API will return an error.

    Returns:
        A confirmation string, e.g. "Deleted PROJ-123".

    Example:
        >>> delete_issue("PROJ-123")
        "Deleted PROJ-123"

        >>> delete_issue("PROJ-100", delete_subtasks=True)
        "Deleted PROJ-100"
    """
    path = f"/issue/{issue_key}?deleteSubtasks={'true' if delete_subtasks else 'false'}"
    _delete(path)
    return f"Deleted {issue_key}"


if __name__ == "__main__":
    mcp.run()
