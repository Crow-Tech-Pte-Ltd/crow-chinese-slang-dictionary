# Crow Chinese Slang Dictionary

Free, open data describing informal Chinese across regional and overseas Chinese
communities, by [Crow Tech](https://github.com/Crow-Tech-Pte-Ltd).

Includes everyday colloquialisms, internet slang, code-switching, playful spellings
and vulgar terms with source labels. “Common” is community-specific; regional
attestation does not establish exclusive origin or present-day popularity.

## Release v0.6

**8,735 spelling-and-sense records across 7,519 distinct spellings.** This includes
4,819 independently selected, openly licensed dictionary senses and 1,504 curated
records. Explicit script forms have separate lookup records. **549 records cite
231 public social pages:** 45 fetched posts and 186 indexed post excerpts.

Alternate spellings are separate entries linked by `formRelations` and
`senseGroupId`. Links apply to the specific meaning and spoken variety. For example,
`蚌埠住了` links to `绷不住了`; literal meanings remain separate. Script forms are
expanded only when explicitly supported by the source; generic lemma alternatives
never inherit every slang sense. Unproved spelling relationships remain unlinked.

This scope correction removes **87 records** of ordinary technical/workplace
vocabulary, literal borrowings and generic English slang. `root`, `router` and
computer storage units are outside this collection. Chinese abbreviations such as
`YYDS` / 永远的神 and `XSWL` / 笑死我了 remain. Decisions apply to individual
senses: the `QQ` emoticon remains while the plain product name is excluded.
[Exclusion reasons](data/scope-exclusions.jsonl) and [build rules](config/slang-scope.json)
are reproducible; a spelling without Hanzi is never rejected for that alone.

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
source-bound whole-word readings for **6,462 records**. Another **2,273 records**
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
The default cap is $2; this expansion used an explicitly raised $8 cumulative cap.
Use the same cap on resumed commands. Keys, raw contexts and model responses stay
in ignored files. [Reproduction commands](docs/reproduction.md) cover source imports,
public-platform searches, review recovery, spelling links and export. Corrections
with regional context and public usage sources are welcome.
