# B.E.A.V.E.R.T.A.I.L.S.

**B**eaver
**E**ngineering
**A**nd
**V**illage
**E**xpansion
**R**esource
**T**ransport
**A**llocation
**I**nteger
**L**inear
**S**ystems

A resource planning assistant for the *Timberborn* video game.

## Getting Started

```
pip install -r requirements.txt
python -m beavertails.lib
python -m beavertails.tui
```

## Building for macOS

```
pyinstaller beavertails/tui.py \
  --add-data beavertails/static:./beavertails/static \
  --add-data beavertails/beavertails.tcss:. \
  --collect-all pulp \
  --onefile
```

## Roadmap

- [x] TUI using textual
- [ ] Allow beavers to eat multiple foods
- [ ] worker efficiencies
- [ ] injuries
- [ ] well-being