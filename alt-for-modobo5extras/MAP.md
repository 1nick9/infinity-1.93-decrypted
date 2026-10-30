# Modbo 5.0 / Infinity 1.93 flash image map

512 KB Modbo 5.0 SPI flash (`MODBO50.BIN`). Infinity 1.93 flashes use the same layout for the
first region only (64 KB chips stop after the core chain).

| offset | size | contents |
|---|---|---|
| `0x00000-0x0B400` | ~45 KB | **Infinity core chain** — stage-1 XOR header + stage-2 LCG chunks (checksummed). Decrypts + LZMA-unpacks to the ~50 KB EE core at 0x110000, which contains the config menu and (Modbo) the add-on. Ends at the `00000000` chunk terminator. |
| `0x0E000-0x0F000` | 4 KB | **boot logo** bitmap (ILOGO) |
| `0x0F500` | 232 B | **stage-1 seed loader** — the small routine the chip injects into the EE kernel to start the read. Mirrored at `0x1FF00` and `0x7FF00`. |
| `0x0FC00` | 16 B | **configuration record** (settings). Modbo mirrors it at `0x17C00`. |
| `0x10800-0x11000` | — | erased sector (a few single-bit-drift cells; not data) |
| `0x20000-~0x5E2B4` | ~250 KB | **Modbo "USBADV" boot menu** — `boot_menu V1.00`, NRV2E-compressed. A graphical USB app launcher (the Modbo 5.0 front-end). Already an ELF once decompressed (entry 0x100108). |
| everything else | — | erased flash (`0xFF`) |

## Two menus, one image
- **Infinity configuration menu** (settings: screen fix, region, DVD9, …) lives inside the core
  and is byte-identical across Infinity 1.93, the update disc and Modbo 5.0.
- **Modbo "USBADV" boot menu** is a *separate* program at `0x20000` — it is what gives the Modbo
  5.0 its different look. It loads a desktop/background and up to four USB app ELFs via a config file.

A small Modbo add-on (extra ~4 KB inside the stage-2 stream, running at 0x10A35C) hooks the kernel,
moves the settings record to `0x17C00`, and brings up the boot menu.
