"""Recognize public post URLs; search/profile indexes are discovery only."""

import re
from urllib.parse import urlsplit

RULES = {
    "reddit.com": r"^/r/[^/]+/comments/[A-Za-z0-9]+",
    "v2ex.com": r"^/t/\d+",
    "bbs.hupu.com": r"^/\d+\.html",
    "chiphell.com": r"^/(?:thread-\d+|forum\.php)",
    "nga.cn": r"^/(?:read\.php|thread\.php)",
    "ngabbs.com": r"^/(?:read\.php|thread\.php)",
    "gamer.com.tw": r"^/C\.php",
    "taptap.cn": r"^/(?:moment|topic)/\d+",
    "bilibili.com": r"^/(?:video/(?:BV|av)|opus/\d|read/cv\d|dynamic/\d)",
    "weibo.com": r"^/(?:\d{5,}/[A-Za-z0-9]+|ttarticle/p/show)",
    "weibo.cn": r"^/(?:detail|status)/[A-Za-z0-9]+",
    "zhihu.com": r"^/(?:question/\d+(?:/answer/\d+)?|p/\d+)",
    "xiaohongshu.com": r"^/(?:explore|discovery/item)/[A-Za-z0-9]+",
    "douyin.com": r"^/video/\d+",
    "tieba.baidu.com": r"^/p/\d+",
    "douban.com": r"^/(?:group/topic|note)/\d+",
    "ptt.cc": r"^/bbs/[^/]+/M\.[^/]+\.html",
    "dcard.tw": r"^/f/[^/]+/p/\d+",
    "lihkg.com": r"^/thread/\d+",
    "discuss.com.hk": r"^/(?:viewthread\.php|forum\.php|thread-\d+)",
    "huaren.us": r"^/(?:showtopic|(?:forum\.php))",
    "1point3acres.com": r"^/(?:bbs/)?(?:thread-\d+|forum\.php|viewthread\.php)",
    "wenxuecity.com": r"^/(?:bbs/[^/]+/\d+|myblog/\d+/\d+/\d+|blog/\d+)",
    "oursteps.com.au": r"^/(?:bbs/)?(?:forum\.php|thread-\d+|viewthread\.php)",
}


def social_page_kind(url):
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    for domain, pattern in RULES.items():
        if host == domain or host.endswith("." + domain):
            if host.startswith(("search.", "pgy.", "fe.", "service.", "widget.")):
                return "platform-index"
            if not re.search(pattern, p.path):
                return "platform-index"
            if p.path.endswith("forum.php") and not re.search(
                r"(?:^|&)(?:mod=viewthread|tid=\d+)", p.query
            ):
                return "platform-index"
            if domain in ["nga.cn", "ngabbs.com"] and not re.search(
                r"(?:^|&)tid=\d+", p.query
            ):
                return "platform-index"
            if domain == "gamer.com.tw" and not re.search(r"(?:^|&)snA=\d+", p.query):
                return "platform-index"
            return "public-post"
    return "non-platform-page"
