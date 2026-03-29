import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Ebbinghaus import curve_api, adjust_current_task, _update_current_time

class TestCurveApi(unittest.TestCase):
    """Test curve_api function"""

    def test_empty_tag(self):
        """空标签返回None和原标签"""
        result = curve_api("")
        self.assertEqual(result, (None, ""))

    def test_no_review_tag(self):
        """无review标签返回原标签"""
        tag = "[## Task ##]"
        result = curve_api(tag)
        self.assertEqual(result, (None, tag))

    def test_empty_review_tag(self):
        """空的review标签添加第一个时间"""
        tag = "[## Task [review:] ##]"
        next_time, new_tag = curve_api(tag)
        self.assertIsNotNone(next_time)
        self.assertIn("[review:", new_tag)

    def test_one_timestamp(self):
        """已有1个时间戳添加第二个"""
        past = datetime.now() - timedelta(hours=1)
        tag = f"[## Task [review:{past.isoformat()}] ##]"
        next_time, new_tag = curve_api(tag)
        self.assertIsNotNone(next_time)
        # 第二个时间应该是12小时后
        self.assertGreaterEqual(next_time, datetime.now() + timedelta(hours=11))

    def test_five_timestamps(self):
        """已有5个时间戳不再添加"""
        times = [datetime.now() - timedelta(days=i) for i in range(5)]
        tag = f"[## Task [review:{','.join(t.isoformat() for t in times)}] ##]"
        next_time, new_tag = curve_api(tag)
        self.assertIsNone(next_time)
        self.assertEqual(new_tag, tag)

    def test_invalid_timestamp_ignored(self):
        """无效时间戳被忽略"""
        tag = "[## Task [review:invalid,2026-04-01T10:00:00] ##]"
        next_time, new_tag = curve_api(tag)
        self.assertIsNotNone(next_time)
        # 应该是第一个有效时间后的间隔
        self.assertIn("2026-04-01T10:00:00", new_tag)

    def test_future_times_count(self):
        """计算下一个时间时包含过去和未来时间"""
        past1 = datetime.now() - timedelta(days=1)
        past2 = datetime.now() - timedelta(days=2)
        future = datetime.now() + timedelta(days=10)
        tag = f"[## Task [review:{past1.isoformat()},{past2.isoformat()},{future.isoformat()}] ##]"
        next_time, new_tag = curve_api(tag)
        self.assertIsNotNone(next_time)
        # 已有3个时间，下一个应该是15天后
        self.assertGreaterEqual(next_time, datetime.now() + timedelta(days=14))


class TestUpdateCurrentTime(unittest.TestCase):
    """Test _update_current_time helper function"""

    def test_no_review_tag(self):
        """无review标签返回原标签"""
        tag = "[## Task ##]"
        result = _update_current_time(tag, datetime.now())
        self.assertEqual(result, tag)

    def test_update_first_unexpired_time(self):
        """替换第一个未过期的时间"""
        future1 = datetime.now() + timedelta(hours=1)
        future2 = datetime.now() + timedelta(hours=2)
        tag = f"[## Task [review:{future1.isoformat()},{future2.isoformat()}] ##]"
        new_time = datetime.now() + timedelta(minutes=30)
        result = _update_current_time(tag, new_time)
        self.assertIn(new_time.isoformat(), result)
        self.assertNotIn(future1.isoformat(), result)

    def test_does_not_update_expired_times(self):
        """不修改已过期的时间"""
        past = datetime.now() - timedelta(hours=1)
        future = datetime.now() + timedelta(hours=1)
        tag = f"[## Task [review:{past.isoformat()},{future.isoformat()}] ##]"
        new_time = datetime.now() + timedelta(minutes=30)
        result = _update_current_time(tag, new_time)
        self.assertIn(past.isoformat(), result)  # 已过期时间保留


class TestAdjustCurrentTask(unittest.TestCase):
    """Test adjust_current_task function"""

    @patch('builtins.input', return_value='n')
    def test_empty_list_returns_empty(self, mock_input):
        """空列表返回空结果"""
        result = adjust_current_task([])
        self.assertEqual(result, [])

    @patch('builtins.input', return_value='n')
    def test_single_task_equal_spacing(self, mock_input):
        """单个任务放在窗口开始"""
        tag = "[## Task [review:] ##]"
        result = adjust_current_task([tag])
        self.assertEqual(len(result), 1)
        self.assertIn("time", result[0])
        self.assertIn("content", result[0])

    @patch('builtins.input', return_value='n')
    def test_multiple_tasks_equal_spacing(self, mock_input):
        """多个任务均等间隔分布"""
        now = datetime.now()
        future = now + timedelta(hours=1)
        tags = [
            f"[## Task1 [review:{future.isoformat()}] ##]",
            f"[## Task2 [review:{future.isoformat()}] ##]",
            f"[## Task3 [review:{future.isoformat()}] ##]"
        ]
        result = adjust_current_task(tags)
        self.assertEqual(len(result), 3)
        # 验证时间在2小时窗口内
        for item in result:
            dt = datetime.fromisoformat(item["time"])
            self.assertLessEqual(dt, now + timedelta(hours=2))


if __name__ == "__main__":
    unittest.main()