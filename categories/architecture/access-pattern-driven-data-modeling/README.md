# Access Pattern Driven Data Modeling

Complete Agent Skill Package distilled from the engineering principles in
*Designing Data-Intensive Applications*.

## Structure

- `SKILL.md` — execution contract
- `references/` — detailed engineering knowledge loaded when needed
- `scripts/` — deterministic validation
- `assets/` — reusable input template

## Use

1. Copy this directory into the Agent's skill directory.
2. Trigger it for schema/model/index/query design tasks.
3. Copy `assets/access-patterns.example.yaml` into the project and replace it with real access patterns.
4. Run:

```bash
python scripts/validate_access_patterns.py <your-inventory.yaml>
```

5. For critical queries, inspect actual database execution plans and run representative workload tests.

The validator checks input completeness. It does not prove that a database design is optimal.
