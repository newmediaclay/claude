#!/usr/bin/env python3
"""
Sales Pipeline Tracker - A simple CLI tool for managing sales prospects.

Usage:
    python pipeline.py add "Company Name" --value 10000 --stage contact --contact "John Doe"
    python pipeline.py list
    python pipeline.py list --stage proposal_sent
    python pipeline.py show 1
    python pipeline.py update 1 --stage proposal_sent --value 15000
    python pipeline.py note 1 "Follow up next Tuesday about pricing"
    python pipeline.py followup 1 "2024-02-15"
    python pipeline.py delete 1
    python pipeline.py summary
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# ============================================================================
# CONFIGURATION - Customize these values as needed
# ============================================================================

DATA_FILE = Path(__file__).parent / "data" / "deals.json"

# Sales pipeline stages - customize these to match your process
STAGES = [
    "contact",       # Initial contact/prospect identified
    "proposal_sent", # Proposal/quote sent
    "won",           # Deal closed successfully
    "lost",          # Deal lost
]

# Default stage for new deals
DEFAULT_STAGE = "contact"

# Currency symbol for display
CURRENCY = "$"

# ============================================================================
# DATA MANAGEMENT
# ============================================================================

def load_data() -> dict:
    """Load deals from the JSON file."""
    if not DATA_FILE.exists():
        return {"deals": [], "next_id": 1}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data: dict) -> None:
    """Save deals to the JSON file."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

def get_deal_by_id(data: dict, deal_id: int) -> Optional[dict]:
    """Find a deal by its ID."""
    for deal in data["deals"]:
        if deal["id"] == deal_id:
            return deal
    return None

# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def format_value(value: float) -> str:
    """Format a monetary value."""
    if value >= 1000:
        return f"{CURRENCY}{value:,.0f}"
    return f"{CURRENCY}{value:.2f}"

def format_date(date_str: Optional[str]) -> str:
    """Format a date string for display."""
    if not date_str:
        return "-"
    return date_str

def stage_indicator(stage: str) -> str:
    """Return a visual indicator for the stage."""
    indicators = {
        "contact": "○",
        "proposal_sent": "◕",
        "won": "✓",
        "lost": "✗",
    }
    return indicators.get(stage, "?")

def print_deal_row(deal: dict) -> None:
    """Print a single deal as a table row."""
    indicator = stage_indicator(deal["stage"])
    followup = deal.get("followup_date", "")
    if followup:
        followup_display = f" [Follow-up: {followup}]"
    else:
        followup_display = ""

    print(f"  {deal['id']:>3}  {indicator} {deal['stage']:<12}  "
          f"{format_value(deal['value']):>12}  {deal['name'][:30]:<30}"
          f"{followup_display}")

def print_deal_detail(deal: dict) -> None:
    """Print detailed view of a single deal."""
    print(f"\n{'='*60}")
    print(f"  Deal #{deal['id']}: {deal['name']}")
    print(f"{'='*60}")
    print(f"  Stage:       {stage_indicator(deal['stage'])} {deal['stage']}")
    print(f"  Value:       {format_value(deal['value'])}")
    print(f"  Contact:     {deal.get('contact', '-')}")
    print(f"  Email:       {deal.get('email', '-')}")
    print(f"  Phone:       {deal.get('phone', '-')}")
    print(f"  Follow-up:   {format_date(deal.get('followup_date'))}")
    print(f"  Created:     {deal['created_at'][:10]}")
    print(f"  Updated:     {deal['updated_at'][:10]}")

    if deal.get("notes"):
        print(f"\n  Notes:")
        print(f"  {'-'*56}")
        for note in deal["notes"]:
            print(f"  [{note['timestamp'][:10]}] {note['text']}")
    print()

# ============================================================================
# COMMANDS
# ============================================================================

