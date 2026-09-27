# Semantic Conflict Detection

## 1. Synonym collision

Multiple names may represent one concept:

- TenderDocument
- TenderFile
- BidFile
- ProjectDocument

Decision required: alias, deprecated name, or truly different object.

## 2. Homonym collision

The same name may represent different concepts.

Example: `status` may mean upload status, parse job status, business state, approval state, or archive state.

Rule: split distinct lifecycles into distinct names.

## 3. Representation collision

Do not conflate:

- business object;
- database row;
- binary file;
- extracted text;
- AI interpretation;
- search index document.

Each may represent the same business object but is not the same semantic thing.

## 4. State/result collision

`PARSED` must not ambiguously mean both “the parser ran” and “the parsed result is verified for business use.”

Use separate states when business guarantees differ.

## 5. Hidden fallback collision

Patterns such as “A else B else history” often indicate unresolved authority.

Ask:

- Is fallback an approved business rule?
- Is B a cache/projection or a second authority?
- Does fallback hide data corruption?

## 6. Conflict outcomes

Every conflict must resolve to one of:

- `RESOLVED`: canonical definition recorded;
- `DEPRECATED`: old name/path is explicitly legacy;
- `UNVERIFIED`: evidence insufficient;
- `BLOCKED`: contradictory authoritative rules.
