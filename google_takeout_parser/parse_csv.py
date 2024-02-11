import csv
from pathlib import Path
from typing import List, TextIO, Iterator

from .models import CSVYoutubeComment, CSVYoutubeLiveChat
from .common import Res
from .time_utils import parse_json_utc_date


def _parse_youtube_comment_row(row: List[str]) -> Res[CSVYoutubeComment]:
    # Comment ID,Channel ID,Comment Create Timestamp,Price,Parent Comment ID,Video ID,Comment Text
    try:
        (
            comment_id,
            channel_id,
            created_at,
            price,
            parent_comment_id,
            video_id,
            textJSON,
        ) = row
    except ValueError as e:
        return e
    return CSVYoutubeComment(
        commentId=comment_id,
        channelId=channel_id,
        dt=parse_json_utc_date(created_at),
        price=price,
        parentCommentId=parent_comment_id if parent_comment_id.strip() else None,
        videoId=video_id,
        # for now just pass the contents of the message as JSON forwards,
        # will add helpers that let the user access it in different ways programatically
        # instead of trying to define every access pattern in a model
        contentJSON=textJSON,
    )


def is_empty_row(row: List[str]) -> bool:
    if len(row) == 0:
        return True
    for item in row:
        if item.strip():
            return False
    return True


def _parse_youtube_comments_buffer(
    buf: TextIO,
    skip_first: bool = True,
) -> Iterator[Res[CSVYoutubeComment]]:
    reader = csv.reader(buf)
    if skip_first:
        next(reader)
    for row in reader:
        if is_empty_row(row):
            continue
        if len(row) != 7:
            yield ValueError(f"Expected 7 columns, got {len(row)}: {row}")
            continue
        yield _parse_youtube_comment_row(row)


def _parse_youtube_comments_csv(path: Path) -> Iterator[Res[CSVYoutubeComment]]:
    with path.open("r", newline="") as f:
        yield from _parse_youtube_comments_buffer(f)


# Live Chat ID,Channel ID,Live Chat Create Timestamp,Price,Video ID,Live Chat Text


def _parse_youtube_live_chat_row(row: List[str]) -> Res[CSVYoutubeLiveChat]:
    try:
        (
            live_chat_id,
            channel_id,
            created_at,
            price,
            video_id,
            textJSON,
        ) = row
    except ValueError as e:
        return e
    return CSVYoutubeLiveChat(
        liveChatId=live_chat_id,
        channelId=channel_id,
        dt=parse_json_utc_date(created_at),
        price=price,
        videoId=video_id,
        contentJSON=textJSON,
    )


def _parse_youtube_live_chats_buffer(
    buf: TextIO,
    skip_first: bool = True,
) -> Iterator[Res[CSVYoutubeLiveChat]]:
    reader = csv.reader(buf)
    if skip_first:
        next(reader)
    for row in reader:
        if is_empty_row(row):
            continue
        if len(row) != 6:
            yield ValueError(f"Expected 6 columns, got {len(row)}: {row}")
            continue
        yield _parse_youtube_live_chat_row(row)


def _parse_youtube_live_chats_csv(path: Path) -> Iterator[Res[CSVYoutubeLiveChat]]:
    with path.open("r", newline="") as f:
        yield from _parse_youtube_live_chats_buffer(f)
