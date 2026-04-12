# -*- coding: utf-8 -*-
"""
Abstract base class for review types.
Implement this interface to add new review types (fill_blank, choice, rating, etc.)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class ReviewInterface(ABC):
    """
    Base interface for all review types.
    Subclass this to implement specific review flows.
    """

    @abstractmethod
    def show(self, task_data: Dict) -> None:
        """
        Display the review content to the user.
        Called when user clicks on a notification card or starts a review.

        Args:
            task_data: Dictionary containing task info from pending queue
                       (path, tag_content, task_time, task_id, review_type, etc.)
        """
        pass

    @abstractmethod
    def on_complete(self) -> Dict[str, Any]:
        """
        Called when user clicks 'Complete'.
        Should return a dict with result data (e.g., score, time spent, etc.)
        """
        pass

    @abstractmethod
    def on_skip(self) -> Dict[str, Any]:
        """
        Called when user clicks 'Skip'.
        Should return a dict indicating the skip reason or metadata.
        """
        pass

    @abstractmethod
    def get_result(self) -> Dict[str, Any]:
        """
        Return the final result of this review session.
        Used by the app to write response.json.
        """
        pass

    def get_review_type(self) -> str:
        """
        Return the review type identifier string.
        Used for selecting which ReviewInterface implementation to use.
        """
        return "simple"


# Registry of available review types
_REVIEW_TYPES: Dict[str, type] = {}


def register_review_type(review_type: str, cls: type) -> None:
    """
    Register a ReviewInterface implementation for a given review_type string.
    Call this at module load time in each review implementation.
    """
    _REVIEW_TYPES[review_type] = cls


def get_review_handler(review_type: str) -> ReviewInterface:
    """
    Get an instance of the appropriate ReviewInterface for the given review_type.
    Returns SimpleReview by default if not found.
    """
    if review_type in _REVIEW_TYPES:
        return _REVIEW_TYPES[review_type]()
    # Default to simple review
    from reviewhelperapp.reviews.simple_review import SimpleReview
    return SimpleReview()
