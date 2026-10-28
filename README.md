# Crow Chinese Slang Dictionary

Free, open data describing informal Chinese across regional and overseas Chinese
communities, by [Crow Tech](https://github.com/Crow-Tech-Pte-Ltd).

Includes everyday colloquialisms, internet slang, code-switching, playful spellings
and vulgar terms with source labels. “Common” is community-specific; regional
attestation does not establish exclusive origin or present-day popularity.

## Release v0.7

**7,455 spelling-and-sense records across 6,429 distinct spellings.** Includes
4,089 selected openly licensed source senses and 1,328 curated records, with
script variants linked by `formRelations` and `senseGroupId`.

A fresh review of all 8,735 previous records removes or holds **1,280 more
records**: English novelty puns such as `propoorty`, generic jargon, neutral
vocabulary and uncertain senses. Chinese abbreviations such as `YYDS` and `XSWL`,
Chinese semantic shifts and regional slang remain. Every meaning received two
independent automatic checks; proposed exclusions received a third check.
[Decisions](data/full-scope-review.jsonl.gz), [exclusion reasons](data/scope-exclusions.jsonl)
and [definition-bound release approvals](config/slang-scope.json) are reproducible.
New or changed senses require fresh approval. Non-Hanzi spelling alone is not a
rejection reason. No human review or verified frequency is claimed.

## Download

- [Entries, JSONL](data/entries.jsonl) or [gzip JSONL](data/entries.jsonl.gz)
- [Source links and credits](data/sources.json)
- [Counts and checksums](data/manifest.json), [entry schema](schema/entry.schema.json)

Source imports retain Wiktionary definitions and labels with attribution.
Curated explanations are AI-assisted original summaries. DeepSeek and GLM perform
separate selection/checking roles. **No human review or complete coverage is
claimed.** Machine familiarity is not a frequency measurement. Uncertain candidates
remain outside the release; linked groups do not exhaust all equivalent senses.

A separate [pronunciation evidence file](data/pronunciations.jsonl.gz) supplies
source-bound whole-word readings for **5,580 records**. Another **1,875 records**
remain [unresolved or unsupported](data/pronunciation-unresolved.jsonl.gz).
Readings keep their source attribution and do not change the lexical variety label.
They do not certify local accents or generated audio. Audio is not included.

## Free to use

**Code:** [MIT](LICENSE). **Entry data:** [CC BY-SA 4.0](DATA_LICENSE.md), allowing
commercial reuse with attribution and ShareAlike. Retain [upstream credits](data/NOTICE.txt).
Linked articles and social posts retain their copyrights; their prose is not
redistributed. See the [evidence policy](docs/evidence-policy.md).

## Build and contribute

Python 3.10+, standard library only. Offline validation:

```sh
python3 -m unittest discover -s tests
python3 -m slangdict.validate
```

Optional paid research is resumable, cached and bounded by a persistent ledger.
The default cap is $2; this expansion used an explicitly raised $10 cumulative cap.
Use the same cap on resumed commands. Keys, raw contexts and model responses stay
in ignored files. [Reproduction commands](docs/reproduction.md) cover source imports,
public-platform searches, review recovery, spelling links and export. Corrections
with regional context and public usage sources are welcome.
