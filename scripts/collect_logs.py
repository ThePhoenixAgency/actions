#!/usr/bin/env python3
"""
Collect and aggregate logs from recent GitHub Actions runs.
Helps identify patterns and recurring issues.
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re

def get_recent_failed_runs(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent failed workflow runs."""
    try:
        result = subprocess.run(
            ['gh', 'run', 'list', '--status', 'failure', '--limit', str(limit),
             '--json', 'name,number,status,conclusion,createdAt,updatedAt,url,databaseId'],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error fetching failed runs: {e}")
        return []

def get_run_logs(run_number: int) -> str:
    """Download logs for a specific run."""
    try:
        result = subprocess.run(
            ['gh', 'run', 'view', str(run_number), '--log'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        print(f"Error getting logs for run {run_number}: {e}")
        return ""

def extract_error_patterns(logs: str) -> List[str]:
    """Extract common error patterns from logs."""
    patterns = {
        'timeout': r'.*timeout.*',
        'out_of_memory': r'.*(out of memory|OOM|FATAL: OutOfMemory).*',
        'connection_error': r'.*(connection|socket|network|timeout).*',
        'authentication': r'.*(auth|permission|forbidden|401|403).*',
        'not_found': r'.*(not found|404|no such file).*',
    }

    errors = {}
    for error_type, pattern in patterns.items():
        matches = re.findall(pattern, logs, re.IGNORECASE | re.MULTILINE)
        if matches:
            errors[error_type] = matches[:3]  # Keep first 3 matches

    return errors

def save_logs_and_analysis() -> None:
    """Collect, analyze, and save logs."""
    os.makedirs('logs', exist_ok=True)

    print("📊 Collecting recent workflow logs...")
    failed_runs = get_recent_failed_runs(limit=10)

    summary = {
        'timestamp': datetime.utcnow().isoformat(),
        'total_runs_checked': len(failed_runs),
        'analysis': []
    }

    for run in failed_runs:
        print(f"  Processing run: {run['name']} #{run['number']}")

        logs = get_run_logs(run['number'])
        errors = extract_error_patterns(logs)

        analysis = {
            'run_name': run['name'],
            'run_number': run['number'],
            'conclusion': run.get('conclusion'),
            'created_at': run['createdAt'],
            'url': run['url'],
            'error_patterns': errors,
            'log_file': f"run-{run['number']}.log"
        }

        summary['analysis'].append(analysis)

        # Save individual run logs
        log_file = f"logs/run-{run['number']}.log"
        with open(log_file, 'w') as f:
            f.write(f"Run: {run['name']} #{run['number']}\n")
            f.write(f"URL: {run['url']}\n")
            f.write(f"Status: {run['conclusion']}\n")
            f.write("="*80 + "\n\n")
            f.write(logs)

    # Save analysis summary
    summary_file = f"logs/analysis-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Logs saved to logs/ directory")
    print(f"📋 Analysis summary: {summary_file}")

    # Print quick stats
    print("\n" + "="*60)
    print("Error Pattern Summary")
    print("="*60)

    error_counts = {}
    for item in summary['analysis']:
        for error_type, patterns in item.get('error_patterns', {}).items():
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

    for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {error_type.upper()}: {count} runs affected")

    print("="*60 + "\n")

if __name__ == '__main__':
    save_logs_and_analysis()
