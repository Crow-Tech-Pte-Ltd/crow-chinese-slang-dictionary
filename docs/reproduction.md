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

## Targeted gap round (v0.3)

The coverage audit records research effort and source coverage, not a missing-word
percentage. `config/gap-research-round3.json` adds 56 searches: 16 regional, 12
overseas-community and 28 community/topic searches. Keep the baseline immutable:

```sh
mkdir -p work/v0.2-base
git show v0.2.0:data/entries.jsonl > work/v0.2-base/entries.jsonl
python3 -m slangdict discover --query-file config/gap-research-round3.json --key-file /path/to/key --max-usd 8
python3 -m slangdict.novelty --baseline 0.2.0 --key-file /path/to/key
python3 -m slangdict attest
python3 -m slangdict.curated_resume --key-file /path/to/key
python3 -m slangdict.assemble --version 0.3.0
```

The novelty pass compares definitions for the exact spelling against the frozen
release. Another regional label alone is not a new meaning. Covered/uncertain
candidates are held before independent source review; a new spelling still needs
context and common-use checks. Gap candidates cannot bypass this gate after an
interruption. This triage is cached and is not a popularity judgement. Existing
valid decisions, including rejections, are reused. The same $8 cumulative cap
covers the pilot and both expansion rounds. No Runpod deployment is needed.

The final scope pass checks foreign-script terms and proposed new meanings against
their sources and the baseline. Ordinary English vocabulary and unsupported
community/variety claims are held. Versioned, source-backed language metadata fixes
are recorded in `config/round3-variety-corrections.json`. On a fresh round-3 build,
apply these after attestation, then retriage/reattest before independent review:

```sh
python3 -m slangdict.corrections
python3 -m slangdict.novelty --baseline 0.2.0 --key-file /path/to/key
python3 -m slangdict attest
python3 -m slangdict.curated_resume --key-file /path/to/key
python3 -m slangdict.assemble --version 0.3.0
python3 -m slangdict.scope_audit --baseline 0.2.0 --key-file /path/to/key
python3 -m slangdict.assemble --version 0.3.0
```

A scope veto survives ordinary triage resumption. Changing language metadata
invalidates the independent input hash; a new source-context check is required.
English code-switches are labelled mixed; unresolved regional varieties stay und.
The scope pass does not supply pronunciation or human approval.

## Broader public-source round (v0.4)

`config/broad-research-round4.json` contains 141 targeted queries spanning Chinese
forums, Xiaohongshu topics, media and overseas communities. Preserve the baseline:

```sh
mkdir -p work/v0.3-base
git fetch origin tag v0.3.0
git show v0.3.0:data/entries.jsonl > work/v0.3-base/entries.jsonl
python3 -m slangdict discover --query-file config/broad-research-round4.json --key-file /path/to/key --max-usd 8
```

When a search route yields no usable sources, public search excerpts can be
provided separately. Input is a JSON array of `{url,title,content}` objects from
public, indexed Reddit threads. Keep it ignored in work/, retain the original
ordering for paid-cache reuse, and never include private groups or profiles. The
link-only examined-source catalogue is in reports/public-reddit-source-catalog.json.
A source's inclusion in that catalogue does not mean any entry was accepted.

```sh
python3 -m slangdict.web_discover discover --input work/public-search-seeds.json --key-file /path/to/key
python3 -m slangdict.web_discover import
python3 -m slangdict.novelty --baseline 0.3.0 --key-file /path/to/key
python3 -m slangdict attest
python3 -m slangdict.curated_resume --key-file /path/to/key
python3 -m slangdict.assemble --version 0.4.0
python3 -m slangdict.scope_audit --baseline 0.3.0 --key-file /path/to/key
python3 -m slangdict.assemble --version 0.4.0
```

Run the import after the main discover writer has finished. Seed extraction uses
existing spellings as coverage hints and caps proposed definitions at five per
source. It requires exact literal mentions and exact supplied URLs. Raw excerpts
and responses remain private. Post/profile/index classification now includes
Reddit, NGA, Hupu, V2EX and other forums. Cached page/excerpt dates are preserved
to avoid paying again merely because a command is resumed another day.

For the versioned language correction, run corrections with
`--input config/round4-variety-corrections.json`, then repeat triage, attestation,
current-context review and scope checks. The metadata change invalidates the old
review hash. Finish with offline validation and primary-data auditing:

```sh
python3 -m slangdict.validate
python3 -m slangdict.audit_local --baseline 0.3.0 --source /path/to/pinned-chinese.jsonl.gz
python3 -m unittest discover -s tests
```

The $8 financial cap is unchanged and cumulative across all rounds. The separate
request-count ceiling was expanded to accommodate this larger research plan; it
does not increase the monetary cap. Xiaohongshu access limits are reported rather
than treated as successful full reads. No website or audio deployment is implied.


Pronunciation evidence (no audio assets):

```sh
python3 -m slangdict.pronunciations --inventory /path/to/private/audio-inventory
python3 -m slangdict.validate
```

The inventory must account for every released entry using `record-readings.jsonl`
and `unresolved.jsonl`. Whole-word source readings are kept separately from lexical
variety labels; no character-by-character guesses are accepted. Regenerate this
sidecar after rebuilding the lexical dataset. The website serves audio separately.

## Chinese slang scope

Both corpus builders apply `config/slang-scope.json` before export. Ordinary
technical labels, generic English slang and literal borrowings do not qualify
just because a source calls them colloquial or a Chinese-speaking person uses
them. Chinese abbreviations, regional expressions and Chinese-specific semantic
shifts remain eligible. Decisions are per sense and bound to definition hashes.
To reproduce this correction against the v0.5.0 data (or reapply idempotently):

```sh
python3 -m slangdict.scope --version 0.6.0
python3 -m slangdict.pronunciations --inventory /path/to/private/slang-audio-inventory
python3 -m unittest discover -s tests
python3 -m slangdict.validate
```

Filtered inventory rows are skipped only when their ID and spelling match the
explicit exclusion queue. Audio assets are unchanged and are never copied here.


## Whole-corpus scope review (v0.7.0)

Start from the v0.6.0 input release. Review units separate Hanzi script variants
from foreign-script forms even when they share a sense group. Private retained
source excerpts improve review but are not redistributed. Automated classification
is scope selection, not independent attestation or human review.

```sh
python3 -m slangdict.full_review --key-file /path/to/key --max-usd 10 --raise-budget --pilot
python3 -m slangdict.full_review --key-file /path/to/key --max-usd 10
python3 -m slangdict.recover_full_review
# Resume with --batch-size 3 if a batch had malformed rows; valid results skip.
python3 -m slangdict.full_review --key-file /path/to/key --max-usd 10 --role adjudicator
python3 -m slangdict.recover_full_review
python3 -m slangdict.finalize_full_scope
python3 -m slangdict.finalize_full_scope --apply
python3 -m slangdict.validate
python3 -m unittest discover -s tests
```

The finalizer requires complete, input-hash-bound reviews before applying any
change. It accepts two keep votes, holds uncertainty, and applies explicit
sense-bound product-scope exclusions. Its frozen-input assertion prevents a
second application to a changed release. The final public audit contains
review IDs and reasons, without raw source contexts or provider responses.
The release validator and website importer reject unapproved or changed senses.
