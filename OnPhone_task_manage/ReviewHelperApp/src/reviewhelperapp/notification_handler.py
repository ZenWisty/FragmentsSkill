# -*- coding: utf-8 -*-
"""
Notification handler for Android notification cards.
Uses pyjnius to access Android NotificationManager API directly.
"""
import os
import sys
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Detect Android environment
ANDROID = sys.platform.lower() == 'android'

# Cached Android classes
_AndroidClasses = {}


def _get_android_classes():
    """Lazily load and cache Android classes via pyjnius."""
    global _AndroidClasses
    if _AndroidClasses:
        return _AndroidClasses

    if not ANDROID:
        return _AndroidClasses

    try:
        from jnius import autoclass

        _AndroidClasses = {
            'Context': autoclass('android.content.Context'),
            'Intent': autoclass('android.content.Intent'),
            'PendingIntent': autoclass('android.app.PendingIntent'),
            'NotificationManager': autoclass('android.app.NotificationManager'),
            'NotificationChannel': autoclass('android.app.NotificationChannel'),
            'NotificationCompat': autoclass('androidx.core.app.NotificationCompat'),
            'NotificationCompat_Builder': None,  # set after Context known
            'R': autoclass('android.R'),
        }
        return _AndroidClasses
    except Exception as e:
        logger.warning(f"pyjnius not available: {e}")
        return _AndroidClasses


