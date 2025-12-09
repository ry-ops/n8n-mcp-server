# Enhanced Workflow Filtering Guide

This document describes the enhanced filtering capabilities for the `list_workflows` tool in the n8n-mcp-server.

## Overview

The `list_workflows` tool now supports advanced filtering options that allow you to find workflows based on multiple criteria. Filters can be combined to create powerful search queries.

## Available Filters

### 1. Active Status Filter (`active`)

**Type:** Boolean
**API Support:** Yes (server-side filtering)

Filter workflows by their active/inactive status.

**Examples:**
```json
{"active": true}   // Only active workflows
{"active": false}  // Only inactive workflows
```

**Usage with Claude:**
> "Show me all active workflows"
> "List inactive workflows"

---

### 2. Name Filter (`name`)

**Type:** String
**API Support:** No (client-side filtering)
**Matching:** Case-insensitive substring match

Filter workflows by name. Finds any workflow whose name contains the specified text.

**Examples:**
```json
{"name": "email"}       // Matches "Email Campaign", "Send Email", etc.
{"name": "prod"}        // Matches "Production Deploy", "Prod Backup", etc.
{"name": "Daily Report"} // Matches workflows with "Daily Report" in name
```

**Usage with Claude:**
> "Show me all workflows with 'email' in the name"
> "Find workflows related to production"
> "List all daily report workflows"

---

### 3. Tags Filter (`tags`)

**Type:** String (comma-separated)
**API Support:** No (client-side filtering)
**Matching:** Case-insensitive, must have ALL specified tags

Filter workflows by tags. When multiple tags are specified (comma-separated), the workflow must have ALL of them.

**Examples:**
```json
{"tags": "production"}              // Workflows with "production" tag
{"tags": "production, critical"}    // Workflows with BOTH tags
{"tags": "email, automated, daily"} // Workflows with all three tags
```

**Usage with Claude:**
> "Show workflows tagged with production"
> "Find workflows that have both production and critical tags"
> "List all automated email workflows" (assuming tags exist)

---

### 4. Created After Filter (`created_after`)

**Type:** String (ISO 8601 date format)
**API Support:** No (client-side filtering)
**Matching:** Workflows created on or after the specified date

Filter workflows by creation date. Only shows workflows created after (or on) the specified date.

**Supported Date Formats:**
- `YYYY-MM-DD` (e.g., "2024-12-01")
- `YYYY-MM-DDTHH:MM:SSZ` (e.g., "2024-12-01T10:30:00Z")
- `YYYY-MM-DDTHH:MM:SS.fffZ` (e.g., "2024-12-01T10:30:00.123Z")

**Examples:**
```json
{"created_after": "2024-12-01"}
{"created_after": "2024-12-01T00:00:00Z"}
{"created_after": "2024-01-01"}
```

**Usage with Claude:**
> "Show me workflows created after December 1st, 2024"
> "Find workflows created this month"
> "List workflows created in the last week"

---

### 5. Updated After Filter (`updated_after`)

**Type:** String (ISO 8601 date format)
**API Support:** No (client-side filtering)
**Matching:** Workflows updated on or after the specified date

Filter workflows by last update date. Only shows workflows that were modified after (or on) the specified date.

**Supported Date Formats:** Same as `created_after`

**Examples:**
```json
{"updated_after": "2024-12-01"}
{"updated_after": "2024-12-01T10:30:00Z"}
```

**Usage with Claude:**
> "Show me workflows updated in the last 7 days"
> "Find workflows modified after December 1st"
> "List recently updated workflows"

---

## Combining Filters

Filters can be combined for powerful searches. All specified filters must match (AND logic).

### Example 1: Active Production Workflows
```json
{
  "active": true,
  "tags": "production"
}
```

**Claude:** "Show me active production workflows"

### Example 2: Recent Email Workflows
```json
{
  "name": "email",
  "created_after": "2024-11-01",
  "tags": "automated"
}
```

**Claude:** "Find email workflows created after November 1st with the automated tag"

### Example 3: Recently Updated Production Critical Workflows
```json
{
  "tags": "production, critical",
  "updated_after": "2024-12-01",
  "active": true
}
```

**Claude:** "Show me active workflows with production and critical tags that were updated after December 1st"

---

## Implementation Details

### API-Level vs Client-Side Filtering

