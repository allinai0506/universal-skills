# Access Pattern Method

A data model is an implementation of the operations the system needs to perform.

For each operation:

```yaml
name:
type: read|write
purpose:
filters:
sort:
joins:
returned_fields:
pagination:
frequency:
expected_result_size:
expected_data_volume:
freshness:
consistency:
```

### Common patterns

**Point lookup**
- Find record by identifier
- Focus on uniqueness and direct lookup

**Range query**
- Orders for a customer between dates
- Focus on filtering, ordering, and index column order

**Top-N**
- Latest 20 orders
- Focus on filter + sort + bounded result

**Aggregation**
- Monthly sales by product
- Focus on scan volume, grouping, and whether precomputation is justified

**Search**
- Keyword search across invoices
- First determine whether ordinary indexes are sufficient or a dedicated search structure is required

The key question is not:

> What tables should I create?

It is:

> What operations must the system perform, and what representation makes those operations correct and sufficiently efficient?