def cmd_add(args) -> None:
    """Add a new deal to the pipeline."""
    data = load_data()

    deal = {
        "id": data["next_id"],
        "name": args.name,
        "value": args.value or 0,
        "stage": args.stage or DEFAULT_STAGE,
        "contact": args.contact or "",
        "email": args.email or "",
        "phone": args.phone or "",
        "followup_date": args.followup or "",
        "notes": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    data["deals"].append(deal)
    data["next_id"] += 1
    save_data(data)

    print(f"\n  ✓ Added deal #{deal['id']}: {deal['name']}")
    print(f"    Stage: {deal['stage']} | Value: {format_value(deal['value'])}\n")

def cmd_list(args) -> None:
    """List all deals, optionally filtered by stage."""
    data = load_data()
    deals = data["deals"]

    # Filter by stage if specified
    if args.stage:
        deals = [d for d in deals if d["stage"] == args.stage]

    # Filter out won/lost unless specifically requested
    if not args.all and not args.stage:
        deals = [d for d in deals if d["stage"] not in ["won", "lost"]]

    if not deals:
        print("\n  No deals found.\n")
        return

    # Sort by stage order, then by value descending
    stage_order = {s: i for i, s in enumerate(STAGES)}
    deals.sort(key=lambda d: (stage_order.get(d["stage"], 99), -d["value"]))

    print(f"\n  {'ID':>3}  {'Stage':<14}  {'Value':>12}  {'Company':<30}")
    print(f"  {'-'*3}  {'-'*14}  {'-'*12}  {'-'*30}")

    for deal in deals:
        print_deal_row(deal)

    total = sum(d["value"] for d in deals)
    print(f"\n  Total pipeline value: {format_value(total)} ({len(deals)} deals)\n")

def cmd_show(args) -> None:
    """Show detailed view of a specific deal."""
    data = load_data()
    deal = get_deal_by_id(data, args.id)

    if not deal:
        print(f"\n  Error: Deal #{args.id} not found.\n")
        return

    print_deal_detail(deal)

def cmd_update(args) -> None:
    """Update a deal's information."""
    data = load_data()
    deal = get_deal_by_id(data, args.id)

    if not deal:
        print(f"\n  Error: Deal #{args.id} not found.\n")
        return

    updates = []
    if args.name:
        deal["name"] = args.name
        updates.append(f"name → {args.name}")
    if args.value is not None:
        deal["value"] = args.value
        updates.append(f"value → {format_value(args.value)}")
    if args.stage:
        deal["stage"] = args.stage
        updates.append(f"stage → {args.stage}")
    if args.contact:
        deal["contact"] = args.contact
        updates.append(f"contact → {args.contact}")
    if args.email:
        deal["email"] = args.email
        updates.append(f"email → {args.email}")
    if args.phone:
        deal["phone"] = args.phone
        updates.append(f"phone → {args.phone}")
    if args.followup:
        deal["followup_date"] = args.followup
        updates.append(f"follow-up → {args.followup}")

    if updates:
        deal["updated_at"] = datetime.now().isoformat()
        save_data(data)
        print(f"\n  ✓ Updated deal #{args.id}:")
        for u in updates:
            print(f"    • {u}")
        print()
    else:
        print("\n  No updates specified.\n")

def cmd_note(args) -> None:
    """Add a note to a deal."""
    data = load_data()
    deal = get_deal_by_id(data, args.id)

    if not deal:
        print(f"\n  Error: Deal #{args.id} not found.\n")
        return

    note = {
        "text": args.text,
        "timestamp": datetime.now().isoformat(),
    }
    deal["notes"].append(note)
    deal["updated_at"] = datetime.now().isoformat()
    save_data(data)

    print(f"\n  ✓ Added note to deal #{args.id}: {deal['name']}\n")

def cmd_followup(args) -> None:
    """Set a follow-up date for a deal."""
    data = load_data()
    deal = get_deal_by_id(data, args.id)

    if not deal:
        print(f"\n  Error: Deal #{args.id} not found.\n")
        return

    deal["followup_date"] = args.date
    deal["updated_at"] = datetime.now().isoformat()
    save_data(data)

    print(f"\n  ✓ Set follow-up for deal #{args.id} ({deal['name']}) to {args.date}\n")

def cmd_delete(args) -> None:
    """Delete a deal from the pipeline."""
    data = load_data()
    deal = get_deal_by_id(data, args.id)

    if not deal:
        print(f"\n  Error: Deal #{args.id} not found.\n")
        return

    if not args.force:
        confirm = input(f"  Delete deal #{args.id}: {deal['name']}? [y/N] ")
        if confirm.lower() != 'y':
            print("  Cancelled.\n")
            return

    data["deals"] = [d for d in data["deals"] if d["id"] != args.id]
    save_data(data)

    print(f"\n  ✓ Deleted deal #{args.id}: {deal['name']}\n")

def cmd_summary(args) -> None:
    """Show a summary of the pipeline."""
    data = load_data()
    deals = data["deals"]

    if not deals:
        print("\n  No deals in pipeline.\n")
        return

    print(f"\n  {'='*50}")
    print(f"  PIPELINE SUMMARY")
    print(f"  {'='*50}\n")

    # Group by stage
    stage_stats = {}
    for stage in STAGES:
        stage_deals = [d for d in deals if d["stage"] == stage]
        if stage_deals:
            stage_stats[stage] = {
                "count": len(stage_deals),
                "value": sum(d["value"] for d in stage_deals),
            }

    # Display by stage
    for stage in STAGES:
        if stage in stage_stats:
            stats = stage_stats[stage]
            bar = "█" * min(stats["count"], 20)
            print(f"  {stage_indicator(stage)} {stage:<12}  "
                  f"{stats['count']:>3} deals  {format_value(stats['value']):>12}  {bar}")

    # Totals
    active_deals = [d for d in deals if d["stage"] not in ["won", "lost"]]
    won_deals = [d for d in deals if d["stage"] == "won"]

    print(f"\n  {'-'*50}")
    print(f"  Active pipeline:  {len(active_deals)} deals  "
          f"{format_value(sum(d['value'] for d in active_deals))}")
    print(f"  Won this period:  {len(won_deals)} deals  "
          f"{format_value(sum(d['value'] for d in won_deals))}")

    # Upcoming follow-ups
    today = datetime.now().strftime("%Y-%m-%d")
    upcoming = [d for d in active_deals if d.get("followup_date") and d["followup_date"] >= today]
    upcoming.sort(key=lambda d: d["followup_date"])

    if upcoming:
        print(f"\n  UPCOMING FOLLOW-UPS:")
        print(f"  {'-'*50}")
        for deal in upcoming[:5]:
            print(f"  {deal['followup_date']}  #{deal['id']} {deal['name'][:30]}")

    print()

def cmd_due(args) -> None:
    """Show deals with follow-ups due today or overdue."""
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")

    active_deals = [d for d in data["deals"] if d["stage"] not in ["won", "lost"]]
    due_deals = [d for d in active_deals
                 if d.get("followup_date") and d["followup_date"] <= today]
    due_deals.sort(key=lambda d: d["followup_date"])

    if not due_deals:
        print("\n  No follow-ups due today.\n")
        return

    print(f"\n  FOLLOW-UPS DUE")
    print(f"  {'-'*50}")
    for deal in due_deals:
        overdue = " (OVERDUE)" if deal["followup_date"] < today else ""
        print(f"  {deal['followup_date']}  #{deal['id']} {deal['name'][:30]}{overdue}")
    print()

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Sales Pipeline Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command
    p_add = subparsers.add_parser("add", help="Add a new deal")
    p_add.add_argument("name", help="Company or deal name")
    p_add.add_argument("-v", "--value", type=float, help="Deal value")
    p_add.add_argument("-s", "--stage", choices=STAGES, help="Pipeline stage")
    p_add.add_argument("-c", "--contact", help="Contact person name")
    p_add.add_argument("-e", "--email", help="Contact email")
    p_add.add_argument("-p", "--phone", help="Contact phone")
    p_add.add_argument("-f", "--followup", help="Follow-up date (YYYY-MM-DD)")
    p_add.set_defaults(func=cmd_add)

    # List command
    p_list = subparsers.add_parser("list", aliases=["ls"], help="List deals")
    p_list.add_argument("-s", "--stage", choices=STAGES, help="Filter by stage")
    p_list.add_argument("-a", "--all", action="store_true", help="Include won/lost deals")
    p_list.set_defaults(func=cmd_list)

    # Show command
    p_show = subparsers.add_parser("show", help="Show deal details")
    p_show.add_argument("id", type=int, help="Deal ID")
    p_show.set_defaults(func=cmd_show)

    # Update command
    p_update = subparsers.add_parser("update", help="Update a deal")
    p_update.add_argument("id", type=int, help="Deal ID")
    p_update.add_argument("-n", "--name", help="New name")
    p_update.add_argument("-v", "--value", type=float, help="New value")
    p_update.add_argument("-s", "--stage", choices=STAGES, help="New stage")
    p_update.add_argument("-c", "--contact", help="New contact")
    p_update.add_argument("-e", "--email", help="New email")
    p_update.add_argument("-p", "--phone", help="New phone")
    p_update.add_argument("-f", "--followup", help="New follow-up date")
    p_update.set_defaults(func=cmd_update)

    # Note command
    p_note = subparsers.add_parser("note", help="Add a note to a deal")
    p_note.add_argument("id", type=int, help="Deal ID")
    p_note.add_argument("text", help="Note text")
    p_note.set_defaults(func=cmd_note)

    # Follow-up command
    p_followup = subparsers.add_parser("followup", aliases=["fu"], help="Set follow-up date")
    p_followup.add_argument("id", type=int, help="Deal ID")
    p_followup.add_argument("date", help="Follow-up date (YYYY-MM-DD)")
    p_followup.set_defaults(func=cmd_followup)

    # Delete command
    p_delete = subparsers.add_parser("delete", aliases=["rm"], help="Delete a deal")
    p_delete.add_argument("id", type=int, help="Deal ID")
    p_delete.add_argument("-f", "--force", action="store_true", help="Skip confirmation")
    p_delete.set_defaults(func=cmd_delete)

    # Summary command
    p_summary = subparsers.add_parser("summary", aliases=["stats"], help="Show pipeline summary")
    p_summary.set_defaults(func=cmd_summary)

    # Due command
    p_due = subparsers.add_parser("due", help="Show follow-ups due today")
    p_due.set_defaults(func=cmd_due)

    args = parser.parse_args()

    if not args.command:
        # Default to list if no command given
        args.stage = None
        args.all = False
        cmd_list(args)
    else:
        args.func(args)

if __name__ == "__main__":
    main()