**API-Level Filtering (Server-Side):**
- `active` - Handled by n8n API
- More efficient for large workflow lists
- Reduces data transfer

**Client-Side Filtering:**
- `name`, `tags`, `created_after`, `updated_after`
- Processed after fetching workflows from the API
- Allows for advanced filtering not supported by the n8n API
- Still efficient for typical workflow counts (< 1000 workflows)

### Performance Considerations

1. **Use `active` filter first** - This reduces the dataset at the API level
2. **Combine filters** - Multiple filters narrow results efficiently
3. **Date filters** - Very efficient for finding recent workflows
4. **Tag filters** - Efficient when workflows are properly tagged

---

## Use Cases

### 1. Finding Active Production Workflows
```json
{
  "active": true,
  "tags": "production"
}
```

### 2. Identifying Stale Workflows
```json
{
  "updated_after": "2024-01-01"
}
```
Then look for workflows NOT in the results (i.e., not updated this year).

### 3. Audit New Workflows
```json
{
  "created_after": "2024-12-01"
}
```

### 4. Finding Specific Workflow Types
```json
{
  "name": "backup",
  "tags": "daily, automated"
}
```

### 5. Production Health Check
```json
{
  "tags": "production, critical",
  "active": true
}
```

### 6. Recent Changes Review
```json
{
  "updated_after": "2024-12-07",
  "tags": "production"
}
```

---

## Error Handling

### Invalid Date Format
If you provide an invalid date format, you'll receive an error:
```
Error: Invalid created_after date format: Date must be in ISO 8601 format
```

**Solution:** Use one of the supported formats (YYYY-MM-DD or ISO 8601 with time)

### No Matches
If no workflows match your filters, you'll receive an empty list:
```json
{"data": []}
```

This is normal and indicates no workflows meet your criteria.

---

## Backwards Compatibility

The enhanced filtering is fully backwards compatible:
- Existing `active` filter works exactly as before
- All existing API calls continue to function
- New filters are optional - omit them for unfiltered results

---

## Testing

Comprehensive test coverage includes:
- Individual filter tests
- Combined filter tests
- Edge cases (no matches, invalid formats)
- Case-insensitive matching
- Date parsing variations

Run tests:
```bash
uv run pytest tests/test_workflows.py -v
```

---

## Examples with Claude Desktop

### Morning Check-In
> "Good morning! Show me all active production workflows updated in the last 24 hours"

### Audit Report
> "List all workflows created this month with the production tag"

### Cleanup Planning
> "Find all inactive workflows that haven't been updated this year"

### Deployment Verification
> "Show me workflows with 'deploy' in the name that are tagged production and critical"

### Tag Management
> "List all workflows tagged with 'test' or 'dev' so I can clean them up"

---

## Tips for Best Results

1. **Be specific with dates** - Use ISO 8601 format for precision
2. **Use lowercase for tags** - Matching is case-insensitive, but lowercase is clearer
3. **Combine filters** - Multiple filters create powerful queries
4. **Start broad, then narrow** - If unsure, start with fewer filters
5. **Use natural language with Claude** - Claude understands conversational requests

---

## Migration from Basic Filtering

If you were using basic filtering, here's how to upgrade:

**Before:**
```json
{"active": true}
```

**After (same result):**
```json
{"active": true}
```

**Enhanced (more specific):**
```json
{
  "active": true,
  "tags": "production",
  "updated_after": "2024-12-01"
}
```

---

## Roadmap

Future enhancements under consideration:
- OR logic for tags (match ANY tag instead of ALL)
- Created before / Updated before filters
- Workflow name regex support
- Custom date ranges (last 7 days, last month, etc.)
- Performance optimizations for large deployments

---

## Support

For issues or questions:
- GitHub Issues: [n8n-mcp-server](https://github.com/ry-ops/n8n-mcp-server/issues)
- See also: [n8n API Documentation](https://docs.n8n.io/api/)

---

## Version History

**v1.1.0** (Enhanced Filtering)
- Added `name` filter (case-insensitive substring match)
- Added `tags` filter (comma-separated, must have all)
- Added `created_after` filter (ISO 8601 date)
- Added `updated_after` filter (ISO 8601 date)
- Comprehensive test coverage
- Full backwards compatibility

**v1.0.0** (Initial Release)
- Basic `active` status filter
