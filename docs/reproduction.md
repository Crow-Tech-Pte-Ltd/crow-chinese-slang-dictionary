# Reproduction and provenance

The downloadable release validates offline without a key or private work files.
Full regeneration also needs the pinned upstream snapshot, cached source contexts
or network access, and an explicitly supplied OpenRouter key. Never commit a key.

## Licensed source senses

`config/lexical-source.json` pins the snapshot and SHA-256. Acquire the matching
Chinese JSONL extraction from Kaikki's raw-data archive or a retained local copy.
Extraction refuses another snapshot until its metadata is explicitly reviewed.
Only original glosses, labels, sense references and explicit script forms are
imported. Examples and supplemental synonym/dialect tables are not imported.

```sh
python3 -m slangdict.expand extract --source /path/to/pinned-chinese.jsonl.gz
python3 -m slangdict.expand select --role generator --key-file /path/to/key --max-usd 8
python3 -m slangdict.expand select --role checker --key-file /path/to/key --max-usd 8
python3 -m slangdict.recover_selection --role checker
python3 -m slangdict.short_review --key-file /path/to/key
```

The recovery command makes zero network requests. It accepts only exact expected
identifiers appearing once in an exact cached request. Invalid/missing identifiers
are held; they are never fuzzy-corrected. Only genuinely undecided rows go to the
short-reference review. Completed decisions, including rejections, are reused.

## Public usage and spelling research

The platform query plan covers Bilibili, Weibo, Zhihu, Xiaohongshu, Douyin,
Tieba/Douban, PTT/Dcard, Hong Kong discussion boards and overseas Chinese forums.
It also researches 23 proposed spelling families. A proposal is not an approval.
Only public accessible/indexed material is used; no login bypass or private groups.

```sh
python3 -m slangdict discover --key-file /path/to/key --max-usd 8 --raise-budget
python3 -m slangdict discover --query-file config/expansion-social-queries.json --key-file /path/to/key --max-usd 8
python3 -m slangdict attest
python3 -m slangdict review --key-file /path/to/key --max-usd 8
python3 -m slangdict.curated_resume --key-file /path/to/key
python3 -m slangdict.variants --key-file /path/to/key
```

`--raise-budget` authorizes only the configured cap increase and preserves all
previous usage. Omit it for ordinary resumption. The cap is cumulative, not per
command. Unknown charges are quarantined and never retried automatically.
The ledger deliberately reserves conservatively; provider-reported charges and
conservative reservations differ. No services or GPUs remain rented by these commands.

Platform search, profile and topic indexes are discovery material, not accepted
post evidence. Actual fetched posts and indexed excerpts of specific posts have
different evidence labels. A single occurrence does not establish broad popularity.

## Assembly, variants and validation

Start from a retained original release for its existing reading credits:

```sh
mkdir -p work/v0.1-base
git show v0.1.0:data/entries.jsonl > work/v0.1-base/entries.jsonl
```

The baseline's source texts are not needed. Current source contexts and checks
are required for curated entries; an old approval cannot override a current hold.

```sh
python3 -m slangdict.assemble
python3 -m slangdict.lexical_variants --key-file /path/to/key
python3 -m slangdict.assemble
python3 -m slangdict.validate
python3 -m slangdict.audit_local --source /path/to/pinned-chinese.jsonl.gz
python3 -m unittest discover -s tests
```

Explicit source `alt_of` senses can propose abbreviation/respelling links to
specific released target senses. An independent check chooses the exact meaning,
or abstains. Bare lemma alternatives never propagate across all senses.
Public groups link proven equivalents only; unlinked duplicate senses can remain.
The ignored `work/held-v0.2.jsonl` records exclusion reasons. Reports distinguish
source senses, spelling records, distinct spellings and actual social references.
Lossless source provenance is retained in each `sourceImport`, including row,
sense, snapshot and checksum. No website integration or audio generation is part
of these commands.
