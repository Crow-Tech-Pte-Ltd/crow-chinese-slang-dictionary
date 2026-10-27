# Crow Chinese Slang Dictionary

Free, open data describing informal Chinese across regional and overseas Chinese
communities, by [Crow Tech](https://github.com/Crow-Tech-Pte-Ltd).

The aim is **documented use**, including nonstandard spellings, new senses of
familiar words, internet slang, code-switching and vulgar terms with clear labels.
“Common” means within the identified community, not every Chinese speaker.
Regional attestation is not a claim of exclusive origin.

## Initial release

**197 entries, 191 spellings, 21 regional/community groups and 81 cited pages.**
English explanations; 80 entries have a unique existing dictionary reading.
Some evidence is search-excerpt-only and is labelled accordingly. Additional
candidates remain outside the release for evidence, review or source-diversity
limits. This is a starter collection, not a complete inventory of Chinese slang.

## Download

- [English entries, JSONL](data/entries.jsonl) or [gzip JSONL](data/entries.jsonl.gz)
- [Source links and provenance](data/sources.json)
- [Release counts and checksums](data/manifest.json)
- [Entry schema](schema/entry.schema.json)

Each record identifies a spelling, sense and community. The same spelling can
appear with different senses or regional attestations. Definitions are AI-assisted
and checked by a different model against source contexts. **No human review or
complete coverage is claimed.** Uncertain candidates remain outside the release.
Existing dictionary overlap does not establish whether its slang sense is covered.

Pronunciation is included only when a compatible existing dictionary supplies a
unique reading for that spoken variety. Empty readings are intentional; Mandarin
is not substituted for Cantonese, Hokkien or other varieties. Audio is not included.

## Free to use

**Code:** [MIT](LICENSE). **Contributed/compatible derived entry data:**
[CC BY-SA 4.0](DATA_LICENSE.md), permitting commercial reuse with attribution and
ShareAlike. Linked articles retain their copyrights; their full text and proprietary
dictionary definitions are not redistributed.

## Build and contribute

Python 3.10+, standard library only:

```sh
python3 -m unittest discover -s tests
python3 -m slangdict.validate
python3 -m slangdict discover --key-file /path/to/.openrouter-key
python3 -m slangdict attest
python3 -m slangdict review --key-file /path/to/.openrouter-key
python3 -m slangdict build
python3 -m slangdict budget
```

Paid calls are opt-in, resumable and capped at $2 by default in a persistent ledger.
Completed searches and responses are reused. Unknown charges are not retried.
For optional local dictionary overlap/readings, pass `build --inventory PATH`.
Do not commit keys or ignored work files. Corrections with regional context and
public usage sources are welcome. See the [evidence policy](docs/evidence-policy.md).
