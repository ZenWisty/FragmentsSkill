# -*- coding: utf-8 -*-
"""
ReviewHelperApp - Main application entry point.

Handles:
- Reading pending tasks from review_pending.json
- Showing notification cards for each task
- Processing complete/skip actions (from notification buttons OR in-app UI)
- Calling review_job_launch.py on complete
- Writing responses to review_response.json

On Android: runs as a foreground-like service via Kivy
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

# Detect Android
ANDROID = sys.platform.lower() == 'android'


class ReviewHelperApp:
    """
    Main application controller.
    Manages the lifecycle of review tasks.
    """

    def __init__(self):
        self.notification_handler = NotificationHandler()
        self.pending_tasks = []
        self.current_review = None
        self._intent_processed = False  # track if current launch intent was handled

    def run(self):
        """
        Main entry point. Process pending tasks and show notifications.
        """
        logger.info("ReviewHelperApp starting...")

        # Handle any intent actions from notification button clicks
        self._handle_intent_actions()

        # Read pending tasks
        self.pending_tasks = read_pending()
        logger.info(f"Found {len(self.pending_tasks)} pending tasks")

        if not self.pending_tasks:
            logger.info("No pending tasks, app will exit")
            self._exit_app()
            return

        # Show all notifications
        self._show_all_notifications()

        # Check if launched with a specific action (user tapped notification button)
        if not self._intent_processed:
            # Not launched via notification action - show the in-app UI
            if ANDROID:
                self._run_android_ui()
            else:
                self._run_interactive_loop()

    def _handle_intent_actions(self) -> bool:
        """
        Handle actions passed via Android Intent extras.
        When notification action button is clicked, Android launches the app
        with action and task_id as Intent extras.
        These arrive in sys.argv as: ['.', '-a', 'complete', '--task-id', 'uuid', ...]
        Returns True if an action was processed.
        """
        self._intent_processed = False

        if not ANDROID:
            # Desktop: parse --action and --task_id from command line
            action = None
            task_id = None
            for i, arg in enumerate(sys.argv):
                if arg == "--action" and i + 1 < len(sys.argv):
                    action = sys.argv[i + 1]
                elif arg == "--task_id" and i + 1 < len(sys.argv):
                    task_id = sys.argv[i + 1]
                elif arg in ("-a", "--action") and i + 1 < len(sys.argv):
                    action = sys.argv[i + 1]
                elif arg == "--task-id" and i + 1 < len(sys.argv):
                    task_id = sys.argv[i + 1]

            if action and task_id:
                logger.info(f"Processing intent: action={action}, task_id={task_id}")
                self._process_action(action, task_id)
                self._intent_processed = True
                return True
        else:
            # Android: parse Intent extras from sys.argv
            # Kivy/PythonActivity on Android passes Intent extras as special argv elements
            # Format can be like: ['.', '--action=complete', '--task-id=uuid', ...]
            action = None
            task_id = None

            for arg in sys.argv:
                if arg.startswith('--action='):
                    action = arg.split('=', 1)[1]
                elif arg.startswith('--task-id='):
                    task_id = arg.split('=', 1)[1]
                elif arg.startswith('--task_id='):
                    task_id = arg.split('=', 1)[1]
                elif arg == '-a' or arg == '--action':
                    continue  # handled above via split
                elif arg in ('complete', 'skip') and action is None:
                    action = arg

            if action and task_id:
                logger.info(f"Processing Android intent: action={action}, task_id={task_id}")
                self._process_action(action, task_id)
                self._intent_processed = True
                return True

        return False

    def _run_android_ui(self):
        """
        Run a minimal Android UI using Kivy.
        Shows pending tasks as a scrollable list with Complete/Skip buttons.
        This is shown when user taps the notification body (not action buttons).
        """
        try:
            from kivy.app import App
            from kivy.uix.boxlayout import BoxLayout
            from kivy.uix.button import Button
            from kivy.uix.label import Label
            from kivy.uix.scrollview import ScrollView
            from kivy.uix.gridlayout import GridLayout
            from kivy.uix.textinput import TextInput
            from kivy.core.window import Window
            from kivy.clock import Clock
        except ImportError:
            logger.warning("Kivy not available, falling back to interactive mode")
            self._run_interactive_loop()
            return

        class ReviewTaskWidget(BoxLayout):
            """Single task card with file info and action buttons."""
            def __init__(self, task_data, app_controller, **kwargs):
                super().__init__(**kwargs)
                self.orientation = 'vertical'
                self.size_hint_y = None
                self.height = '150dp'
                self.padding = 10
                self.spacing = 5

                self.task_data = task_data
                self.app_controller = app_controller

                filename = os.path.basename(task_data.get('path', 'unknown'))
                task_time = task_data.get('task_time', '')

                # File label
                self.add_widget(Label(
                    text=f"📄 {filename}",
                    font_size='16sp',
                    size_hint_y=0.5,
                    halign='left',
                    valign='middle'
                ))

                # Time label
                self.add_widget(Label(
                    text=f"⏰ {task_time}",
                    font_size='13sp',
                    size_hint_y=0.25,
                    halign='left',
                    color=(0.6, 0.6, 0.6, 1)
                ))

                # Button row
                btn_row = BoxLayout(size_hint_y=0.35, spacing=10)
                btn_complete = Button(
                    text='✅ 完成',
                    background_color=(0.2, 0.7, 0.3, 1),
                    on_press=lambda x: self._on_complete()
                )
                btn_skip = Button(
                    text='⏭️ 跳过',
                    background_color=(0.8, 0.5, 0.2, 1),
                    on_press=lambda x: self._on_skip()
                )
                btn_row.add_widget(btn_complete)
                btn_row.add_widget(btn_skip)
                self.add_widget(btn_row)

            def _on_complete(self):
                self.app_controller._do_complete(self.task_data)
                # Remove this widget from parent
                parent = self.parent
                if parent:
                    parent.remove_widget(self)

            def _on_skip(self):
                self.app_controller._do_skip(self.task_data)
                parent = self.parent
                if parent:
                    parent.remove_widget(self)

        class ReviewApp(App):
            """Kivy App displaying the review task list."""

            def __init__(self, app_controller, **kwargs):
                super().__init__(**kwargs)
                self.app_controller = app_controller

            def build(self):
                root = BoxLayout(orientation='vertical', padding=10, spacing=10)

                # Header
                header = BoxLayout(size_hint_y=0.08)
                header.add_widget(Label(
                    text='📋 复习任务',
                    font_size='20sp',
                    bold=True
                ))
                root.add_widget(header)

                # Task list (scrollable)
                scroll = ScrollView(size_hint_y=0.82, do_scroll_y=True)
                task_list = GridLayout(
                    cols=1,
                    size_hint_y=None,
                    spacing=10,
                    padding=10
                )
                task_list.bind(minimum_height=task_list.setter('height'))

                for task in self.app_controller.pending_tasks:
                    task_widget = ReviewTaskWidget(task, self.app_controller)
                    task_list.add_widget(task_widget)

                scroll.add_widget(task_list)
                root.add_widget(scroll)

                # Footer with refresh and clear-all
                footer = BoxLayout(size_hint_y=0.1, spacing=10)

                # Refresh button
                btn_refresh = Button(
                    text='🔄 刷新',
                    background_color=(0.3, 0.5, 0.7, 1),
                    on_press=lambda x: self._refresh()
                )

                # Exit button
                btn_exit = Button(
                    text='❌ 退出',
                    background_color=(0.5, 0.5, 0.5, 1),
                    on_press=lambda x: self._exit_app()
                )

                footer.add_widget(btn_refresh)
                footer.add_widget(btn_exit)
                root.add_widget(footer)

                return root

            def _refresh(self):
                """Reload pending tasks from file."""
                self.app_controller.pending_tasks = read_pending()
                # Rebuild the UI by restarting
                self.stop()
                self.app_controller._run_android_ui()

            def _exit_app(self):
                self.stop()

        logger.info("Starting Kivy UI...")
        app = ReviewApp(self)
        app.title = "ReviewHelperApp"
        try:
            app.run()
        except Exception as e:
            logger.error(f"Kivy UI error: {e}")
            self._run_interactive_loop()

    def _run_interactive_loop(self):
        """
        Interactive loop for non-Android or fallback.
        """
        print("\n=== ReviewHelperApp Interactive Mode ===")
        self._list_tasks()

        while True:
            print("\nCommands: complete <idx>, skip <idx>, list, refresh, exit")
            try:
                cmd = input("> ").strip()
            except EOFError:
                break

            if cmd == "exit":
                break
            elif cmd == "list" or cmd == "refresh":
                self._list_tasks()
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

    def _list_tasks(self):
        """List pending tasks."""
        print(f"\nPending tasks ({len(self.pending_tasks)}):")
        for i, task in enumerate(self.pending_tasks):
            filename = os.path.basename(task.get('path', 'unknown'))
            task_time = task.get('task_time', '')
            print(f"  [{i}] {filename}  ({task_time})")

    def _show_all_notifications(self):
        """Show notification cards for all pending tasks."""
        for task in self.pending_tasks:
            task_id = task.get("task_id", str(uuid.uuid4()))
            filename = os.path.basename(task.get("path", "unknown"))
            task_time = task.get("task_time", "")
            review_type = task.get("review_type", "simple")

            title = f"复习任务: {filename}"
            body = f"计划时间: {task_time}"

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
        # Find task data in pending
        task_data = None
        for t in self.pending_tasks:
            if t.get("task_id") == task_id:
                task_data = t
                break

        if not task_data:
            logger.warning(f"Task {task_id} not found in pending")
            return

        logger.info(f"Processing {action} for task {task_id}: {task_data.get('path')}")

        if action == "complete":
            self._do_complete(task_data)
        elif action == "skip":
            self._do_skip(task_data)

    def _process_complete(self, idx: int):
        """Process complete for a task by list index."""
        if 0 <= idx < len(self.pending_tasks):
            task = self.pending_tasks[idx]
            self._do_complete(task)

    def _process_skip(self, idx: int):
        """Process skip for a task by list index."""
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
            logger.info(f"review_job_launch.py output: {result.stdout.strip()}")
            if result.stderr:
                logger.warning(f"review_job_launch.py stderr: {result.stderr}")
        except Exception as e:
            logger.error(f"Failed to call review_job_launch.py: {e}")

        # Step 2: Write response
        write_response(task_id, "complete", review_type,
                      path=path, tag_content=tag_content,
                      action_script=action_script)
        logger.info(f"Response written: task_id={task_id} action=complete")

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

        # Step 1: Write response
        write_response(task_id, "skip", review_type,
                      path=path, tag_content=tag_content,
                      action_script=action_script)
        logger.info(f"Response written: task_id={task_id} action=skip")

        # Step 2: Remove from pending
        self.pending_tasks = [t for t in self.pending_tasks if t.get("task_id") != task_id]

        # Step 3: Cancel notification
        self.notification_handler.cancel_notification(task_id)

    def _exit_app(self):
        """Exit the application gracefully."""
        if ANDROID:
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                PythonActivity.finish()
            except Exception as e:
                logger.warning(f"Could not finish activity: {e}")
        sys.exit(0)


def main():
    """Entry point."""
    app = ReviewHelperApp()
    app.run()


if __name__ == "__main__":
    main()
