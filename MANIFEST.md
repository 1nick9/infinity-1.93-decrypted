# Infinity 1.93 patch package - manifest

Naming follows *Infinity 1.93 Core - Reading Guide*. Every extracted blob and signature is included; items that are not menu options are kept and marked `not_covered` exactly as the guide marks them (console checks / chip handshake), without further detail.

## Branches

* `update_disc_1.93/` - Infinity 1.93 - official update-disc image (I.ELF)
* `Matrix_Infinity_1.93_SA25F005/` - Infinity 1.93 - SA25F005 flash dump
* `MODBO50/` - Modbo 5.0 - 512 KB flash dump

## Blobs (same in every branch)

| file | guide name | status | menu byte | resident | size |
|---|---|---|---|---|---|
| `menu__macrovision_stub__0x50020.bin` | macrovision_stub | menu | cfg[6] | 0x80050020 | 28 |
| `menu__display_trap_stub__0x50940.bin` | display_trap_stub | menu | cfg[1] | 0x80050940 | 16 |
| `menu__y_offset_table__0x58c80.bin` | y_offset_table | menu | cfg[10] | 0x80058c80 | 10 |
| `menu__psx_screenfix_nonpal_a__0x58f48.bin` | psx_screenfix_nonpal_a | menu | cfg[2] | 0x80058f48 | 68 |
| `menu__psx_screenfix_nonpal_b__0x58f90.bin` | psx_screenfix_nonpal_b | menu | cfg[2] | 0x80058f90 | 24 |
| `menu__psx_screenfix_pal__0x58fa8.bin` | psx_screenfix_pal | menu | cfg[2] | 0x80058fa8 | 144 |
| `dispatcher__program_names__0x58bb0.bin` | program_names | dispatcher | all | 0x80058bb0 | 32 |
| `helper__all_ff_mask__0x58cb0.bin` | all_ff_mask | helper | all | 0x80058cb0 | 16 |
| `table__signature_mask_table__0x58cc0.bin` | signature_mask_table | table | mixed | 0x80058cc0 | 648 |
| `partial__game_boot_block__0x53b50.bin` | game_boot_block | partial | cfg[12] | 0x80053b50 | 2744 |
| `not_covered__osdsys_boot_block__0x53b20.bin` | osdsys_boot_block | not_covered | - | 0x80053b20 | 48 |
| `not_covered__osdsys_hook_payload__0x54610.bin` | osdsys_hook_payload | not_covered | - | 0x80054610 | 1212 |
| `not_covered__osdsys_bootmode_block__0x59038.bin` | osdsys_bootmode_block | not_covered | - | 0x80059038 | 256 |
| `not_covered__console_check_blob_58d00__0x58d00.bin` | console_check_blob_58d00 | not_covered | - | 0x80058d00 | 20 |
| `not_covered__console_check_blob_58d28__0x58d28.bin` | console_check_blob_58d28 | not_covered | - | 0x80058d28 | 48 |

## Signatures

| signature | status | menu byte | what it serves |
|---|---|---|---|
| `sig01` | menu | cfg[11] | DVD-Video region (DVD player patch) |
| `sig02` | menu | cfg[11] | DVD-Video region (DVD player patch) |
| `sig03` | menu | cfg[11] | DVD-Video region (DVD player patch) |
| `sig04` | menu | cfg[11] | DVD-Video region (IOP MechaCon region) |
| `sig05` | not_covered | - | OSDSYS routine 0x800514F8 |
| `sig06` | not_covered | - | OSDSYS routine 0x800514F8 |
| `sig07` | not_covered | - | OSDSYS routine 0x800514F8 |
| `sig08` | not_covered | - | OSDSYS routine 0x800514F8 |
| `sig09` | not_covered | - | OSDSYS routine 0x800514F8 |
| `sig10` | not_covered | - | OSDSYS routine 0x800514F8 |
| `sig11` | not_covered | - | OSDSYS routine 0x800514F8 |
| `sig12` | not_covered | - | OSDSYS routine 0x800514F8 |
| `sig13` | menu | cfg[12] | DVD9 DL support (PS2LOGO flag) |
| `sig14` | menu | cfg[12] | DVD9 DL support (PS2LOGO flag) |
| `sig15` | menu | cfg[2] | PSX screen fix (PS1DRV) |
| `sig16` | menu | cfg[2] | PSX screen fix (PS1DRV) |
| `sig17` | menu | cfg[4] | ATAD auto patch, part 1 |
| `sig18` | menu | cfg[4] | ATAD auto patch, part 1 |
| `sig19` | not_covered | - | IOP routine 0x800524A0 - part not covered |
| `sig20` | menu | cfg[3] | MC16 (secrman_for_cex search) |
| `sig21` | not_covered | - | IOP routine 0x800524A0 - part not covered |
| `sig22` | menu | cfg[4] | ATAD auto patch, part 2 |
| `sig23` | menu | cfg[4] | ATAD auto patch, part 2 |
| `sig24` | menu | cfg[4] | ATAD auto patch, part 2 |

`menu` = configurable in the option menu. `not_covered` = part of the console check / chip handshake; kept as raw bytes only. `partial` = the cfg[12] flag path is a menu option, the rest of the block is not covered.
