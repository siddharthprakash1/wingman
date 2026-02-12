# Available Tools

## System Tools

- `bash` — Execute shell commands on the local machine
- `read_file` — Read the contents of a file
- `write_file` — Write content to a file (creates if not exists)
- `edit_file` — Edit specific lines in an existing file
- `list_dir` — List files and directories

## Information Tools

- `web_search` — Search the web using DuckDuckGo
- `browser_navigate` — Open a URL in a browser and extract content
- `browser_click` — Click an element on a web page
- `browser_extract` — Extract text or data from a web page

## Memory Tools

- `memory_read` — Read a specific memory file
- `memory_update` — Update a memory file with new content
- `memory_append` — Append information to a memory file

## Automation Tools

- `cron_add` — Schedule a recurring task
- `cron_list` — List all scheduled tasks
- `cron_remove` — Remove a scheduled task

## Notes

- Shell commands run with the user's permissions
- File operations are relative to the workspace unless absolute paths given
- Web search uses DuckDuckGo (no API key required)
- Browser operations require Playwright to be installed
