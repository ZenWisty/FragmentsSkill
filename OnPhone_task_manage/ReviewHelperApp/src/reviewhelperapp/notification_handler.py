# -*- coding: utf-8 -*-
"""
Notification handler for Android notification cards.
Supports action buttons via pyjnius (Android API).
Falls back to plyer for basic notifications.
"""
import os
import sys
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Detect Android environment
ANDROID = sys.platform.lower() == 'android'


def _get_android_notification_manager():
    """
    Get Android NotificationManager via pyjnius.
    Returns (notification_manager, notification_builder_class) or (None, None) if unavailable.
    """
    if not ANDROID:
        return None, None
    try:
        from jnius import autoclass
        Context = autoclass('android.content.Context')
        NotificationManager = autoclass('android.app.NotificationManager')
        NotificationCompat = autoclass('androidx.core.app.NotificationCompat')
        PendingIntent = autoclass('android.app.PendingIntent')
        Intent = autoclass('android.content.Intent')
        return NotificationManager, NotificationCompat
    except Exception as e:
        logger.warning(f"pyjnius not available: {e}")
        return None, None


class NotificationHandler:
    """
    Handles creation and interaction of notification cards.
    On Android: uses NotificationCompat with Action buttons
    On other platforms: uses plyer (basic notifications)
    """

    CHANNEL_ID = "review_helper_channel"
    CHANNEL_NAME = "Review Tasks"

    def __init__(self):
        self._notification_manager = None
        self._notification_compat_class = None
        self._pending_intents = {}  # task_id -> pending_intent

        if ANDROID:
            self._notification_manager, self._notification_compat_class = \
                _get_android_notification_manager()
            if self._notification_manager:
                self._create_notification_channel()

    def _create_notification_channel(self) -> None:
        """Create notification channel on Android 8.0+"""
        try:
            from jnius import autoclass
            if not ANDROID:
                return
            Context = autoclass('android.content.Context')
            channel = autoclass('android.app.NotificationChannel')(
                self.CHANNEL_ID,
                self.CHANNEL_NAME,
                self._notification_manager.IMPORTANCE_HIGH
            )
            # Configure channel...
            app_context = Context.getApplicationContext()
            # Channel registration requires app context, skip if not available
        except Exception as e:
            logger.warning(f"Could not create notification channel: {e}")

    def show_task_notification(self, task_id: str, title: str,
                                body: str, review_handler) -> None:
        """
        Show a notification card for a task.

        Args:
            task_id: Unique ID for this task
            title: Notification title (e.g., filename)
            body: Notification body text
            review_handler: SimpleReview instance for this task
        """
        if ANDROID and self._notification_manager and self._notification_compat_class:
            self._show_android_notification(task_id, title, body, review_handler)
        else:
            self._show_plyer_notification(task_id, title, body)

    def _show_android_notification(self, task_id: str, title: str,
                                   body: str, review_handler) -> None:
        """Show notification using Android NotificationCompat with action buttons."""
        try:
            from jnius import autoclass
            Context = autoclass('android.content.Context')
            Intent = autoclass('android.content.Intent')
            PendingIntent = autoclass('android.app.PendingIntent')

            # Build the notification
            builder = self._notification_compat_class.Builder(
                Context.getApplicationContext(), self.CHANNEL_ID) \
                .setSmallIcon(android.R.drawable.ic_dialog_info) \
                .setContentTitle(title) \
                .setContentText(body) \
                .setPriority(self._notification_compat_class.PRIORITY_HIGH) \
                .setAutoCancel(True)

            # Add Complete action
            complete_intent = Intent(Context.getApplicationContext(),
                                     self._get_main_activity_class())
            complete_intent.putExtra("action", "complete")
            complete_intent.putExtra("task_id", task_id)
            complete_intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)

            complete_pending = PendingIntent.getActivity(
                Context.getApplicationContext(), hash("complete" + task_id),
                complete_intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            )
            builder.addAction(android.R.drawable.ic_menu_send, "完成", complete_pending)

            # Add Skip action
            skip_intent = Intent(Context.getApplicationContext(),
                                 self._get_main_activity_class())
            skip_intent.putExtra("action", "skip")
            skip_intent.putExtra("task_id", task_id)
            skip_intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)

            skip_pending = PendingIntent.getActivity(
                Context.getApplicationContext(), hash("skip" + task_id),
                skip_intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            )
            builder.addAction(android.R.drawable.ic_menu_close_clear_cancel, "跳过", skip_pending)

            notification = builder.build()
            self._notification_manager.notify(
                hash(task_id),  # notification ID
                notification
            )
            logger.info(f"Notification shown for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to show Android notification: {e}")
            self._show_plyer_notification(task_id, title, body)

    def _show_plyer_notification(self, task_id: str, title: str, body: str) -> None:
        """Fallback: show basic notification using plyer."""
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=body,
                app_name="ReviewHelperApp",
                timeout=60  # notification stays for 60 seconds
            )
            logger.info(f"Plyer notification shown for task {task_id}")
        except Exception as e:
            logger.warning(f"plyer notification failed: {e}")
            # Last resort: just print to console
            print(f"[NOTIFICATION] {title}: {body}")

    def _get_main_activity_class(self):
        """Get the main Activity class for intent handling."""
        try:
            from jnius import autoclass
            # This would be the PythonActivity or custom Activity
            return autoclass('org.kivy.android.PythonActivity')
        except:
            return None

    def cancel_notification(self, task_id: str) -> None:
        """Cancel a notification when task is completed or skipped."""
        if ANDROID and self._notification_manager:
            try:
                self._notification_manager.cancel(hash(task_id))
                logger.info(f"Notification cancelled for task {task_id}")
            except Exception as e:
                logger.warning(f"Failed to cancel notification: {e}")

    def cancel_all(self) -> None:
        """Cancel all notifications."""
        if ANDROID and self._notification_manager:
            try:
                self._notification_manager.cancelAll()
            except Exception as e:
                logger.warning(f"Failed to cancel all notifications: {e}")
