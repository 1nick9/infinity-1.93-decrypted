vibed again. but i knew there was a path to decrypt this from what found, i just couldn't actually do it :)

expect mistakes as with all vibe


this is not the fpga dump. just eeprom n update disc.


# Infinity 1.93 — decrypted core, patch blobs and signatures

Naming follows **Infinity 1.93 Core — Reading Guide**. This package covers the three public
1.93-branch images; every extracted blob and signature is included. Items that are not menu
options are kept as raw bytes and marked `not_covered`, exactly as the guide marks them
(console checks / chip handshake), with no further detail.

## Branches
| folder | source |
|---|---|
| `update_disc_1.93/` | Infinity 1.93 official update-disc image (I.ELF) |
| `Matrix_Infinity_1.93_SA25F005/` | Infinity 1.93 SA25F005 flash dump |
| `MODBO50/` | Modbo 5.0 512 KB flash dump |

The decrypted core (`core_codedecrypted.bin`) is byte-identical between the update disc and the
SA25F005 dump; the Modbo build differs only in its boot add-on. Each folder holds:

```
core_codedecrypted.bin   unpacked core @0x110000, break-crypt removed
core_listing.txt         full disassembly (resident part shown at its run address 0x50000+)
summary.json             machine-readable signatures / blobs / addresses
blobs/                   every data blob, named per the guide
signatures/              every signature + mask, named per the guide
```

Blob and signature file names are prefixed by status:
- `menu__…`        a user-configurable option (its `cfg[N]` byte is in the filename comment)
- `partial__…`     the cfg[12] flag path is a menu option; the rest of the block is not covered
- `dispatcher__`, `helper__`, `table__`  core data used by all patches
- `not_covered__…` not a menu option — kept as raw bytes only (see the guide, "Not covered here")

See `MANIFEST.md` for the full blob/signature table with guide names, status and addresses.

## Decrypting a flash yourself
`decrypt_core.py` reproduces `core_codedecrypted.bin` from a flash dump or a DSLogic bus sniff:

```
python3 decrypt_core.py flash.bin                 # -> core_codedecrypted.bin
python3 decrypt_core.py flash.bin --ram ram.bin   # also dump the stage-2 RAM image
python3 decrypt_core.py capture.dsl --t 1.28 1.80 # from a BIOS-bus sniff
```

Chain: stage-1 rolling XOR → stage-2 LCG chunks (checksummed) → LZMA core (0x110000)
→ break-crypt removal. It is verified to reproduce each shipped `core_codedecrypted.bin` exactly.

```
decrypt_core.py          flash/sniff -> decrypted core
lib/
  infinity_decrypt.py    stage-1 XOR + stage-2 LCG (seed auto-detected)
  breakcrypt.py          in-core break-crypt remover
  sniff_to_flash.py      DSLogic .dsl -> SPI flash bytes
  mdis.py                R5900 disassembler (used for the listings)
```

## Converting addresses (from the guide)
The resident block runs at `0x80050000` but the listing keeps `0x110000` numbering:
`listing = resident - 0x80050000 + 0x110650`.

## Notes
- Only the 1.93 branches are included. Older firmwares use a different code-encryption scheme
  that is not handled here.
- `not_covered` items are present for completeness only and carry no analysis.
