# Card creator

Desktop app for custom cards. The frames, icons, fonts, and printed backs come from `Custom Content`. Drop in a picture, edit the words, and the preview updates in the window.

## Setup

Python 3.10 or newer.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

On Windows, from the project folder:

```bash
py -3 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python main.py
```

The first launch builds the card frames from the Photoshop templates. That can take a few minutes, and then the window opens. Later launches open right away.

On WSL, the window appears on the Windows desktop.

## Use

Pick Character, Enemy, Round / event / item, Card back, or Booster. Upload a picture, change the text, and use Zoom and Vertical focus to crop it. Flip shows the other side. Download saves the side on screen.
