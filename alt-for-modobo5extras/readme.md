# Modbo / Infinity flash extraction toolkit

Maps and extracts the contents of Infinity 1.93 and Modbo 5.0 PS2 modchip SPI flash images,
including the configuration menu and the Modbo boot menu as ELFs.

## What it extracts
| output | what it is |
|---|---|
| `core_codedecrypted.bin` | the decrypted ~50 KB EE core (break-crypt removed), with disassembly-ready code |
| `infinity_config_menu.elf` | the **settings menu** ("INFINITY CONFIGURATION MENU"), R5900, entry 0x100830 |
| `modbo_boot_menu.elf` | the Modbo 5.0 **"USBADV" graphical boot menu**, R5900, entry 0x100108 (Modbo only) |
| `boot_logo.bin` | the 4 KB boot-logo bitmap |
| `config_record.bin` | the 16-byte settings record |

## Usage
```
python3 modbo_extract.py MODBO50.BIN                 # map + extract everything to ./out
python3 modbo_extract.py infv193.bin -o ud           # Infinity 1.93 flash (64 KB, no boot menu)
python3 modbo_extract.py MODBO50.BIN --map           # just print the image map
python3 modbo_extract.py capture.dsl --t 1.28 1.80   # from a DSLogic BIOS-bus sniff
```
Needs only Python 3 (standard library). Supply your own flash dump or sniff — no firmware is
included in this release.

## Decode chains
```
core    : flash -> stage-1 rolling XOR -> stage-2 LCG chunks (checksummed)
          -> LZMA (image @0x110000) -> per-function break-crypt removal
config  : LZMA stream inside the core at core+0x5120 -> flat image -> ELF (entry 0x100830)
bootmenu: container at flash 0x20000 -> UCL NRV2E -> ELF (entry 0x100108, already an ELF)
```

See `MAP.md` for the full image layout and the two-menu explanation.

## How the Modbo 5.0 gets its different menu
The Modbo 5.0 does **not** change the Infinity settings menu — that program is byte-identical to
stock Infinity 1.93. The different on-screen menu is a *separate* program the Modbo bolts on:

1. **Same core, same settings menu.** The decrypted core (and the config menu inside it at
   core+0x5120) is identical to Infinity 1.93. Triangle+Circle at boot still opens the plain
   "INFINITY CONFIGURATION MENU".

2. **An extra add-on in the stage-2 stream.** The Modbo flash carries ~4 KB more than stock in the
   encrypted chunk chain (44 chunks vs 40). After decrypt+unpack this extra code sits just past the
   core in RAM and runs at `0x10A35C`. It hooks the EE kernel, relocates the settings record to
   flash `0x17C00`, and arranges for the boot menu below to run. This region literally carries the
   string `v3.1m USBADV Edition` (author `leoleungp`).

3. **A full second program at flash `0x20000`.** `boot_menu V1.00` — a ~946 KB graphical USB app
   launcher (NRV2E-compressed, already an ELF, entry 0x100108). Built with libpng/libtiff, it loads
   a `desktop.bmp` background and up to four app icons/ELFs (`APP1_ELF`..`APP4_ELF`) from a USB
   drive via a config file, and launches them. **This is the Modbo's front-end** — the different UI
   you see.

So the UI difference is an added launcher program plus a small kernel-hooking add-on, not a modified
settings menu. Running the tool on a Modbo 5.0 dump produces that launcher as `modbo_boot_menu.elf`;
the add-on is the extra code at 0x10A35C in the extracted `core_codedecrypted.bin`.

```
modbo_extract.py          the tool
MAP.md                    full flash image map
lib/
  infinity_decrypt.py     stage-1 XOR + stage-2 LCG (seed auto-detected)
  breakcrypt.py           in-core break-crypt remover
  nrv.py                  UCL NRV2E/2B/2D decompressor (boot menu)
  sniff_to_flash.py       DSLogic .dsl -> SPI flash bytes
  mdis.py                 R5900 disassembler
```

## Notes
- Synthesised ELF wrappers use the firmware's load/entry addresses; program bytes are exactly as
  unpacked. The menus expect their runtime setup, so they are ready for a disassembler but will
  not boot from a plain ELF loader on their own.
- The configuration menu is byte-identical across Infinity 1.93 / update disc / Modbo 5.0.
- Only the 1.93-era core format is handled; older Infinity cores use a different code layer.
