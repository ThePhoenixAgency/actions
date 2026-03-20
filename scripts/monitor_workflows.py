#!/usr/bin/env python3
"""
Monitor GitHub Actions workflow status and report issues.
Designed to track failures, timeouts, and performance issues.
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any

def run_gh_command(args: List[str]) -> Dict[str, Any]:
    """Execute gh CLI command and return JSON output."""
    try:
        result = subprocess.run(
            ['gh'] + args + ['--json'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}
    except Exception as e:
        print(f"Error running gh command: {e}")
        return {}

def get_recent_workflow_runs(hours: int = 24) -> List[Dict[str, Any]]:
    """Get recent workflow runs from the past N hours."""
    try:
        # Get runs using gh CLI
        result = subprocess.run(
            ['gh', 'run', 'list', '--limit', '50', '--json',
             'name,status,conclusion,createdAt,updatedAt,url,databaseId'],
            capture_output=True,
            text=True,
            check=True
        )

        runs = json.loads(result.stdout)
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        filtered_runs = []
        for run in runs:
            created_time = datetime.fromisoformat(run['createdAt'].replace('Z', '+00:00'))
            if created_time > cutoff_time:
                filtered_runs.append(run)

        return filtered_runs
    except Exception as e:
        print(f"Error getting workflow runs: {e}")
        return []

def check_failed_or_cancelled_runs() -> List[Dict[str, Any]]:
    """Check for failed or cancelled workflow runs."""
    runs = get_recent_workflow_runs(hours=24)

    problematic_runs = [
        run for run in runs
        if run.get('conclusion') in ['failure', 'cancelled', 'timed_out']
        or run.get('status') == 'in_progress'
    ]

    return problematic_runs

def check_run_durations() -> List[Dict[str, Any]]:
    """Check for runs that took longer than expected (potential timeout risks)."""
    runs = get_recent_workflow_runs(hours=48)

    slow_runs = []
    for run in runs:
        try:
            created = datetime.fromisoformat(run['createdAt'].replace('Z', '+00:00'))
            updated = datetime.fromisoformat(run['updatedAt'].replace('Z', '+00:00'))
            duration = (updated - created).total_seconds() / 60  # minutes

            if duration > 10:  # Warn if taking more than 10 minutes
                slow_runs.append({
                    'name': run['name'],
                    'duration_minutes': round(duration, 2),
                    'status': run.get('status'),
                    'conclusion': run.get('conclusion'),
                    'url': run['url']
                })
        except Exception as e:
            print(f"Error processing run duration: {e}")

    return slow_runs

def generate_report() -> Dict[str, Any]:
    """Generate monitoring report."""
    failed_runs = check_failed_or_cancelled_runs()
    slow_runs = check_run_durations()

    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'failed_runs': len(failed_runs),
        'slow_runs': len(slow_runs),
        'details': {
            'failed': failed_runs[:10],  # Limit to 10 most recent
            'slow': slow_runs[:10]
        }
    }

    return report

def print_report(report: Dict[str, Any]) -> None:
    """Print human-readable report."""
    print("\n" + "="*60)
    print("GitHub Actions Monitoring Report")
    print(f"Generated: {report['timestamp']}")
    print("="*60)

    print(f"\n❌ Failed/Cancelled Runs: {report['failed_runs']}")
    if report['details']['failed']:
        for run in report['details']['failed']:
            print(f"  - {run['name']}: {run['conclusion']} ({run['url']})")

    print(f"\n⏱️  Slow Runs (>10min): {report['slow_runs']}")
    if report['details']['slow']:
        for run in report['details']['slow']:
            print(f"  - {run['name']}: {run['duration_minutes']}min ({run['url']})")

    print("\n" + "="*60 + "\n")

def save_report(report: Dict[str, Any]) -> None:
    """Save report as JSON for upstream processing."""
    os.makedirs('logs', exist_ok=True)
    report_path = f"logs/workflow-report-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Report saved to: {report_path}")

if __name__ == '__main__':
    report = generate_report()
    print_report(report)
    save_report(report)

    # Exit with error if issues found
    if report['failed_runs'] > 0:
        exit(1)
