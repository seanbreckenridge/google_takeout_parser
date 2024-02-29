from io import StringIO
from datetime import datetime, timezone
from google_takeout_parser.parse_csv import (
    _parse_youtube_comments_buffer,
    _parse_youtube_live_chats_buffer,
)
from google_takeout_parser.models import CSVYoutubeComment, CSVYoutubeLiveChat


def test_parse_youtube_comment_buffer() -> None:
    text_content = """UgxtiXQkY7gqHbldJ1F4AaABAg,UCA6DtnbZ2KJckyTYfXOwQNA,2023-09-19T17:42:53.434647+00:00,0,,WtOskFeLmr4,"{""takeoutSegments"":[{""text"":""coalowl the legend""}]}"
UgwDN8UeMxW4NDFbvY54AaABAg.9iwJkUYNcXa9u0lv3j3Abh,UCA6DtnbZ2KJckyTYfXOwQNA,2023-08-30T01:54:46.801024+00:00,0,UgwDN8UeMxW4NDFbvY54AaABAg,jH39c5-y6kg,"{""takeoutSegments"":[{""text"":""Ah, this is the reason why Ive never seen concurrent write failures myself, python's default timeout value is 5s, so it just waits in a busy loop if I have 'concurrent writers'""}]}"


"""

    buf = StringIO(text_content)

    res = list(_parse_youtube_comments_buffer(buf, skip_first=False))
    assert len(res) == 2

    assert res[0] == CSVYoutubeComment(
        commentId="UgxtiXQkY7gqHbldJ1F4AaABAg",
        channelId="UCA6DtnbZ2KJckyTYfXOwQNA",
        dt=datetime(2023, 9, 19, 17, 42, 53, 434647, tzinfo=timezone.utc),
        price="0",
        parentCommentId=None,
        videoId="WtOskFeLmr4",
        contentJSON='{"takeoutSegments":[{"text":"coalowl the legend"}]}',
    )

    assert res[1] == CSVYoutubeComment(
        commentId="UgwDN8UeMxW4NDFbvY54AaABAg.9iwJkUYNcXa9u0lv3j3Abh",
        channelId="UCA6DtnbZ2KJckyTYfXOwQNA",
        dt=datetime(2023, 8, 30, 1, 54, 46, 801024, tzinfo=timezone.utc),
        price="0",
        parentCommentId="UgwDN8UeMxW4NDFbvY54AaABAg",
        videoId="jH39c5-y6kg",
        contentJSON='{"takeoutSegments":[{"text":"Ah, this is the reason why Ive never seen concurrent write failures myself, python\'s default timeout value is 5s, so it just waits in a busy loop if I have \'concurrent writers\'"}]}',
    )


def test_parse_youtube_live_chat_buffer() -> None:
    text_content = """UgwsSD8yrDW7_h6F5vZ4AaABDqgB5OC1kgI,UCA6DtnbZ2KJckyTYfXOwQNA,2018-09-02T05:16:35.510381+00:00,0,0vGCh85obuI,"{""takeoutSegments"":[{""text"":""\""think the right thing\"" jeez""}]}"

    """

    buf = StringIO(text_content)

    res = list(_parse_youtube_live_chats_buffer(buf, skip_first=False))
    assert len(res) == 1

    assert res[0] == CSVYoutubeLiveChat(
        liveChatId="UgwsSD8yrDW7_h6F5vZ4AaABDqgB5OC1kgI",
        channelId="UCA6DtnbZ2KJckyTYfXOwQNA",
        dt=datetime(2018, 9, 2, 5, 16, 35, 510381, tzinfo=timezone.utc),
        price="0",
        videoId="0vGCh85obuI",
        contentJSON='{"takeoutSegments":[{"text":""think the right thing" jeez"}]}',
    )
