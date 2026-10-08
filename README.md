# Open WebUI + NCSA Lumen

Run your own private chat assistant on your computer, using open-weight models
hosted at NCSA through [Lumen](https://lumen.ncsa.illinois.edu). Optionally give the
assistant a Linux workspace where it can read and write files in one folder, run
code, and produce outputs (similar to Claude's Cowork mode).

Everything runs in Docker. Your chats and settings stay on your computer. Prompts and
any file contents the assistant reads are sent to Lumen for processing.

## What you need

- Docker Desktop (macOS, Windows) or Docker Engine with the compose plugin (Linux)
- A Lumen account and API key
- Basic comfort with a terminal

Check that the key works before going further:

```bash
curl -s https://lumen.ncsa.illinois.edu/v1/models \
  -H "Authorization: Bearer $LUMEN_API_KEY" | python3 -m json.tool | grep '"id"'
```

## Quick start

```bash
git clone <this repo> ~/lumen-openwebui
cd ~/lumen-openwebui

# Put your Lumen key in your shell config (recommended) ...
echo 'export LUMEN_API_KEY="your-key"' >> ~/.bashrc && source ~/.bashrc
# ... or in .env after setup creates it.

bin/owui setup
```

`setup` creates `.env`, generates the secret keys, creates the data and workspace
folders, pulls the images, and starts everything. Open http://localhost:3000 once
`bin/owui status` shows `(healthy)`. The first start takes a minute or two.

Add `bin` to your PATH to type `owui` from anywhere:

```bash
echo 'export PATH="$HOME/lumen-openwebui/bin:$PATH"' >> ~/.bashrc
```

## Commands

| Command | What it does |
|---|---|
| `owui setup` | First-time setup, safe to run again |
| `owui up` / `owui down` | Start / stop and remove containers (data is kept) |
| `owui start` / `owui stop` | Start / stop existing containers |
| `owui status` | Container health, data folder size, last database change |
| `owui logs [service]` | Follow logs (`open-webui` or `open-terminal`) |
| `owui upgrade` | Pull newer images and restart |
| `owui terminal-key` | Print the Open Terminal key |
| `owui push` / `owui pull` | Move your state to or from another machine (see below) |

Plain `docker compose` commands also work from this folder.

## Where things live

| What | Default location | Setting |
|---|---|---|
| Chats, settings, uploads | `~/openwebui-data` | `OWUI_DATA` |
| Folder the AI can work in | `~/owui-workspace` | `OWUI_WORKSPACE` |
| Packages the AI installs | Docker volume `open-terminal-home` | |
| Keys and settings | `.env` in this folder (never commit it) | |

## Open Terminal: let the assistant work with files

Open Terminal gives the model a Linux container with Python, git, pandas, matplotlib,
and common command-line tools. The model can run commands, write files, and show you
the results. A file browser appears in the chat sidebar so you can see, upload, and
download files.

It is on by default (`COMPOSE_PROFILES=terminal` in `.env`). One-time connection:

1. In Open WebUI, open **Admin Panel → Settings → Integrations**.
2. Scroll to the **Open Terminal** section (not "Tools"). Click **+**.
3. URL: `http://open-terminal:8000`. Key: the output of `owui terminal-key`.
   Authentication: Bearer. Save, and check the status turns green.
4. Enable tool use for the model: **Admin Panel → Settings → Models**, edit the model
   you use, and turn on native function calling / built-in tools in its capabilities
   and advanced parameters. Labels vary between Open WebUI versions.
5. In a new chat, pick the terminal from the dropdown next to the model selector, and
   try: "List the files in ~/workspace and summarize what's there."

The model sees **only** `~/workspace` inside the container, which is
`~/owui-workspace` on your computer. Put the files you want it to work on there.

Things to know:

- **It can change and delete files in the workspace.** Do not point `OWUI_WORKSPACE`
  at your home folder or anything without a backup. Use a dedicated folder, ideally
  under git.
- **File contents go to Lumen.** Anything the model reads is sent to the model as part
  of the conversation. Do not put files there that your unit's data rules keep off
  shared services.
- **The container has network access and sudo inside it.** It cannot see the rest of
  your computer, but it can download things.
- **Results depend on the model's tool use.** Models built for agentic work handle this
  much better than plain chat models. If a model ignores the terminal or loops, try
  another one.
- To run without the terminal, remove `terminal` from `COMPOSE_PROFILES` and run
  `owui down && owui up`.

## Personalizing the assistant

Open WebUI has no idea who you are by default. Write a short profile and paste it into
**Settings → General → System Prompt**. It applies to every new chat with every model.
See [docs/system-prompt-template.md](docs/system-prompt-template.md) for a starting point.

## Using it on more than one computer

`owui push` and `owui pull` move your chats and settings between machines over ssh.
Both machines need this repo at the same path under your home folder, the same
`WEBUI_SECRET_KEY`, and the same image versions.

```bash
owui push other-host -n     # dry run: shows what would change
owui push other-host        # stops both sides, syncs, starts the other side
owui pull other-host -w     # pull, including the workspace folder
```

Set `OWUI_REMOTE` in `.env` to skip typing the host. The script refuses to sync from an
empty folder and warns if the destination is newer than the source. Use one machine at
a time: sync is a handoff, not a merge.

## Upgrading

`owui upgrade` pulls the newest images. Upgrades occasionally change the database
format, so upgrade every machine you sync between before syncing again. To avoid
surprises, pin versions with `OWUI_TAG` and `TERMINAL_TAG` in `.env`.

## Troubleshooting

**"500: Internal Error" in the browser after a reinstall.** Usually a browser session
signed with an old secret key. Try a private window, then clear site data for
localhost:3000. Keep `WEBUI_SECRET_KEY` fixed to prevent it.

**Changed the Lumen key in `.env` but nothing happened.** Open WebUI copies connection
settings into its database on first launch and ignores the environment after that.
Change it in **Admin Panel → Settings → Connections**.

**Terminal shows "connection failed".** Use `http://open-terminal:8000`, not localhost.
Check with `docker exec open-webui curl -s http://open-terminal:8000/health`, which
should print `{"status": "ok"}`.

**Permission errors in the workspace on Linux.** The terminal runs as a non-root user
inside the container. If its user id differs from yours, files may be unwritable.
Run `docker exec open-terminal id` and adjust ownership of the workspace folder.

**Starting over.** `owui down`, then move `~/openwebui-data` aside and run `owui setup`.

## Notes

- Open WebUI's license includes a branding clause for larger deployments. Personal use
  is fine. Read it before running a shared instance for many users.
- This setup binds to localhost only and runs in single-user mode (`WEBUI_AUTH=False`).
  For a shared instance, set `WEBUI_AUTH=True` before the first launch and put it
  behind a proper reverse proxy with TLS.
