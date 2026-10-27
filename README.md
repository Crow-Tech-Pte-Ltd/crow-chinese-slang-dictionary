# Crow Chinese Slang Dictionary

Free, open data describing informal Chinese across regional and overseas Chinese
communities, by [Crow Tech](https://github.com/Crow-Tech-Pte-Ltd).

Includes everyday colloquialisms, internet slang, code-switching, playful spellings
and vulgar terms with source labels. “Common” is community-specific; regional
attestation does not establish exclusive origin or present-day popularity.

## Release v0.4

**8,822 spelling-and-sense records across 7,593 distinct spellings.** This includes
4,860 independently selected, openly licensed dictionary senses and 1,546 curated
records. Explicit script forms have separate lookup records. **568 records cite
231 public social pages:** 45 fetched posts and 186 indexed post excerpts.

Alternate spellings are separate entries linked by `formRelations` and
`senseGroupId`. Links apply to the specific meaning and spoken variety. For example,
`蚌埠住了` links to `绷不住了`; literal meanings remain separate. Script forms are
expanded only when explicitly supported by the source; generic lemma alternatives
never inherit every slang sense. Unproved spelling relationships remain unlinked.

This round adds **473 records and 412 new spellings**, with 141 broader source
queries and a separate examination of 87 public Chinese-language Reddit threads.
It includes 98 new records from that Reddit research. Forums, Chinese media and
overseas communities are covered; direct Xiaohongshu access is limited, so its
coverage relies mainly on public excerpts and media reporting.

## Download

- [Entries, JSONL](data/entries.jsonl) or [gzip JSONL](data/entries.jsonl.gz)
- [Source links and credits](data/sources.json)
- [Counts and checksums](data/manifest.json), [entry schema](schema/entry.schema.json)

Source imports retain Wiktionary definitions and labels with attribution.
Curated explanations are AI-assisted original summaries. DeepSeek and GLM perform
separate selection/checking roles. **No human review or complete coverage is
claimed.** Machine familiarity is not a frequency measurement. Uncertain candidates
remain outside the release; linked groups do not exhaust all equivalent senses.

Readings are supplied only from a compatible dictionary with a unique reading for
the stated variety. Unknown readings stay empty. Audio is not included.

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
