# GitHub Actions & Logs Monitoring

Automated monitoring solution for tracking GitHub Actions workflow status and aggregating logs from failed runs.

## Overview

This monitoring system provides:

- **Real-time workflow status checks** - Detects failed, cancelled, or timed-out runs
- **Duration monitoring** - Alerts on runs taking longer than expected (timeout risk)
- **Log aggregation** - Collects and analyzes logs from recent failed runs
- **Error pattern detection** - Identifies common failure patterns across runs
- **Slack integration** - Sends alerts to designated Slack channel

## Configuration

### 1. Slack Webhook Setup

Add the Slack webhook URL to your repository secrets:

```bash
gh secret set SLACK_WEBHOOK_URL --body "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

To create a webhook:
1. Go to [Slack App Configuration](https://api.slack.com/apps)
2. Create a new app or select existing
3. Enable "Incoming Webhooks"
4. Create a new webhook for your channel
5. Copy the webhook URL

### 2. Enable Workflow Permissions

In your repository settings, ensure the workflow has:
- `contents: read` - To read repository content
- `actions: read` - To query workflow status
- `checks: read` - To access workflow details

## Workflows

### `monitor-logs-actions.yaml`

Runs every 15 minutes and on manual trigger (`workflow_dispatch`).

**Jobs:**

#### `monitor-workflows`
- Checks recent workflow runs (past 24 hours)
- Identifies failed, cancelled, or timed-out runs
- Detects slow runs (>10 minutes)
- Sends Slack alert on issues

#### `monitor-logs`
- Collects logs from failed runs
- Analyzes error patterns
- Uploads logs as artifacts (7-day retention)
- Sends summary to Slack

## Scripts

### `scripts/monitor_workflows.py`

Main monitoring script that:
- Queries recent workflow runs
- Checks for failures and timeouts
- Measures run durations
- Generates JSON report

**Output:**
- Console report with summary
- JSON report in `logs/workflow-report-*.json`
- Exit code 1 if issues found (for CI integration)

**Usage:**
```bash
python scripts/monitor_workflows.py
```

### `scripts/collect_logs.py`

Log aggregation script that:
- Fetches recent failed run logs
- Extracts error patterns
- Saves individual run logs
- Generates analysis summary

**Output:**
- Individual run logs: `logs/run-{number}.log`
- Analysis summary: `logs/analysis-*.json`
- Prints error pattern statistics

**Usage:**
```bash
python scripts/collect_logs.py
```

## Usage

### Manual Trigger

Manually run the monitoring workflow:

```bash
gh workflow run monitor-logs-actions.yaml
```

### View Workflow Runs

```bash
# List recent monitoring runs
gh run list --workflow monitor-logs-actions.yaml

# View specific run
gh run view {run-id} --log
```

### Download Artifacts

```bash
# List available artifacts
gh run list --workflow monitor-logs-actions.yaml

# Download logs from specific run
gh run download {run-id} -D ./downloaded-logs
```

## Alert Types

### ❌ Failed/Cancelled Runs
- Detected when workflow conclusion is `failure` or `cancelled`
- Includes run name, status, and link to GitHub Actions

### ⏱️ Slow Runs
- Triggered when run duration exceeds 10 minutes
- Helps identify potential timeout risks
- Shows actual duration for analysis

### ⚠️ Error Patterns
- Timeout errors
- Out of memory errors
- Connection/network errors
- Authentication errors
- Not found errors (missing dependencies, etc.)

## Integration Points

### Slack Notifications

Alerts are sent in two formats:

1. **Failure Alert** - Sent immediately if issues detected
2. **Summary Report** - Sent after log collection complete

Example Slack message:
```
:warning: GitHub Actions Monitoring Alert

Failed workflow detected. Check logs for details.
Repository: owner/repo
Run: [View Details]
```

## Troubleshooting

### Webhook Not Working

1. Verify webhook URL is correct and active
2. Check repository secrets are set: `gh secret list`
3. Check workflow permissions in repository settings
4. Review workflow logs: `gh run view {run-id} --log`

### Missing Logs

- Logs retention is 90 days in GitHub
- Script downloads limited to 50 most recent runs
- May timeout on large workflows (>1000 lines)

### No Failed Runs Detected

- Script only checks past 24 hours
- Increase time range in `monitor_workflows.py` if needed
- Use `gh run list --all` to see all runs

## Performance Considerations

- Script queries limited to 50 recent runs per job
- Log downloads may timeout on very large logs
- Slack webhooks have rate limits (1 request/second)
- Artifacts retained for 7 days only

## Future Enhancements

- [ ] Database storage for trend analysis
- [ ] Custom time windows for monitoring
- [ ] Automatic retry logic for transient failures
- [ ] Integration with incident management (PagerDuty, etc.)
- [ ] Custom alerting rules per workflow
- [ ] Performance trend reports

## Support

For issues or questions:
1. Check workflow logs: `gh run view {run-id} --log`
2. Verify script permissions: `gh auth status`
3. Review Slack webhook configuration
4. Check GitHub Actions status page

---

**Status:** Active
**Last Updated:** 2026-03-20
**Branch:** `claude/slack-monitor-logs-actions-F0B0n`
