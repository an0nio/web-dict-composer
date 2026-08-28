# Magic numbers for file-upload review

This is a human-readable reference, not a line-oriented dictionary. `web-dict-composer` does not
emit these hexadecimal values as binary data and never treats this document as wizard or profile
input.

| Type | Signature or rule | Hexadecimal bytes |
|---|---|---|
| JPEG | Starts with the JPEG SOI marker and a following marker byte | `FF D8 FF` |
| PNG | Fixed eight-byte signature | `89 50 4E 47 0D 0A 1A 0A` |
| GIF87a | ASCII `GIF87a` | `47 49 46 38 37 61` |
| GIF89a | ASCII `GIF89a` | `47 49 46 38 39 61` |
| PDF | ASCII `%PDF-` | `25 50 44 46 2D` |
| ZIP | Normal, empty, or spanned archive prefix | `50 4B 03 04`, `50 4B 05 06`, or `50 4B 07 08` |
| GZIP | Header including compression method 8 | `1F 8B 08` |
| BMP | ASCII `BM` | `42 4D` |
| TIFF, little-endian | TIFF little-endian header | `49 49 2A 00` |
| TIFF, big-endian | TIFF big-endian header | `4D 4D 00 2A` |
| WebP | ASCII `RIFF` at offset 0 and `WEBP` at offset 8 | `52 49 46 46 … 57 45 42 50` |
| OLE/CFB | Compound File Binary header | `D0 CF 11 E0 A1 B1 1A E1` |
| ELF | ELF identification prefix | `7F 45 4C 46` |
| PE/DOS | ASCII `MZ`; insufficient without the later PE structure | `4D 5A` |

SVG, XML, and HTML do not have a single dependable binary magic number. Their identification
depends on text encoding, optional declarations, whitespace, content parsing, and sometimes MIME
sniffing.

## Copy-paste signature files

Use `printf` instead of `echo`: it writes the selected bytes without adding a newline. The
following commands create small signature stubs suitable for checking magic-number detection:

```bash
printf '\xFF\xD8\xFF' > signature-jpeg.jpg
printf '\x89\x50\x4E\x47\x0D\x0A\x1A\x0A' > signature-png.png
printf '\x47\x49\x46\x38\x37\x61' > signature-gif87a.gif
printf '\x47\x49\x46\x38\x39\x61' > signature-gif89a.gif
printf '\x25\x50\x44\x46\x2D' > signature-pdf.pdf
printf '\x50\x4B\x03\x04' > signature-zip.zip
printf '\x1F\x8B\x08' > signature-gzip.gz
printf '\x42\x4D' > signature-bmp.bmp
printf '\x49\x49\x2A\x00' > signature-tiff-le.tiff
printf '\x4D\x4D\x00\x2A' > signature-tiff-be.tiff
printf '\x52\x49\x46\x46\x00\x00\x00\x00\x57\x45\x42\x50' > signature-webp.webp
printf '\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1' > signature-ole.bin
printf '\x7F\x45\x4C\x46' > signature-elf.bin
printf '\x4D\x5A' > signature-pe.exe
```

To append the minimal PHP execution marker, run for example:

```bash
cat -- fixtures/file_upload/php/php_execution_marker.php >> signature-gif89a.gif
```

These are deliberately signature-only files. They are useful for simple magic-number checks, but
they are not complete JPEG, PNG, GIF, archive, executable, or document structures. Create a real
file with the corresponding encoder when the application performs full format decoding.

## Validation caveats

- A prefix match does not prove that the complete file is valid or safe.
- Some formats use signatures at non-zero offsets or structural rules involving several fields.
- Polyglot files can satisfy more than one parser, so extension, MIME, signature, and full decode
  results may disagree.
- Upload validation should use a format-aware parser or decoder, enforce size and policy limits,
  generate server-side names, and store files outside executable locations.

For broader and format-specific rules, consult the upstream
[`file` magic database](https://github.com/file/file/tree/master/magic/Magdir).
