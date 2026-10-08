# Open WebUI + NCSA Lumen

Run your own private chat assistant on your computer, using open-weight models
hosted at NCSA through [Lumen](https://lumen.ncsa.illinois.edu). Optionally give the
assistant a Linux workspace where it can read and write files in one folder, run
code, and produce outputs (similar to Claude's Cowork mode).

Everything runs in Docker. Your chats and settings stay on your computer. Prompts and
any file contents the assistant reads are sent to Lumen for processing.

Maintained on a best-effort basis by PRI Data Stewardship and Computing. Questions and
problems: open an issue on this repo. This is a recipe, not a supported service.

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
git clone https://github.com/PrairieResearchInstitute/lumen-openwebui.git ~/lumen-openwebui
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
| `owui connect-terminal` | Register the terminals in Open WebUI (setup does this) |
| `owui project add/rm/list` | Separate terminals for separate projects (see below) |
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

It is on by default (`COMPOSE_PROFILES=terminal` in `.env`), and `owui setup`
connects it to Open WebUI for you. It shows up as a terminal named **Workspace**.
If you turned the terminal on later, or the automatic step failed, run:

```bash
owui connect-terminal
```

This uses Open WebUI's admin API, so you don't have to touch the admin settings. It is
safe to run again. If you turned on login (`WEBUI_AUTH=True`), first create an API key
under **Settings → Account** and set it as `OWUI_API_KEY` in `.env`.

To use it:

1. Start a new chat and pick a model. Models default to native function calling with
   built-in tools on, which the terminal needs. If you changed a model's
   **Function Calling** to Legacy, set it back to Native under **Workspace → Models**.
2. Click the terminal button (cloud icon) in the chat input and pick **Workspace**
   under **System**.
3. Try: "List the files in ~/owui-workspace and summarize what's there."

The folder `~/owui-workspace` on your computer appears under the same name,
`~/owui-workspace`, inside the container, and the sidebar file browser opens there.
It is the only part of your computer the model can see. Put the files you want it
to work on there. If you point `OWUI_WORKSPACE` at a different folder, it still shows
up as `~/owui-workspace` inside the container.

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
- **Text-only models can't look at images.** By default the terminal won't send image
  files to the model, so a model that tries to check its own plot gets a short error
  and carries on. You still see the image in the file browser. If every model you use
  accepts images, set `TERMINAL_BINARY_MIME_PREFIXES=image` in `.env` and run
  `owui up`.
- To run without the terminal, remove `terminal` from `COMPOSE_PROFILES` and run
  `owui down && owui up`.

## Separate terminals for separate projects

The **Workspace** terminal sees all of `~/owui-workspace`. To keep a project's files
apart, give it its own terminal that sees only its folder:

```bash
owui project add Report ~/owui-workspace/Report
```

This starts another Open Terminal container that mounts only that folder, at the
same path under the home folder (`~/owui-workspace/Report` in both places), and
registers it in Open WebUI as **Report**. In a chat, pick **Report** from the
terminal button instead of **Workspace**. The folder can be anywhere under your
home folder and is created if it does not exist.

```bash
owui project list          # projects and whether their terminals are running
owui project rm Report     # remove the terminal; the folder is not touched
```

Each project terminal has its own installed packages and its own memory limit
(`TERMINAL_MEMORY`, 4G by default), so keep the number reasonable. Projects are
stored in `projects.conf` and `compose.override.yaml` in this folder. Both are
specific to your computer and not committed. `owui up`, `down`, and `status` include
the project terminals automatically.

A lighter option, if you only want to keep work organized: create a chat folder in
Open WebUI, and in the folder's settings set a system prompt such as "Work only in
~/owui-workspace/Report." Every chat in that folder gets it. The model is asked to stay
in that folder but is not prevented from leaving it.

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

**Terminal shows "connection failed".** Run `owui connect-terminal` again. It checks the
connection before saving and prints the error if it fails. If you set it up by hand, use
`http://open-terminal:8000`, not localhost. Check with `docker exec open-webui curl -s http://open-terminal:8000/health`, which
should print `{"status": "ok"}`.

**"Model only supports text input; received unsupported content type 'image_url'".**
The model read an image file and Open WebUI passed the picture to a text-only model.
Check that `TERMINAL_BINARY_MIME_PREFIXES` is empty in `.env`, run `owui up`, and start
a new chat. The old chat still holds the image and fails every time it is sent.

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

## License

The files in this repo are released under the University of Illinois/NCSA Open Source
License. See [LICENSE](LICENSE). Open WebUI and Open Terminal are separate projects
with their own licenses; this repo only configures and runs their published images.
