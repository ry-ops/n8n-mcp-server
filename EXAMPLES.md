# n8n MCP Server - Usage Examples

This document provides practical examples of common tasks you can accomplish with Claude using the n8n MCP Server.

## Table of Contents
1. [Workflow Management](#workflow-management)
2. [Execution Management](#execution-management)
3. [Debugging & Monitoring](#debugging--monitoring)
4. [Bulk Operations](#bulk-operations)
5. [Advanced Workflows](#advanced-workflows)

---

## Workflow Management

### Example 1: List All Workflows

**You ask Claude:**
> "Show me all my n8n workflows"

**What happens:**
Claude uses `list_workflows` and displays all your workflows with their IDs, names, and active status.

---

### Example 2: List Only Active Workflows

**You ask Claude:**
> "Which workflows are currently active?"

**What happens:**
Claude uses `list_workflows` with `active: true` filter to show only running workflows.

---

### Example 3: Get Workflow Details

**You ask Claude:**
> "Tell me about the email campaign workflow"

**What happens:**
1. Claude searches workflows by name
2. Uses `get_workflow` with the workflow ID
3. Shows you the nodes, connections, and settings

---

### Example 4: Activate a Workflow

**You ask Claude:**
> "Activate the daily backup workflow"

**What happens:**
1. Claude finds the workflow by name
2. Uses `activate_workflow` with the workflow ID
3. Confirms the workflow is now active

---

### Example 5: Deactivate Multiple Workflows

**You ask Claude:**
> "Deactivate all workflows tagged with 'testing'"

**What happens:**
1. Claude lists workflows
2. Filters by the 'testing' tag
3. Uses `deactivate_workflow` for each matching workflow
4. Confirms all were deactivated

---

## Execution Management

### Example 6: Execute a Workflow

**You ask Claude:**
> "Execute the email campaign workflow"

**What happens:**
Claude uses `execute_workflow` and triggers a manual execution.

---

### Example 7: Execute with Data

**You ask Claude:**
> "Execute the customer notification workflow with this data: name=John, email=john@example.com"

**What happens:**
Claude uses `execute_workflow` with the data payload:
```json
{
  "data": {
    "name": "John",
    "email": "john@example.com"
  }
}
```

---

### Example 8: List Recent Executions

**You ask Claude:**
> "Show me the last 10 workflow executions"

**What happens:**
Claude uses `list_executions` with `limit: 10` to show recent executions.

---

### Example 9: Check Failed Executions

**You ask Claude:**
> "Show me all failed executions from today"

**What happens:**
Claude uses `list_executions` with `status: error` filter.

---

### Example 10: Get Execution Details

**You ask Claude:**
> "What happened in execution abc123?"

**What happens:**
Claude uses `get_execution` to show detailed execution information including node outputs and errors.

---

## Debugging & Monitoring

### Example 11: Debug a Failed Workflow

**You ask Claude:**
> "Why did the customer sync workflow fail?"

**What happens:**
1. Claude finds the workflow
2. Gets recent executions for that workflow
3. Filters for failed executions
4. Shows error messages and node failures

---

### Example 12: Monitor Workflow Health

**You ask Claude:**
> "Which workflows have been failing recently?"

**What happens:**
1. Claude lists recent executions with error status
2. Groups them by workflow
3. Shows you patterns and common failures

---

### Example 13: Check Execution Time

**You ask Claude:**
> "How long did the data processing workflow take to run?"

**What happens:**
Claude gets the execution details and calculates the duration.

---

### Example 14: View Workflow Activity

**You ask Claude:**
> "Show me all executions for the daily report workflow in the last 7 days"

**What happens:**
Claude lists executions filtered by workflow ID and time range.

---

## Bulk Operations

### Example 15: Activate All Production Workflows

**You ask Claude:**
> "Activate all workflows tagged with 'production'"

**What happens:**
1. Claude lists workflows
2. Filters by 'production' tag
3. Activates each one
4. Confirms activation

---

### Example 16: Deactivate Old Test Workflows

**You ask Claude:**
> "Deactivate all workflows with 'test' or 'dev' in their name"

**What happens:**
1. Claude lists all workflows
2. Filters by name pattern
3. Deactivates matching workflows

---

### Example 17: Clean Up Failed Executions

**You ask Claude:**
> "Delete all failed executions older than 30 days"

**What happens:**
1. Claude lists old failed executions
2. Uses `delete_execution` for each one
3. Confirms cleanup

---

### Example 18: Status Report

**You ask Claude:**
> "Give me a summary of all my workflows - how many active, inactive, total executions today, success rate"

**What happens:**
1. Claude lists all workflows and calculates statistics
2. Lists today's executions
3. Calculates success rate
4. Presents a formatted report

---

## Advanced Workflows

### Example 19: Create a Simple Workflow

**You ask Claude:**
> "Create a new workflow called 'Test Webhook' with a webhook trigger"

**What happens:**
Claude uses `create_workflow` with basic nodes:
```json
{
  "name": "Test Webhook",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "parameters": {
        "path": "test-webhook",
        "responseMode": "onReceived"
      }
    }
  ]
}
```

---

### Example 20: Update Workflow Settings

**You ask Claude:**
> "Update the email campaign workflow to use error workflow handling"

**What happens:**
Claude uses `update_workflow` to modify the settings.

---

### Example 21: Compare Workflow Performance

**You ask Claude:**
> "Compare execution times between the old and new data processing workflows"

**What happens:**
1. Claude gets executions for both workflows
2. Calculates average execution time for each
3. Presents a comparison

---

### Example 22: Workflow Dependency Check

**You ask Claude:**
> "Which workflows depend on the customer database credential?"

**What happens:**
1. Claude lists all workflows
2. Gets details for each
3. Checks which ones use that credential
4. Shows the list

---

### Example 23: Execution Success Trend

**You ask Claude:**
> "Show me the success rate trend for the daily sync workflow over the past month"

**What happens:**
1. Claude gets all executions for that workflow
2. Groups by date
3. Calculates success rate per day
4. Shows the trend

---

### Example 24: Find Unused Workflows

**You ask Claude:**
> "Which workflows haven't been executed in the last 30 days?"

**What happens:**
1. Claude lists all workflows
2. Gets executions for each
3. Identifies workflows with no recent executions

---

### Example 25: Emergency Shutdown

**You ask Claude:**
> "Something's wrong! Deactivate all workflows immediately"

**What happens:**
1. Claude lists all active workflows
2. Deactivates each one quickly
3. Confirms all are stopped

---

## Real-World Scenarios

### Scenario 1: Morning Check-In

**You ask Claude:**
> "Good morning! What's the status of my automation?"

**What happens:**
1. Lists active workflows
2. Shows executions from last 24 hours
3. Highlights any failures
4. Gives you a quick health report

---

### Scenario 2: Deployment

**You ask Claude:**
> "I'm deploying new workflows. Deactivate all 'staging' workflows and activate all 'production' workflows"

**What happens:**
1. Deactivates staging workflows
2. Activates production workflows
3. Confirms the switch

---

### Scenario 3: Troubleshooting

**You ask Claude:**
> "The customer sync has been failing. Show me the last 5 failures with error details"

**What happens:**
1. Gets recent failed executions
2. Shows error messages
3. Identifies which node failed
4. Helps you understand the issue

---

### Scenario 4: Audit

**You ask Claude:**
> "I need an audit report - list all workflows, their last execution time, and success rates"

**What happens:**
Claude generates a comprehensive report with all requested information.

---

## Tips for Best Results

1. **Be specific**: "Activate the email workflow" is better than "start something"
2. **Use names or IDs**: Reference workflows by name or ID for accuracy
3. **Ask for confirmation**: For destructive actions, Claude will ask before proceeding
4. **Use natural language**: Claude understands conversational requests
5. **Iterate**: If the first result isn't perfect, ask Claude to adjust it

## Common Patterns

### Safe Updates
> "Show me the workflow details before we activate it"

### Verification
> "After executing that, show me the execution result to verify it worked"

### Batch Operations
> "Do the same thing for all workflows tagged with 'daily'"

### Conditional Actions
> "If the workflow exists, update it. Otherwise, create a new one."

---

## Integration with Other Tools

Since n8n is about automation, you can combine this with other MCP servers:

### Example: n8n + Cloudflare
> "Execute the deploy workflow, and when it succeeds, purge the Cloudflare cache for example.com"

### Example: n8n + Monitoring
> "If any workflows fail, send me a notification"

---

Need more examples? Just ask Claude for help with your specific use case!