class NotificationHandler:
    """
    Handles creation and interaction of notification cards.
    On Android: uses NotificationCompat with Action buttons
    On other platforms: falls back to plyer
    """

    CHANNEL_ID = "review_helper_channel"
    CHANNEL_NAME = "Review Tasks"
    CHANNEL_DESC = "Obsidian task review notifications"

    def __init__(self):
        self._notification_manager = None
        self._notification_compat_builder_class = None
        self._android_classes = {}
        self._channel_created = False
        self._pending_intents = {}  # task_id -> pending_intent

        if ANDROID:
            self._android_classes = _get_android_classes()
            if self._android_classes.get('NotificationManager'):
                self._notification_manager = self._android_classes['NotificationManager']
                self._notification_compat_builder_class = self._android_classes['NotificationCompat']
                self._create_notification_channel()

    def _create_notification_channel(self) -> None:
        """Create notification channel on Android 8.0+ (API 26+)."""
        if not ANDROID or self._channel_created:
            return

        try:
            C = self._android_classes
            Context = C.get('Context')
            NotificationChannel = C.get('NotificationChannel')

            if not Context or not NotificationChannel:
                return

            # Get application context
            app_context = Context.getApplicationContext()

            # Create channel with HIGH importance for notification dots/actions
            channel = NotificationChannel(
                self.CHANNEL_ID,
                self.CHANNEL_NAME,
                NotificationChannel.IMPORTANCE_HIGH
            )
            channel.setDescription(self.CHANNEL_DESC)
            channel.enableLights(True)
            channel.enableVibration(True)

            # Register the channel with the system
            self._notification_manager.createNotificationChannel(channel)
            self._channel_created = True
            logger.info("Notification channel created successfully")
        except Exception as e:
            logger.warning(f"Could not create notification channel: {e}")

    def _get_drawable(self, drawable_name: str):
        """Get Android drawable resource ID by name via pyjnius."""
        try:
            if 'R' not in self._android_classes:
                from jnius import autoclass
                self._android_classes['R'] = autoclass('android.R')
            R = self._android_classes['R']
            drawable_class = R.drawable
            if hasattr(drawable_class, drawable_name):
                return getattr(drawable_class, drawable_name)
        except Exception as e:
            logger.debug(f"Could not get drawable {drawable_name}: {e}")
        return None

    def show_task_notification(self, task_id: str, title: str,
                                body: str, review_handler) -> None:
        """
        Show a notification card for a task.

        Args:
            task_id: Unique ID for this task
            title: Notification title
            body: Notification body text
            review_handler: SimpleReview instance (unused in Android impl, just for API compat)
        """
        if not ANDROID:
            self._show_plyer_fallback(title, body)
            return

        if not self._notification_manager or not self._notification_compat_builder_class:
            logger.warning("NotificationManager not available, falling back to plyer")
            self._show_plyer_fallback(title, body)
            return

        self._show_android_notification(task_id, title, body)

    def _show_android_notification(self, task_id: str, title: str, body: str) -> None:
        """Show notification using Android NotificationCompat with action buttons."""
        try:
            C = self._android_classes
            Context = C.get('Context')
            Intent = C.get('Intent')
            PendingIntent = C.get('PendingIntent')
            NotificationCompat = C.get('NotificationCompat')

            if not all([Context, Intent, PendingIntent, NotificationCompat]):
                logger.error("Missing required Android classes")
                return

            app_context = Context.getApplicationContext()

            # Get drawable resource IDs - use safe fallbacks
            R = self._android_classes.get('R')
            if R:
                try:
                    icon_complete = getattr(R.drawable, 'ic_menu_send', R.drawable.ic_dialog_info)
                    icon_skip = getattr(R.drawable, 'ic_menu_close_clear_cancel', R.drawable.ic_dialog_alert)
                except Exception:
                    icon_complete = R.drawable.ic_dialog_info
                    icon_skip = R.drawable.ic_dialog_alert
            else:
                icon_complete = self._get_drawable('ic_menu_send') or 0x01080003
                icon_skip = self._get_drawable('ic_menu_close_clear_cancel') or 0x01080014

            # Build the main notification
            # We need the Builder class - access via the compat class
            try:
                builder = NotificationCompat.Builder(app_context, self.CHANNEL_ID)
            except Exception as e:
                logger.error(f"Failed to create builder: {e}")
                return

            builder \
                .setSmallIcon(icon_complete) \
                .setContentTitle(title) \
                .setContentText(body) \
                .setPriority(NotificationCompat.PRIORITY_HIGH) \
                .setAutoCancel(True) \
                .setDefaults(NotificationCompat.DEFAULT_ALL)

            # Get the main Activity class for PendingIntents
            main_activity = self._get_main_activity_class()

            if main_activity:
                # ----- Action: Complete -----
                complete_intent = Intent(app_context, main_activity)
                complete_intent.putExtra("action", "complete")
                complete_intent.putExtra("task_id", task_id)
                complete_intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)

                complete_pending = PendingIntent.getActivity(
                    app_context,
                    hash("complete_" + task_id),
                    complete_intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
                )
                builder.addAction(icon_complete, "完成", complete_pending)

                # ----- Action: Skip -----
                skip_intent = Intent(app_context, main_activity)
                skip_intent.putExtra("action", "skip")
                skip_intent.putExtra("task_id", task_id)
                skip_intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)

                skip_pending = PendingIntent.getActivity(
                    app_context,
                    hash("skip_" + task_id),
                    skip_intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
                )
                builder.addAction(icon_skip, "跳过", skip_pending)

            # Use a unique notification ID per task (derived from task_id hash)
            notif_id = hash(task_id) & 0x7FFFFFFF  # ensure positive

            notification = builder.build()
            self._notification_manager.notify(notif_id, notification)
            logger.info(f"Notification shown for task {task_id} (id={notif_id})")

            # Store mapping for cancellation
            self._pending_intents[task_id] = notif_id

        except Exception as e:
            logger.error(f"Failed to show Android notification: {e}")
            self._show_plyer_fallback(title, body)

    def _show_plyer_fallback(self, title: str, body: str) -> None:
        """Fallback: print to console when Android APIs unavailable."""
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=body,
                app_name="ReviewHelperApp",
                timeout=60
            )
        except Exception:
            # Last resort: print
            print(f"[NOTIFICATION] {title}: {body}")

    def _get_main_activity_class(self):
        """Get the main Activity class for PendingIntent targets."""
        try:
            from jnius import autoclass
            return autoclass('org.kivy.android.PythonActivity')
        except Exception as e:
            logger.warning(f"Could not get PythonActivity: {e}")
            return None

    def cancel_notification(self, task_id: str) -> None:
        """Cancel a specific notification by task_id."""
        if not ANDROID or not self._notification_manager:
            return

        notif_id = self._pending_intents.get(task_id, hash(task_id) & 0x7FFFFFFF)
        try:
            self._notification_manager.cancel(notif_id)
            logger.info(f"Notification cancelled for task {task_id}")
            self._pending_intents.pop(task_id, None)
        except Exception as e:
            logger.warning(f"Failed to cancel notification: {e}")

    def cancel_all(self) -> None:
        """Cancel all notifications."""
        if not ANDROID or not self._notification_manager:
            return
        try:
            self._notification_manager.cancelAll()
            self._pending_intents.clear()
            logger.info("All notifications cancelled")
        except Exception as e:
            logger.warning(f"Failed to cancel all notifications: {e}")
