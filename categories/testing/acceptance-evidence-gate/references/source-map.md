# Source & provenance map

The package is **not** a transcription or condensed edition of the book. Rules are engineered for autonomous Coding Agents, with attribution below.

## Book-derived (publisher-hosted original excerpts)

1. Robert C. Martin, *The Clean Coder* (2011), Chapter 4 "Coding", the boxed sidebar **Define "Done"** on printed page 73 (in the "Help" section of Chapter 4). Main point: avoid a false claim of completion by a completion definition grounded in automated acceptance tests understandable to stakeholders and exercised frequently.
   - Publisher sample PDF: https://www.informit.com/content/images/9780137081073/samplepages/0137081073.pdf
2. Chapter 4 "Coding", section **Being Late**, starting on printed page 71: detect slippage early, make progress and risk transparent, and avoid optimism-driven completion claims. The **reporting of blocked/unverified evidence** is an Agent adaptation, not an exact original procedure.
   - Same publisher sample PDF.
3. Chapter 3 "Saying Yes" (publisher-hosted sample of the chapter): commitment must refer to actions under one's control; if something jeopardizes a commitment, surface the issue early.
   - https://www.informit.com/articles/article.aspx?p=1715058
   - Note: this URL is the publisher's web rendition of Chapter 3 ("A Language of Commitment" / "Learning How to Say 'Yes'" / "Conclusion"), paginated as "Page 1 of 3" — it is a chapter sample, not the full printed chapter text.

## Source-derived (publisher metadata)

- Official book and Table of Contents confirm chapters on professionalism, commitments, coding, TDD, acceptance testing, testing strategies, and estimation.
  - https://www.pearson.com/en-us/subject-catalog/p/Martin-Clean-Coder-The-A-Code-of-Conduct-for-Professional-Programmers/P200000009045

## Model-derived engineering adaptation (not directly in the book)

- Acceptance contract schema with criterion IDs, source references and mapped check commands.
- Python standard-library gate: Git HEAD binding, clean-worktree requirement, command execution, timeout, log hashes, contract hash, receipt freshness and structured error codes.
- Separation of executable evidence validation from Agent inspection of semantic test coverage.

These additions are designed to make the book's 'define done' guidance operational and falsifiable in Coding Agent workflows. No claim is made that the original book defines a JSON receipt format, Git clean-worktree gate, or specific script architecture.
