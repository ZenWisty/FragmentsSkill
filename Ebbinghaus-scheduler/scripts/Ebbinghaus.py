import re
import json
from datetime import datetime, timedelta
# TODO: 文档编辑器模块，后续需要实现
# import md_modifier

def curve_api(tag_content):
    """
    输入: 原始标签字符串，格式如 '[##... [review:<时间1>,<时间2>] ...##]'
    输出: (datetime对象, 修改后的标签字符串)
    逻辑: 在 [review:] 中追加新计算出的 ISO 时间点
    """
    if not tag_content:
        return None, tag_content

    # 查找 [review:...] 内容
    review_match = re.search(r'\[review:([^\]]*)\]', tag_content)

    if not review_match:
        # 没有 review 标签，返回原内容
        return None, tag_content

    review_content = review_match.group(1)  # 冒号后面的内容
    times_str = review_content.strip()  # 可能为空或包含多个时间

    # 解析已有时间
    existing_times = []
    if times_str:
        time_parts = times_str.split(',')
        for t in time_parts:
            t = t.strip()
            if t:
                try:
                    dt = datetime.fromisoformat(t)
                    existing_times.append(dt)
                except ValueError:
                    # 如果解析失败，视为无效时间
                    pass

    # 如果已有5个时间戳，不再添加
    if len(existing_times) >= 5:
        return None, tag_content

    # 计算下一个时间点
    now = datetime.now()

    # 根据已有时间数量决定下一个时间
    intervals = [
        timedelta(minutes=25),      # 0个时间 -> 25分钟后
        timedelta(hours=12),       # 1个时间 -> 12小时后
        timedelta(days=7),          # 2个时间 -> 7天后
        timedelta(days=15),         # 3个时间 -> 15天后
        timedelta(days=90),        # 4个时间 -> 3个月后(90天)
    ]

    next_interval = intervals[len(existing_times)]
    next_time = now + next_interval

    # 追加新时间到 [review:] 中
    if times_str:
        # 已有内容，加逗号再追加
        new_times_str = f"{times_str},{next_time.isoformat()}"
    else:
        # 空标签，直接加时间
        new_times_str = next_time.isoformat()

    # 替换原标签
    new_tag = re.sub(
        r'\[review:[^\]]*\]',
        f'[review:{new_times_str}]',
        tag_content
    )

    return next_time, new_tag


def adjust_current_task(tag_contents_list):
    """
    输入: 2小时内的标签内容列表
    输出: 同样长度的列表，包含 {"time": "ISO字符串", "content": "修改后的标签"}
    """
    if not tag_contents_list:
        return []

    # 获取每个标签的上下文信息
    tag_contexts = []
    for tag in tag_contents_list:
        # TODO: 后续实现文档编辑器接口
        # context = md_modifier.read_md_tag_content(tag)
        # tag_contexts.append(context)
        tag_contexts.append(tag)  # 暂时用原标签代替

    # 打印任务摘要
    print("\n=== 2小时内待安排的任务 ===")
    for i, context in enumerate(tag_contexts):
        print(f"{i+1}. {context[:100]}..." if len(context) > 100 else f"{i+1}. {context}")
    print()

    # 询问是否使用 AI skill
    choice = input("是否使用 AI skill 安排任务? (y/n): ").strip().lower()
    if choice == 'y':
        # 调用 rearrange_task_assist Claude API (MiniMax backend)
        # TODO: 后续实现 rearrange_task_assist skill
        # 以下是 MiniMax API 调用方式（待确认 base_url 和 model）
        #
        # from anthropic import Anthropic
        #
        # MINIMAX_API_KEY = "your-api-key"  # TODO: 从配置读取
        # MINIMAX_BASE_URL = "https://api.minimax.chat/v1"  # TODO: 确认正确的 base URL
        # MINIMAX_MODEL = "MiniMax-Text-01"  # TODO: 确认使用的模型名
        #
        # client = Anthropic(
        #     api_key=MINIMAX_API_KEY,
        #     base_url=MINIMAX_BASE_URL
        # )
        #
        # response = client.messages.create(
        #     model=MINIMAX_MODEL,
        #     max_tokens=1024,
        #     messages=[{
        #         "role": "user",
        #         "content": f"请重新安排以下任务，使它们在2小时内均匀分布:\n{json.dumps(tag_contexts, ensure_ascii=False)}"
        #     }]
        # )
        #
        # schedule_result = response.content[0].text
        # parsed_schedule = json.loads(schedule_result)
        # 使用 parsed_schedule 更新任务时间...

        raise NotImplementedError("rearrange_task_assist skill 尚未实现")

    # 使用均匀分布方式安排任务
    now = datetime.now()
    end_time = now + timedelta(hours=2)

    n = len(tag_contents_list)
    if n > 1:
        interval = (end_time - now) / (n - 1)  # 均匀间隔
    else:
        interval = timedelta(0)

    results = []
    for i, tag in enumerate(tag_contents_list):
        new_time = now + interval * i

        # 修改 [review:] 中当前时间（第一个未到的时间点）
        updated_tag = _update_current_time(tag, new_time)

        results.append({
            "time": new_time.isoformat(),
            "content": updated_tag
        })

    return results


def _update_current_time(tag, new_time):
    """
    更新标签中 [review:] 的当前时间（第一个未到的时间点）
    """
    review_match = re.search(r'\[review:([^\]]*)\]', tag)
    if not review_match:
        return tag

    review_content = review_match.group(1)
    if not review_content.strip():
        return tag

    times = review_content.split(',')
    now = datetime.now()
    updated = False

    new_times = []
    for t in times:
        t = t.strip()
        if not t:
            continue
        try:
            dt = datetime.fromisoformat(t)
            if dt > now and not updated:
                # 替换第一个未到的时间
                new_times.append(new_time.isoformat())
                updated = True
            else:
                new_times.append(t)
        except ValueError:
            new_times.append(t)

    new_review_content = ','.join(new_times)
    new_tag = re.sub(
        r'\[review:[^\]]*\]',
        f'[review:{new_review_content}]',
        tag
    )
    return new_tag