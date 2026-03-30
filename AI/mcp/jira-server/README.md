# Jira MCP Server

An MCP (Model Context Protocol) server that gives Kiro CLI direct access to your Jira instance. Once configured, you can ask Kiro to search, create, update, and manage Jira issues through natural conversation.

NOTE: This MCP is specificaly designed for self hosted custom Jira server, but the general idea is applicable for other domains also.

## Available Tools

| Tool | Description |
|------|-------------|
| `get_issue` | Fetch issue details by key (e.g. `INFR-123`) |
| `search_issues` | Search issues using JQL |
| `create_issue` | Create a new issue |
| `update_issue` | Update fields on an existing issue |
| `delete_issue` | Delete an issue |
| `add_issue_link` | Link two issues together |
| `get_transitions` | List available status transitions |
| `get_current_user` | Show the configured Jira username |

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- Python 3.12+
- A Jira instance with a personal access token (PAT)

## Setup

### 1. Install dependencies

```bash
cd ~/.kiro/mcp-servers/jira-server
uv sync
```

### 2. Create the `.env` file

```bash
cp .env.example .env   # or create manually
```

Edit `.env` with your credentials:

```
JIRA_URL=https://jira.aimtec.cz
JIRA_TOKEN=your-personal-access-token (create here https://jira.aimtec.cz/secure/ViewProfile.jspa) 
JIRA_USERNAME=your-username (roto, simv, etc.)
```

| Variable | Required | Description |
|----------|----------|-------------|
| `JIRA_URL` | Yes | Base URL of your Jira instance (no trailing slash) |
| `JIRA_TOKEN` | Yes | Personal Access Token (PAT) — generate one in Jira under Profile → Personal Access Tokens |
| `JIRA_USERNAME` | No | Your Jira username (used by `get_current_user`) |

### 3. Register the MCP server in Kiro

Add the following to `~/.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "jira": {
      "command": "uv",
      "args": ["run", "--directory", "/root/.kiro/mcp-servers/jira-server", "python", "server.py"]
    }
  }
}
```

> **Note:** Replace `/root/.kiro/mcp-servers/jira-server` with the actual absolute path on your machine if it differs.

### 4. Restart Kiro CLI

Exit and relaunch `kiro-cli chat` so it picks up the new MCP server.

### 5. Verify it works

Ask Kiro something like:

```
What is issue PROJ-123 about?
```

If everything is configured correctly, Kiro will fetch the issue details from Jira and respond.

## Usage Examples

- "Search for open bugs in project INFR" → uses `search_issues` with JQL
- "Create a task in INFR to upgrade Redis" → uses `create_issue`
- "Assign INFR-100 to jdoe" → uses `update_issue`
- "Link INFR-101 as blocked by INFR-100" → uses `add_issue_link`
- "What transitions are available for INFR-100?" → uses `get_transitions`

## Troubleshooting

- **Connection errors** — Verify `JIRA_URL` is reachable from your machine and the token is valid.
- **401 Unauthorized** — Your PAT may have expired. Generate a new one in Jira.
- **SSL errors** — The server disables SSL verification by default (`verify=False`). If your Jira instance uses a custom CA, this keeps things working out of the box.
- **Tools not showing up in Kiro** — Make sure `mcp.json` is correct and you've restarted the CLI.
