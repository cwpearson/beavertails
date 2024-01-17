# B.E.A.V.E.R.T.A.I.L.S.

(**B**eaver
**E**ngineering
**A**nd
**V**illage
**E**xpansion
**R**esource
**T**ransport
**A**llocation
**I**nteger
**L**inear
**S**ystems)

A resource planning assistant for the *Timberborn* video game by [Mechanistry](https://mechanistry.com/).

## Binary Releases

Please see https://github.com/cwpearson/beavertails/releases for the latest releases, built on
* macOS 11
* Ubuntu 20.04
* Windows 2019

If you are using an older OS than that, the binary releases may not work and you'll need to download the source and run it yourself.

## Running from Source

Clone the repository

```
pip install -r requirements.txt
python -m beavertails.tui
```

## Building for macOS

```bash
pyinstaller beavertails/tui.py \
  --add-data beavertails/static:./beavertails/static \
  --add-data beavertails/beavertails.tcss:. \
  --collect-all pulp \
  --onefile
```

## Building for Ubuntu

```bash
pyinstaller beavertails/tui.py \
  --add-data beavertails/static:./beavertails/static \
  --add-data beavertails/beavertails.tcss:. \
  --collect-all pulp \
  --onefile --nowindow --noconfirm
```

## Building for Windows

```bat
pyinstaller beavertails/tui.py --add-data "beavertails/static;./beavertails/static" --add-data "beavertails/beavertails.tcss;." --collect-all pulp --onefile --nowindow --noconfirm
```

## Roadmap

- [x] TUI using textual
- [ ] Allow beavers to eat multiple foods
- [ ] worker efficiencies
- [ ] injuries
- [ ] well-being
