# -*- coding: utf-8 -*-
"""
Simple Review - minimum viable implementation.
Shows file path and allows Complete/Skip.
"""
import os
from typing import Dict, Any
from reviewhelperapp.review_interface import ReviewInterface, register_review_type

# Register this review type
register_review_type("simple", type('SimpleReview', (ReviewInterface,), {}))


class SimpleReview(ReviewInterface):
    """
    Simple review: just display file info, let user confirm complete or skip.
    Used as the default review type and fallback.
    """

    def __init__(self):
        self._task_data: Dict = {}
        self._result: Dict[str, Any] = {}
        self._current_file_path: str = ""
        self._current_tag_content: str = ""

    def show(self, task_data: Dict) -> None:
        """
        Store task data and display the file being reviewed.
        In notification-based UI, this shows the notification.
        For dialog UI, this would display the complete UI.
        """
        self._task_data = task_data
        self._current_file_path = task_data.get("path", "")
        self._current_tag_content = task_data.get("tag_content", "")

        # Build display info
        filename = os.path.basename(self._current_file_path)
        self._display_info = {
            "filename": filename,
            "full_path": self._current_file_path,
            "task_time": task_data.get("task_time", ""),
        }

    def on_complete(self) -> Dict[str, Any]:
        """
        User confirmed they completed the review.
        Returns result indicating successful completion.
        """
        self._result = {
            "status": "completed",
            "file": self._current_file_path,
            "tag_content": self._current_tag_content,
        }
        return self._result

    def on_skip(self) -> Dict[str, Any]:
        """
        User skipped the review.
        Returns result indicating skip.
        """
        self._result = {
            "status": "skipped",
            "file": self._current_file_path,
            "reason": "user_skip",
        }
        return self._result

    def get_result(self) -> Dict[str, Any]:
        """Return the final result of this review session."""
        return self._result

    def get_review_type(self) -> str:
        return "simple"

    def get_display_info(self) -> Dict:
        """Get display info for notification content."""
        return self._display_info
