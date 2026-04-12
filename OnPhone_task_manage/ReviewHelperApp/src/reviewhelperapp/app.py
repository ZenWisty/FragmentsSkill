# -*- coding: utf-8 -*-
"""
ReviewHelperApp - Main application entry point.

Handles:
- Reading pending tasks from review_pending.json
- Showing notification cards for each task
- Processing complete/skip actions
- Calling review_job_launch.py on complete
- Writing responses to review_response.json
"""
import os
import sys
import logging
import subprocess
import uuid
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from reviewhelperapp.communication import (
    read_pending, remove_pending_task, read_pending_by_id,
    write_response, read_and_clear_response
)
from reviewhelperapp.notification_handler import NotificationHandler
from reviewhelperapp.review_interface import get_review_handler

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Paths
SCRIPT_DIR = "/storage/emulated/0/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/scripts"
REVIEW_LAUNCH_SCRIPT = os.path.join(SCRIPT_DIR, "review_job_launch.py")


class ReviewHelperApp:
    """
    Main application controller.
    Manages the lifecycle of review tasks.
    """

    def __init__(self):
        self.notification_handler = NotificationHandler()
        self.pending_tasks = []
        self.current_review = None

    def run(self):
        """
        Main entry point. Process pending tasks and show notifications.
        This is called when the app starts (from am start by monitor).
        """
        logger.info("ReviewHelperApp starting...")

        # Handle any intent actions that were passed at startup
        self._handle_intent_actions()

        # Read pending tasks
        self.pending_tasks = read_pending()
        logger.info(f"Found {len(self.pending_tasks)} pending tasks")

        if not self.pending_tasks:
            logger.info("No pending tasks, app will exit")
            return

        # Show notification for each task
        self._show_all_notifications()

        # Now wait for user interactions
        # In a real implementation, this would be event-driven
        # For now, the app stays alive to handle notification button callbacks
        logger.info("App is running, waiting for user interactions...")
        logger.info("Press Ctrl+C to exit (all notifications will remain)")

        # In Android, the app runs as a service waiting for notification callbacks
        # For testing purposes, we provide a simple input loop
        self._run_interactive_loop()

    def _run_interactive_loop(self):
        """
        Interactive loop for testing / manual operation.
        In production Android, this would be event-driven via notification callbacks.
        """
        print("\n=== ReviewHelperApp Interactive Mode ===")
        print("Pending tasks:")
        for i, task in enumerate(self.pending_tasks):
            print(f"  [{i}] {os.path.basename(task.get('path', 'unknown'))}")

        while True:
            print("\nCommands: complete <idx>, skip <idx>, list, exit")
            try:
                cmd = input("> ").strip()
            except EOFError:
                break

            if cmd == "exit":
                break
            elif cmd == "list":
                for i, task in enumerate(self.pending_tasks):
                    print(f"  [{i}] {os.path.basename(task.get('path', 'unknown'))}")
            elif cmd.startswith("complete "):
                try:
                    idx = int(cmd.split()[1])
                    if 0 <= idx < len(self.pending_tasks):
                        self._process_complete(idx)
                    else:
                        print("Invalid index")
                except (ValueError, IndexError):
                    print("Invalid command")
            elif cmd.startswith("skip "):
                try:
                    idx = int(cmd.split()[1])
                    if 0 <= idx < len(self.pending_tasks):
                        self._process_skip(idx)
                    else:
                        print("Invalid index")
                except (ValueError, IndexError):
                    print("Invalid command")

        print("ReviewHelperApp exiting...")

    def _handle_intent_actions(self):
        """
        Handle actions passed via command line arguments (from am start intent extras).
        Format: app.py --action complete --task_id <uuid>
        """
        action = None
        task_id = None

        # Parse command line args (passed via am start -e extra)
        args = sys.argv
        for i, arg in enumerate(args):
            if arg == "--action" and i + 1 < len(args):
                action = args[i + 1]
            elif arg == "--task_id" and i + 1 < len(args):
                task_id = args[i + 1]

        if action and task_id:
            logger.info(f"Processing intent action: {action} for task_id: {task_id}")
            self._process_action(action, task_id)

    def _show_all_notifications(self):
        """Show notification cards for all pending tasks."""
        for task in self.pending_tasks:
            task_id = task.get("task_id", str(uuid.uuid4()))
            filename = os.path.basename(task.get("path", "unknown"))
            task_time = task.get("task_time", "")
            review_type = task.get("review_type", "simple")

            title = f"复习任务: {filename}"
            body = f"计划时间: {task_time}"

            # Get the appropriate review handler for display content
            handler = get_review_handler(review_type)
            handler.show(task)

            self.notification_handler.show_task_notification(
                task_id, title, body, handler
            )

    def _process_action(self, action: str, task_id: str):
        """
        Process a complete or skip action for a specific task.
        Called when user clicks notification action button.
        """
        # Find task data
        task_data = None
        for t in self.pending_tasks:
            if t.get("task_id") == task_id:
                task_data = t
                break

        if not task_data:
            logger.warning(f"Task {task_id} not found in pending")
            return

        if action == "complete":
            self._do_complete(task_data)
        elif action == "skip":
            self._do_skip(task_data)

    def _process_complete(self, idx: int):
        """Process complete for a task by index (interactive mode)."""
        if 0 <= idx < len(self.pending_tasks):
            task = self.pending_tasks[idx]
            self._do_complete(task)

    def _process_skip(self, idx: int):
        """Process skip for a task by index (interactive mode)."""
        if 0 <= idx < len(self.pending_tasks):
            task = self.pending_tasks[idx]
            self._do_skip(task)

    def _do_complete(self, task_data: Dict):
        """
        Execute the complete action:
        1. Call review_job_launch.py to append timestamp
        2. Write response to review_response.json
        3. Remove from pending
        4. Cancel notification
        """
        task_id = task_data.get("task_id")
        path = task_data.get("path")
        tag_content = task_data.get("tag_content")
        action_script = task_data.get("action", REVIEW_LAUNCH_SCRIPT)
        review_type = task_data.get("review_type", "simple")

        logger.info(f"Completing task: {path}")

        # Step 1: Call review_job_launch.py to append timestamp
        try:
            result = subprocess.run(
                ["python3", action_script, path, tag_content],
                capture_output=True,
                text=True,
                timeout=30
            )
            logger.info(f"review_job_launch.py output: {result.stdout}")
            if result.stderr:
                logger.warning(f"review_job_launch.py stderr: {result.stderr}")
        except Exception as e:
            logger.error(f"Failed to call review_job_launch.py: {e}")

        # Step 2: Write response (with path/tag_content for monitor matching)
        write_response(task_id, "complete", review_type,
                      path=path, tag_content=tag_content,
                      action_script=action_script)
        logger.info(f"Response written for task {task_id}: complete")

        # Step 3: Remove from pending
        self.pending_tasks = [t for t in self.pending_tasks if t.get("task_id") != task_id]

        # Step 4: Cancel notification
        self.notification_handler.cancel_notification(task_id)

    def _do_skip(self, task_data: Dict):
        """
        Execute the skip action:
        1. Write response to review_response.json
        2. Remove from pending
        3. Cancel notification
        """
        task_id = task_data.get("task_id")
        path = task_data.get("path")
        tag_content = task_data.get("tag_content")
        action_script = task_data.get("action", REVIEW_LAUNCH_SCRIPT)
        review_type = task_data.get("review_type", "simple")

        logger.info(f"Skipping task: {path}")

        # Step 1: Write response (with path/tag_content for monitor matching)
        write_response(task_id, "skip", review_type,
                      path=path, tag_content=tag_content,
                      action_script=action_script)
        logger.info(f"Response written for task {task_id}: skip")

        # Step 2: Remove from pending
        self.pending_tasks = [t for t in self.pending_tasks if t.get("task_id") != task_id]

        # Step 3: Cancel notification
        self.notification_handler.cancel_notification(task_id)


def main():
    """Entry point."""
    app = ReviewHelperApp()
    app.run()


if __name__ == "__main__":
    main()
