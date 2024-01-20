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

An unofficial, unaffiliated, third-party resource planning assistant for [Mechanistry](https://mechanistry.com/)'s *Timberborn* video game.

## Binary Releases

Prebuilt binaries are available on the [releases](https://github.com/cwpearson/beavertails/releases) page for
* macOS 11
* Ubuntu 20.04
* Windows 2019

If you are using an older operating system the binary releases may not work and you'll need to download the source and run it yourself.

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

## Acknowledgements

* Built using [textualize/textual](https://github.com/Textualize/textual)
* Built using [coin-or/pulp](https://github.com/coin-or/pulp)

## Roadmap

- [x] TUI using textual
- [ ] include recipe utilization in the model
  - [ ] beavers should be treated differently (e.g., a n underutilized recipe still consumes a beaver)
  - [ ] the granularity should not go from [0..1) but (0..1]
- [ ] configurable workday length
- [ ] configurable other parameters
- [ ] use `.spec` for pyInstaller
- [ ] Beavers eat multiple foods
- [ ] worker efficiencies
- [ ] injuries
- [ ] well-being

