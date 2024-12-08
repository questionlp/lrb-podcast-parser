# Copyright (c) 2024 Linh Pham
# lrb-podcast-parser is released under the terms of the MIT License
# SPDX-License-Identifier: MIT
#
# vim: set noai syntax=python ts=4 sw=4:
"""Little Red Bandwagon Podcast Feed Parser."""

import datetime
import unicodedata
from pathlib import Path
from string import Formatter
from typing import Any

import markdown
import podcastparser
import requests
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0"
_FEED_URL = "https://feeds.transistor.fm/lrb"


def parse_markdown(text: str) -> str:
    """Parse text as Markdown."""
    return markdown.markdown(text=text, output_format="html")


def generate_date_time_stamp() -> str:
    """Generate a current date/timestamp with UTC timezone."""
    now: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")


def unsmart_quotes(text: str) -> str:
    """Replaces "smart" quotes with normal quotes."""
    text: str = text.replace("’", "'")
    text = text.replace("”", '"')
    text = text.replace("“", '"')
    return text


def timedelta_to_str(
    time_delta: datetime.timedelta,
    format_string: str = "{D:02}d {H:02}h {M:02}m {S:02}s",
    input_type: str = "timedelta",
) -> str:
    """Return a formatted string for datetime.timedelta object.

    Convert a datetime.timedelta object or a regular number to a custom-
    formatted string, just like the stftime() method does for datetime.datetime
    objects.

    The fmt argument allows custom formatting to be specified.  Fields can
    include seconds, minutes, hours, days, and weeks.  Each field is optional.

    Some examples:
        '{D:02}d {H:02}h {M:02}m {S:02}s' --> '05d 08h 04m 02s' (default)
        '{W}w {D}d {H}:{M:02}:{S:02}'     --> '4w 5d 8:04:02'
        '{D:2}d {H:2}:{M:02}:{S:02}'      --> ' 5d  8:04:02'
        '{H}h {S}s'                       --> '72h 800s'

    The inputtype argument allows tdelta to be a regular number instead of the
    default, which is a datetime.timedelta object.  Valid inputtype strings:
        's', 'seconds',
        'm', 'minutes',
        'h', 'hours',
        'd', 'days',
        'w', 'weeks'

    Credit: MarredCheese (CC-BY-SA 3.0)
    Source: https://stackoverflow.com/a/42320260
    """
    # Convert tdelta to integer seconds.
    if input_type == "timedelta":
        remainder: int = int(time_delta.total_seconds())
    elif input_type in ["s", "seconds"]:
        remainder: int = int(time_delta)
    elif input_type in ["m", "minutes"]:
        remainder: int = int(time_delta) * 60
    elif input_type in ["h", "hours"]:
        remainder: int = int(time_delta) * 3600
    elif input_type in ["d", "days"]:
        remainder: int = int(time_delta) * 86400
    elif input_type in ["w", "weeks"]:
        remainder: int = int(time_delta) * 604800

    f = Formatter()
    desired_fields: list[str | None] = [field_tuple[1] for field_tuple in f.parse(format_string)]
    possible_fields: tuple = ("W", "D", "H", "M", "S")
    constants: dict[str, int] = {"W": 604800, "D": 86400, "H": 3600, "M": 60, "S": 1}
    values: dict = {}
    for field in possible_fields:
        if field in desired_fields and field in constants:
            values[field], remainder = divmod(remainder, constants[field])

    return f.format(format_string, **values)


def parse_feed(feed_url: str, feed_file: str | None = None) -> list[dict]:
    """Parser podcast feed file."""
    if feed_file:
        feed_path: Path = Path.cwd() / feed_file
        with feed_path.open(mode="r", encoding="utf-8") as _feed_file:
            _feed: dict[str, Any] = podcastparser.parse(url=feed_url, stream=_feed_file)
    else:
        with requests.get(
            url=feed_url, headers={"User-Agent": _USER_AGENT}, stream=True, timeout=30
        ) as _response:
            _response.raw.decode_content = True
            _feed: dict[str, Any] = podcastparser.parse(url=feed_url, stream=_response.raw)

    _episodes: list | None = _feed.get("episodes")
    _episodes.reverse()
    return _episodes


def process_episodes(raw_episodes: list[dict]) -> list[dict]:
    """Process raw episode data into a format used to render episodes page."""
    _processed_episodes = []
    for episode in raw_episodes:
        _guid: str = episode["guid"]
        _title: str = unsmart_quotes(text=episode["title"])
        _formatted_description: str = unsmart_quotes(text=episode["description_html"])
        _formatted_description = _formatted_description.replace(r"\+", "+")
        _formatted_description = unicodedata.normalize("NFKC", _formatted_description)
        _enclosure_url: str = episode["enclosures"][0]["url"].strip()
        _published_date: datetime.datetime = datetime.datetime.fromtimestamp(
            episode["published"], datetime.timezone.utc
        )
        _date = _published_date.strftime(format="%Y-%m-%d %H:%M:%S %Z")
        _total_time: datetime.timedelta = datetime.timedelta(seconds=episode.get("total_time", 0))
        _total_time_str: str = timedelta_to_str(
            time_delta=_total_time, format_string="{H:2}:{M:02}:{S:02}"
        )
        _processed_episodes.append(
            {
                "guid": _guid,
                "title": _title,
                "published_date": _date,
                "total_time": _total_time_str,
                "description": _formatted_description,
                "raw_description": episode["description_html"],
                "enclosure_url": _enclosure_url,
            }
        )

    return _processed_episodes


def render_html(
    episode_list: list[dict],
    template_path: str = "templates",
    template_file: str = "page.html",
    output_file: str = "output/episodes.html",
) -> None:
    """Render episodes as HTML."""
    _env: Environment = Environment(
        loader=FileSystemLoader(template_path),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    _env.filters["parse_markdown"] = parse_markdown
    _env.globals["generate_date_time_stamp"] = generate_date_time_stamp()
    _template: Template = _env.get_template(template_file)
    _page: str = _template.render(episodes=episode_list)

    output_path: Path = Path.cwd() / output_file
    with output_path.open(mode="w", encoding="utf-8") as _output_file:
        _output_file.write(_page)


episodes: list[dict] = parse_feed(feed_url=_FEED_URL, feed_file="feeds/feed.xml")

if episodes:
    processed_episodes: list[dict] = process_episodes(raw_episodes=episodes)
    render_html(episode_list=processed_episodes)
