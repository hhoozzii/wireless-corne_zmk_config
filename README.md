# Miryoku (QWERTY) layout

This fork uses the [Miryoku](https://github.com/manna-harbour/miryoku) layout with QWERTY alphas,
from [hhoozzii/miryoku_zmk](https://github.com/hhoozzii/miryoku_zmk) (copied into `config/miryoku/`).
Miryoku uses 36 keys (3x5 per half + 3 thumbs). This build is for a Corne with the outer pinky
columns cut off: the keymaps use the board's 5-column layout (`foostan_corne_5col_layout`) and the
36-key mapping in `config/miryoku/mapping/36/corne_5col.h`. (To go back to a full 6-column board,
include `mapping/42/corne.h` and `&foostan_corne_6col_layout` instead.)

* Layout options: `config/miryoku/custom_config.h` (alphas, Mac clipboard, vi nav, flip...)
* Keymap and settings: `config/blecorne.keymap` / `blecorne.conf` (Boardsource Wireless Corne SMT)
* nice!view displays use a **custom status screen** (`boards/shields/nice_view_custom/`, preview in `docs/nice_view_preview.png`):
  * Left: battery and output (USB, BLE connected, BLE disconnected, or pairing), the Miryoku layer name, ten layer pips
    (filled = on, underline = current), held home-row mods **G A C S**, BLE profiles 1-5
    (filled = selected, thick border = connected, thin = paired), words per minute.
  * Right: battery, link to the left half, and a map of the right-hand Miryoku keys with the home-row mods inverted.
  * Set `CONFIG_NICE_VIEW_CUSTOM_INVERTED=y` in the `.conf` for white-on-black.
  * Plug the nice!view into header pins 3–7 (MOSI, SCK, VCC, GND, CS) with the screen facing up.

**Getting firmware:** every push runs GitHub Actions. (On a fork, Actions stays off until you open the
Actions tab and click "I understand my workflows, go ahead and enable them"; after that use
"Run workflow" or push any change.) Open the Actions tab, pick the latest run,
download the `firmware` artifact and unzip it. It has three files: `blecorne_left` (left half),
`blecorne_right` (right half) and `settings_reset` (works on both halves). Double-tap reset to mount
the USB drive, then copy the `.uf2` onto it. Coming from other firmware (or if the halves don't pair
with each other), flash `settings_reset` to both halves first, then the normal files.

---

# Boardsource Wireless Corne SMT Firmware

This repository contains the official ZMK configuration for the **Wireless Corne SMT**. This PCB is designed for a seamless, cable-free experience with full support for ZMK Studio.

* **Product Page:** [Wireless Corne SMT PCB](https://boardsource.xyz/products/wireless-corne-smt-pcb-assembled-hot-swap-zmk-compatible-split-keyboard-pcb)
* **Full Documentation & Build Guide:** [Wireless SMT Corne Docs](https://boardsource.xyz/blogs/guides/wireless-smt-corne-docs)

---

## Features

* **ZMK Studio Ready:** Change your keymap in real-time without reflashing.
* **Fully Wireless:** No TRRS cable or USB connection required for standard use.
* **Universal Support:** Works with MX, Choc v1, and Choc v2 switches.
* **Pre-Flashed:** Ready to use out of the box.

---

## Expansion Pinout

The 8-pin header on each side (identical, not mirrored) is read from left to right. These are perfect for screens (nice!view / e-ink) or custom hardware.

| Pin | GPIO | Note |
| --- | --- | --- |
| 1 | 0.07 |  |
| 2 | 0.21 |  |
| 3 | 0.12 |  |
| 4 | 0.23 |  |
| 5 | VCC | Switched via pin 0.31 |
| 6 | GND |  |
| 7 | 0.19 |  |
| 8 | 0.05 |  |

---

## Battery Information

If shipping allows, batteries are included. The PCB features a micro JST connector (BM02B-ACHSS-GAN-ETF) and labeled solder pads (+/-) for custom installs.

**Max Dimensions:**

* **Choc:** 30x17x3mm
* **MX:** 30x17x6mm

---

## How to Flash

1. **Modify:** Fork this repo and edit your files in the `config/` folder.
2. **Build:** GitHub Actions will automatically compile your firmware.
3. **Download:** Grab the `firmware.uf2` from the Actions tab.
4. **Install:** Connect the board via USB, double-tap the reset button, and drag the file onto the drive.
