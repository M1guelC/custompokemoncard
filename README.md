# Card creator

Desktop app for custom cards. The frames, icons, fonts, and printed backs come from `Custom Content`. Drop in a picture, edit the words, and the preview updates in the window.

## Run

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and start it. On WSL, also turn on Settings > Resources > WSL integration for this distro. Then, from the project folder:

```bash
./run
```

That is the only command. Docker runs the Python side that draws the cards. The window is the Windows Electron app, on the Windows desktop. The first run builds the image and can take a few minutes. The first time the server starts, it also prepares the card frames from the Photoshop templates.

In Cursor or VS Code, **Reopen in Container** opens that same Python environment. Use `./run` when you want the window.

## Setup without Docker

Python 3.10 or newer, and Node.js 22.12 or newer. The editor opens in an Electron window. Python still draws the cards.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd desktop && npm install && cd ..
.venv/bin/python main.py
```

On WSL, that `npm install` downloads the Windows Electron build, so the window opens on the Windows desktop instead of through the slower Linux desktop.

On Windows, from the project folder:

```bash
py -3 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
cd desktop && npm install && cd ..
.venv\Scripts\python main.py
```

The first launch builds the card frames from the Photoshop templates. That can take a few minutes, and then the window opens. Later launches open right away.

## Use

Pick Character, Enemy, Round / event / item, Card back, or Booster. Upload a picture, change the text, and use Zoom and Vertical focus to crop it. Flip shows the other side. Download saves the side on screen.
