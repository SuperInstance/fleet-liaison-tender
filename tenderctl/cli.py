"""tenderctl CLI — Fleet Liaison Tender control interface."""

import sys
import json
import argparse
from typing import Dict, List

from .github_client import GitHubClient
from .bottles import Bottle, read_bottle
from .compression import MessageCompressor
from .priority import PriorityTranslator
from .state import StateManager


class TenderCtl:
    """Main CLI controller for tenderctl."""

    def __init__(self, token: str = None):
        self.github = GitHubClient(token)
        self.compressor = MessageCompressor()
        self.translator = PriorityTranslator()
        self.state = StateManager()

    def scan(self, vessels: List[str] = None) -> dict:
        """Scan vessels for new bottles."""
        if vessels is None:
            vessels = self.github.list_vessels()

        results = {
            "scanned_vessels": len(vessels),
            "bottles_found": [],
            "summary": {},
        }

        for vessel in vessels:
            bottles = self.github.scan_bottles("SuperInstance", vessel)
            for bottle_info in bottles:
                try:
                    content = self.github.get_file_content(
                        "SuperInstance", vessel, bottle_info["path"]
                    )
                    bottle = read_bottle(content)
                    if bottle:
                        bottle_id = f"{vessel}/{bottle_info['name']}"
                        self.state.add_bottle(bottle_id, vessel, bottle.to_dict())
                        results["bottles_found"].append({
                            "id": bottle_id,
                            "vessel": vessel,
                            "type": bottle.type,
                            "priority": bottle.priority,
                            "path": bottle_info["path"],
                        })
                except Exception as e:
                    results["summary"][vessel] = f"error: {str(e)}"

        results["total_bottles"] = len(results["bottles_found"])
        return results

    def deliver(self, target_vessel: str = None) -> dict:
        """Compress and forward messages to target vessels."""
        status = self.state.get_all_status()
        results = {
            "deliveries": [],
            "skipped": [],
            "summary": {},
        }

        for vessel_id, vessel_status in status.get("vessels", {}).items():
            if target_vessel and vessel_id != target_vessel:
                continue

            pending_count = vessel_status.get("pending", 0)
            if pending_count == 0:
                results["skipped"].append({
                    "vessel": vessel_id,
                    "reason": "no pending messages",
                })
                continue

            # Get pending bottles for this vessel
            vessel_bottles = [
                (bid, b) for bid, b in self.state.state["bottles"].items()
                if b["vessel"] == vessel_id and b["status"] == "pending"
            ]

            delivered = 0
            for bottle_id, bottle_state in vessel_bottles:
                # Compress message
                compressed = self.compressor.compress({
                    "type": bottle_state.get("type", "context"),
                    "payload": bottle_state.get("payload", {}),
                    "priority": bottle_state.get("priority", "medium"),
                })

                # Check if should forward based on priority
                if not self.translator.should_forward(
                    bottle_state.get("priority", "medium")
                ):
                    results["skipped"].append({
                        "vessel": vessel_id,
                        "bottle": bottle_id,
                        "reason": "priority filtered (low)",
                    })
                    self.state.update_bottle_status(bottle_id, "acked")
                    continue

                # Update status to delivered
                self.state.update_bottle_status(bottle_id, "delivered")
                delivered += 1

                results["deliveries"].append({
                    "vessel": vessel_id,
                    "bottle": bottle_id,
                    "compressed_message": compressed,
                })

            results["summary"][vessel_id] = {
                "delivered": delivered,
                "skipped": pending_count - delivered,
            }

        results["total_delivered"] = len(results["deliveries"])
        results["total_skipped"] = len(results["skipped"])
        return results

    def status(self, vessel: str = None) -> dict:
        """Show pending/delivered/acked counts."""
        if vessel:
            return self.state.get_vessel_status(vessel)
        return self.state.get_all_status()

    def ack(self, vessel: str, file: str) -> dict:
        """Mark a bottle as acknowledged."""
        bottle_id = f"{vessel}/{file}"
        bottle = self.state.state["bottles"].get(bottle_id)

        if not bottle:
            return {
                "error": f"Bottle {bottle_id} not found",
                "success": False,
            }

        self.state.update_bottle_status(bottle_id, "acked")
        return {
            "success": True,
            "bottle": bottle_id,
            "status": "acked",
            "previous_status": bottle["status"],
        }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="tenderctl — Fleet Liaison Tender control interface"
    )
    parser.add_argument(
        "--output", "-o",
        choices=["json", "pretty"],
        default="json",
        help="Output format (default: json)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan vessels for new bottles")
    scan_parser.add_argument(
        "--vessels", "-v",
        nargs="+",
        help="Specific vessels to scan (default: all)",
    )

    # deliver command
    deliver_parser = subparsers.add_parser("deliver", help="Deliver messages to vessels")
    deliver_parser.add_argument(
        "--vessel", "-t",
        help="Target vessel (default: all)",
    )

    # status command
    status_parser = subparsers.add_parser("status", help="Show message status")
    status_parser.add_argument(
        "--vessel", "-v",
        help="Specific vessel (default: all)",
    )

    # ack command
    ack_parser = subparsers.add_parser("ack", help="Acknowledge a bottle")
    ack_parser.add_argument("vessel", help="Vessel name")
    ack_parser.add_argument("file", help="Bottle filename")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        ctl = TenderCtl()
        result = None

        if args.command == "scan":
            result = ctl.scan(vessels=args.vessels)
        elif args.command == "deliver":
            result = ctl.deliver(target_vessel=getattr(args, "vessel", None))
        elif args.command == "status":
            result = ctl.status(vessel=getattr(args, "vessel", None))
        elif args.command == "ack":
            result = ctl.ack(args.vessel, args.file)

        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps(result, indent=2))

    except Exception as e:
        error_result = {"error": str(e), "success": False}
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
