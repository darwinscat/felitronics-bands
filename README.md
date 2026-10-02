# felitronics-bands

The named EQ bands of the Felitronics family — one table that tabbyEQ, the mastering core and its web and desktop shells
all read, so a band means the same thing everywhere.

- `bands.toml` — each band's key, filter type, frequency and Q. These numbers are sound: a product renders them as written,
  and a change is a release.
- `text/<lang>.toml` — each band's name and one short line, per language; `ru` is the canon, the others follow it.
- `languages.toml` — the languages that are whole.

Products embed these files at build time (`felitronics_toml_embed` from felitronics-toml), so nothing is read or parsed
while a product runs. Longer explanations are not here: each product links to them.

`python3 tools/check.py --controls` is the gate CI runs: every band sound, every listed language whole (names and short
lines within their lengths, polite or impersonal), and each kind of damage refused.

AGPL-3.0-or-later — see LICENSE.
