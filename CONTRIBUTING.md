# Contributing

Connect is documentation and ecosystem infrastructure. It is not a runtime product.

## What this repository is for

- Explaining how the products fit together
- Combined installation instructions
- Architecture across product boundaries
- The compatibility matrix and the known-gaps list
- Engineering philosophy

## What must never be added here

- Libraries or Python packages
- Services or daemons
- APIs
- Any code that is imported, installed, or executed as part of using the ecosystem

Small, illustrative snippets inside documentation are fine — they are prose. A `setup.py`
is not. If a change to Connect would make someone `pip install` this repository, the
change belongs in a product repository instead.

## What belongs in a product repository

Anything about installing, configuring, or using **one** product. Connect states the
product's purpose in a paragraph and links out. It does not mirror the product's own
documentation, because a mirror drifts and the drift is discovered by a user who trusted
the wrong copy.

The dividing question: *would this document still make sense if the other three products
did not exist?* If yes, it belongs to that product.

The exception is [COMPATIBILITY.md](COMPATIBILITY.md), which is intended to be canonical
across the ecosystem. Product repositories should link to it rather than maintain their own
matrix, so that a cross-product claim has exactly one place to be wrong.

## The documentation standard

This repository is where the ecosystem's honesty principle is most easily broken, because
nothing here fails to compile when it becomes false.

**Verify before you assert.** Every claim about a product must be checked against that
product's current code, not its README, its roadmap, or your memory of it. If you write
that an interface exists, name the module. If you write that a command works, run it.

**Distinguish what exists from what is designed.** The convention throughout these
documents:

- Solid arrows in diagrams, plain prose: paths that exist in code today.
- Dashed arrows, explicit labels: contracts defined but not implemented, or designs not
  yet built.
- A section describing an unbuilt system says so in its first sentence, in bold.

**Describe a test suite by what it exercises.** An in-process test verifies semantics. It
does not verify a network path. Say which one you have.

**Name missing features where a reader would look for them**, not in a footnote. If
`wiki serve` does not exist, the sentence about reaching BrainConnect over HTTP is the
sentence that says so.

**Prose is bounded by what a product has published.** A product with no charter gets no
description at all. A product with a written charter but no runtime — ComputeConnect today —
gets exactly its charter, labelled *design phase*, with no timeline, no implied capability,
and no undashed arrow in any diagram. A validation prototype that its own authors call "not
the product" — ToolConnect today — earns a mention of what the prototype proved and a
*validation phase* label, but still no runtime prose: it has no server and no tool execution,
and the docs must say so. A product with a runnable release gets described by that release.
Never let a design document or a throwaway prototype be quoted as though it were the shipped
product.

The failure mode this rule exists to prevent is subtle: a charter is written to be
persuasive, and prose lifted from it will read as a description of something that works.
Say what phase it is in, in the same breath.

## Proposing a scope for a pre-runtime product

Open an issue on this repository. A scope proposal should answer:

1. What does it do that no existing product does?
2. Can it stand alone? (See [MANIFESTO.md](MANIFESTO.md#1-standalone-first) — if it cannot,
   it is a module of something else.)
3. What is the contract? Which product owns the interface, and does that interface already
   exist?
4. What is it explicitly *not*?

Question 4 is not optional. Every product in this ecosystem states its boundary, and the
boundary is the most useful sentence in its README. ComputeConnect is not an inference
engine. ToolConnect is not a tool-execution proxy. Both sentences do more work than the
paragraphs around them.

## Style

- Markdown. Mermaid for diagrams — GitHub renders it, and it stays reviewable in a diff.
- Wrap prose at roughly 90 characters.
- Link between documents with relative paths.
- Prefer a table to a bulleted list of pairs. Prefer prose to a table of sentences.
- Write out the technical term. The reader is a new user; they do not know your shorthand.

## Changes to the manifesto

[MANIFESTO.md](MANIFESTO.md) makes claims about how the code behaves, and each principle
cites its enforcement. If a principle's enforcement changes, the manifesto is wrong and
must be corrected in the same change that broke it.

A principle that is aspirational rather than enforced must say so. An unenforced principle
presented as an enforced one is the specific failure the last section of that document
exists to prevent.
