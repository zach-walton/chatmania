# DDR Bot

Parses a simfile (StepMania SM format) and plays the chart in the configured HipChat room.

Supports speed mods, song speed multipliers, and renders arrow spacing correctly.

## Setup

### ~/.hipchat.yml example

Optionally set multiple comma-delimited API keys to cycle through them and get around HipChat rate limiting

```
api_keys: [redacted], [redacted2], [redacted3], ...
room: show me your hottest moves
url: https://hipchat.com/v2/
```

### Emoticons

Create custom emoticons at https://your.hipchat.server.com/emoticons.  Use the icons in the icons/ directory and alias them to:

* Up arrow: (ddr)
* Right arrow: (ddrright)
* Left arrow: (ddrleft)
* Down arrow: (ddrdown)

## Usage

```
[master 🚽 #⁉️ ] 11:55:20-zachwalton ~/ddrbot 💫  ./bot.py -h

Usage: ./bot.py :simfile :style :difficulty :speed_mod :song_speed_multiplier

:simfile:               Max300.sm
:style:                 Single|Double
:difficulty:            Easy|Medium|Hard
:speed_mod:             1x|2x|3x|...
:song_speed_multiplier: 1|2|3|...

[master 🚽 #⁉️ ] 11:56:12-zachwalton ~/ddrbot 💫  ./bot.py MAX300.sm Single Hard 1x 2
A-a-are a-a-a-are you ready!?
________________
________________
________________
________________
________________
________________
________________
________________
________________
________________
________________
________________
________________
________________
________________
________________
____________(ddrright)
________________
____(ddrdown)________
________________
________(ddr)____
(ddrleft)____________
________________
________(ddr)____
(ddrleft)____________
________________
____(ddrdown)________
________________
________(ddr)____
____________(ddrright)
________________
________(ddr)____
____________(ddrright)
```

![Max 300](hottest_moves.png?raw=true)

### hipchat logger

This uses the hiplogging module from https://github.com/invernizzi/hiplogging
