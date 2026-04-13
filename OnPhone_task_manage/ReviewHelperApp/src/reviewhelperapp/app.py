# -*- coding: utf-8 -*-
"""
ReviewHelperApp - Main application entry point.

Handles:
- Reading pending tasks from review_pending.json
- Showing a simple task UI with Complete/Skip buttons
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

# Ensure the parent of "reviewhelperapp" package is on sys.path.
# This is needed because BeeWare's PythonActivity bootstrap may not include it.
_pkg_dir = os.path.dirname(__file__)  # directory containing this file (reviewhelperapp/)
_parent = os.path.dirname(_pkg_dir)  # parent (should contain reviewhelperapp/ as a package)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from reviewhelperapp.communication import (
    read_pending, write_response
)
from reviewhelperapp.notification_handler import NotificationHandler

# Logging to file
LOG_FILE = "/storage/emulated/0/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/docs/app.log"

def log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(f"{msg}\n")
    print(msg)

# Detect Android
ANDROID = sys.platform.lower() == 'android'

log(f"App starting... platform={sys.platform}, ANDROID={ANDROID}")


class ReviewHelperApp:
    """
    Main application controller.
    Manages the lifecycle of review tasks.
    """

    def __init__(self):
        self.notification_handler = NotificationHandler()
        self.pending_tasks = []
        self.current_review = None
        self._intent_processed = False

        log(f"ReviewHelperApp init: pending_tasks={len(self.pending_tasks)}")

    def run(self):
        """Main entry point."""
        log("App.run() called")

        # Handle any intent actions from notification button clicks
        self._handle_intent_actions()

        # Read pending tasks
        self.pending_tasks = read_pending()
        log(f"Read {len(self.pending_tasks)} pending tasks")

        if not self.pending_tasks:
            log("No pending tasks, showing empty screen")
            self._show_empty_ui()
            return

        # Show all notifications (for future use, currently pyjnius unavailable)
        for task in self.pending_tasks:
            task_id = task.get("task_id", str(uuid.uuid4()))
            filename = os.path.basename(task.get("path", "unknown"))
            task_time = task.get("task_time", "")
            self.notification_handler.show_task_notification(
                task_id,
                f"复习任务: {filename}",
                f"计划时间: {task_time}",
                None
            )

        # Show the task UI
        if ANDROID:
            log("Running Android Kivy UI")
            self._run_android_ui()
        else:
            log("Running interactive loop")
            self._run_interactive_loop()

    def _show_empty_ui(self):
        """Show UI when no tasks pending."""
        if ANDROID:
            self._show_simple_ui([("无待处理任务", "")])
        else:
            print("No pending tasks")

    def _handle_intent_actions(self) -> bool:
        """Handle actions passed via Android Intent extras."""
        self._intent_processed = False

        if not ANDROID:
            for i, arg in enumerate(sys.argv):
                if arg == "--action" and i + 1 < len(sys.argv):
                    action = sys.argv[i + 1]
                elif arg == "--task_id" and i + 1 < len(sys.argv):
                    task_id = sys.argv[i + 1]
            if action and task_id:
                self._process_action(action, task_id)
                self._intent_processed = True
                return True
        else:
            for arg in sys.argv:
                if arg.startswith('--action='):
                    action = arg.split('=', 1)[1]
                elif arg.startswith('--task-id='):
                    task_id = arg.split('=', 1)[1]
                elif arg.startswith('--task_id='):
                    task_id = arg.split('=', 1)[1]
            if action and task_id:
                log(f"Processing intent: action={action}, task_id={task_id}")
                self._process_action(action, task_id)
                self._intent_processed = True
                return True
        return False

    def _run_android_ui(self):
        """Show Android Kivy UI with pending tasks."""
        log("_run_android_ui() called")
        try:
            from kivy.app import App
            from kivy.uix.boxlayout import BoxLayout
            from kivy.uix.button import Button
            from kivy.uix.label import Label
            from kivy.uix.scrollview import ScrollView
            from kivy.uix.gridlayout import GridLayout
            from kivy.core.window import Window
            log("Kivy imports OK")
        except ImportError as e:
            log(f"Kivy ImportError: {e}")
            self._run_interactive_loop()
            return
        except Exception as e:
            log(f"Kivy unexpected error: {e}")
            self._run_interactive_loop()
            return

        # Configure window
        try:
            Window.clearcolor = (0.1, 0.1, 0.1, 1)
            log("Window configured")
        except Exception as e:
            log(f"Window config error: {e}")

        class TaskScreen(BoxLayout):
            def __init__(self, app_controller, **kwargs):
                super().__init__(**kwargs)
                self.app_controller = app_controller
                self.orientation = 'vertical'
                self.padding = 20
                self.spacing = 10
                log(f"TaskScreen init: {len(app_controller.pending_tasks)} tasks")
                self._build_ui()

            def _build_ui(self):
                self.clear_widgets()

                # Title
                title = Label(
                    text='📋 复习任务',
                    font_size='24sp',
                    size_hint_y=0.1,
                    color=(1, 1, 1, 1)
                )
                self.add_widget(title)

                # Task list
                scroll = ScrollView(size_hint_y=0.8, do_scroll_y=True)
                list_container = GridLayout(
                    cols=1,
                    size_hint_y=None,
                    spacing=10,
                    padding=10
                )
                list_container.bind(minimum_height=list_container.setter('height'))

                for task in self.app_controller.pending_tasks:
                    task_card = self._make_task_card(task)
                    list_container.add_widget(task_card)

                scroll.add_widget(list_container)
                self.add_widget(scroll)

                # Exit button
                exit_btn = Button(
                    text='❌ 退出',
                    size_hint_y=0.1,
                    background_color=(0.5, 0.5, 0.5, 1)
                )
                exit_btn.bind(on_press=lambda x: self._exit())
                self.add_widget(exit_btn)

            def _make_task_card(self, task):
                card = BoxLayout(orientation='vertical', size_hint_y=None, height='160dp',
                                 padding=10, spacing=5)
                card.add_widget(Label(
                    text=f"📄 {os.path.basename(task.get('path', 'unknown'))}",
                    font_size='18sp',
                    color=(1, 1, 1, 1),
                    halign='left'
                ))
                card.add_widget(Label(
                    text=f"⏰ {task.get('task_time', '')}",
                    font_size='14sp',
                    color=(0.7, 0.7, 0.7, 1)
                ))

                btn_row = BoxLayout(size_hint_y=0.4, spacing=10)
                complete_btn = Button(
                    text='✅ 完成',
                    background_color=(0.2, 0.7, 0.3, 1)
                )
                complete_btn.bind(on_press=lambda x, t=task: self._on_complete(t))
                skip_btn = Button(
                    text='⏭️ 跳过',
                    background_color=(0.8, 0.5, 0.2, 1)
                )
                skip_btn.bind(on_press=lambda x, t=task: self._on_skip(t))
                btn_row.add_widget(complete_btn)
                btn_row.add_widget(skip_btn)
                card.add_widget(btn_row)
                return card

            def _on_complete(self, task):
                log(f"_on_complete: {task.get('task_id')}")
                self.app_controller._do_complete(task)

            def _on_skip(self, task):
                log(f"_on_skip: {task.get('task_id')}")
                self.app_controller._do_skip(task)

            def _exit(self):
                log("User pressed exit")
                App.get_running_app().stop()

        class ReviewApp(App):
            def build(self):
                log("ReviewApp.build() called")
                screen = TaskScreen(self.controller)
                log("TaskScreen built OK")
                return screen

        try:
            log("Creating ReviewApp instance")
            app = ReviewApp()
            app.controller = self
            log("Calling app.run()")
            app.run()
            log("app.run() finished")
        except Exception as e:
            log(f"ReviewApp error: {e}")
            import traceback
            log(traceback.format_exc())

    def _show_simple_ui(self, tasks):
        """Show a simple non-Kivy UI using Android widget via pyjnius."""
        # Fallback to printing to log - Kivy UI is the primary
        for title, time in tasks:
            log(f"[TASK] {title} | {time}")

    def _run_interactive_loop(self):
        """Interactive loop for non-Android."""
        print("\n=== ReviewHelperApp Interactive Mode ===")
        self._list_tasks()

        while True:
            print("\nCommands: complete <idx>, skip <idx>, list, exit")
            try:
                cmd = input("> ").strip()
            except EOFError:
                break

            if cmd == "exit":
                break
            elif cmd in ("list", "refresh"):
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
        print(f"\nPending tasks ({len(self.pending_tasks)}):")
        for i, task in enumerate(self.pending_tasks):
            filename = os.path.basename(task.get('path', 'unknown'))
            task_time = task.get('task_time', '')
            print(f"  [{i}] {filename}  ({task_time})")

    def _process_action(self, action: str, task_id: str):
        """Process a complete or skip action."""
        task_data = None
        for t in self.pending_tasks:
            if t.get("task_id") == task_id:
                task_data = t
                break
        if not task_data:
            log(f"Task {task_id} not found in pending")
            return
        if action == "complete":
            self._do_complete(task_data)
        elif action == "skip":
            self._do_skip(task_data)

    def _process_complete(self, idx: int):
        if 0 <= idx < len(self.pending_tasks):
            self._do_complete(self.pending_tasks[idx])

    def _process_skip(self, idx: int):
        if 0 <= idx < len(self.pending_tasks):
            self._do_skip(self.pending_tasks[idx])

    def _do_complete(self, task_data: Dict):
        task_id = task_data.get("task_id")
        path = task_data.get("path")
        tag_content = task_data.get("tag_content")
        action_script = task_data.get("action",
            "/storage/emulated/0/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/scripts/review_job_launch.py")
        review_type = task_data.get("review_type", "simple")

        log(f"_do_complete: {path}")

        try:
            result = subprocess.run(
                ["python3", action_script, path, tag_content],
                capture_output=True, text=True, timeout=30
            )
            log(f"review_job_launch output: {result.stdout.strip()}")
        except Exception as e:
            log(f"review_job_launch error: {e}")

        write_response(task_id, "complete", review_type,
                      path=path, tag_content=tag_content,
                      action_script=action_script)
        log(f"Response written: complete for {task_id}")

        self.pending_tasks = [t for t in self.pending_tasks if t.get("task_id") != task_id]
        self.notification_handler.cancel_notification(task_id)

    def _do_skip(self, task_data: Dict):
        task_id = task_data.get("task_id")
        path = task_data.get("path")
        tag_content = task_data.get("tag_content")
        action_script = task_data.get("action",
            "/storage/emulated/0/MyObsidianVaults/scripts_db/FragmentsSkill/OnPhone_task_manage/scripts/review_job_launch.py")
        review_type = task_data.get("review_type", "simple")

        log(f"_do_skip: {path}")

        write_response(task_id, "skip", review_type,
                      path=path, tag_content=tag_content,
                      action_script=action_script)
        log(f"Response written: skip for {task_id}")

        self.pending_tasks = [t for t in self.pending_tasks if t.get("task_id") != task_id]
        self.notification_handler.cancel_notification(task_id)


def main():
    """Entry point."""
    from datetime import datetime
    # Clear log on startup
    try:
        with open(LOG_FILE, 'w') as f:
            f.write(f"App started at {datetime.now().isoformat()}\n")
    except Exception as e:
        pass  # Cannot write log, continue anyway
    app = ReviewHelperApp()
    app.run()


if __name__ == "__main__":
    main()
