# -*- coding: utf-8 -*-
"""Fix garbled Chinese docstrings (ASCII source, UTF-8 output)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "transparent_proxy_gateway"


def patch_file(rel: str, replacements: list[tuple[str, str]]) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        if old not in text:
            print("WARN missing pattern in", rel, repr(old[:40]))
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    print("patched", rel)


HC_OLD_MOD = '"""\n??????????? httpx ?? + ??? ORM ????\n\n????????????????? ASGI ?????????????? ORM ???\n"""'
HC_NEW_MOD = (
    '"""\n'
    "\u540e\u53f0\u4e0a\u6e38\u5065\u5eb7\u68c0\u67e5\uff1ahttpx \u63a2\u6d4b + \u7ebf\u7a0b\u5185 ORM \u6301\u4e45\u5316\u3002\n\n"
    "\u5728\u72ec\u7acb\u5b88\u62a4\u7ebf\u7a0b\u4e2d\u8fd0\u884c asyncio \u5faa\u73af\uff0c"
    "\u4e0d\u963b\u585e ASGI \u4ee3\u7406\uff1b\u6570\u636e\u5e93\u4f7f\u7528\u5bbf\u4e3b DATABASES\u3002\n"
    '"""'
)

patch_file(
    "services/health_checker.py",
    [
        (HC_OLD_MOD, HC_NEW_MOD),
        (
            '    """\n    ??????????????? API ??????\n\n    ?????????? False?\n    """',
            '    """\n    \u5f02\u6b65\u8c03\u5ea6\u5355\u6b21\u5065\u5eb7\u68c0\u67e5\uff08\u5982\u7ba1\u7406 API \u624b\u52a8\u89e6\u53d1\uff09\u3002\n\n    \u82e5\u5df2\u6709\u68c0\u67e5\u5728\u8dd1\u5219\u8fd4\u56de False\u3002\n    """',
        ),
    ],
)

RW_OLD_MOD = (
    '"""\n?????????? Location?Set-Cookie Path?Referer/Origin?\n\n'
    "301/302/303/307/308 ? ``Location`` ?????? URL?httpx ??\n"
    "``follow_redirects=False``???????????``Set-Cookie`` ? Path\n"
    "???????????? Cookie ?????????\n\"\"\""
)
RW_NEW_MOD = (
    '"""\n'
    "\u4e0a\u6e38\u54cd\u5e94\u6539\u5199\uff1a\u91cd\u5b9a\u5411 Location\u3001Set-Cookie Path\u3001Referer/Origin\u3002\n\n"
    "301/302/303/307/308 \u7684 ``Location`` \u4f1a\u6539\u5199\u4e3a\u7f51\u5173 URL\uff08httpx \u4f7f\u7528\n"
    "``follow_redirects=False``\uff0c\u7531\u6d4f\u89c8\u5668\u8ddf\u968f\u8df3\u8f6c\uff09\u3002"
    "``Set-Cookie`` \u7684 Path\n"
    "\u4f1a\u52a0\u4e0a\u7f51\u5173\u524d\u7f00\uff0c\u907f\u514d\u4f1a\u8bdd Cookie \u5728\u7f51\u5173\u8def\u5f84\u4e0b\u4e22\u5931\u3002\n"
    '"""'
)

patch_file(
    "proxy/response_rewrite.py",
    [
        (RW_OLD_MOD, RW_NEW_MOD),
        ("# ???? Location ? HTTP ???", "# \u9700\u8981\u6539\u5199 Location \u7684 HTTP \u72b6\u6001\u7801"),
        (
            '    """???? URL ? host:port ?????? loopback ????"""',
            '    """\u5224\u65ad\u4e24\u4e2a URL \u7684 host:port \u662f\u5426\u7b49\u4ef7\uff08\u542b loopback \u4e92\u8ba4\uff09\u3002"""',
        ),
        (
            '    """? Referer/Origin ????????????????? CSRF/CORS??"""',
            '    """\u5c06 Referer/Origin \u4e2d\u7f51\u5173\u5730\u5740\u66ff\u6362\u4e3a\u4e0a\u6e38\u6e90\u7ad9\u5730\u5740\u3002"""',
        ),
        (
            '    """\n    ?? Set-Cookie??? Domain??? Path ?????? + ?? Path??\n\n    ????? Path=/admin/????? /test ? Path=/test/admin/\n    """',
            '    """\n    \u6539\u5199 Set-Cookie\uff1a\u53bb\u6389 Domain\uff0c\u5408\u5e76 Path \u4e3a\u300c\u7f51\u5173\u524d\u7f00 + \u4e0a\u6e38 Path\u300d\u3002\n\n    \u793a\u4f8b\uff1a\u4e0a\u6e38 Path=/admin/\u3001\u7f51\u5173\u524d\u7f00 /test \u2192 Path=/test/admin/\n    """',
        ),
        (
            '    """\n    ? Location ????????? URL??? nginx proxy_redirect??\n\n    ????/?????????? URL??? loopback ????????\n    """',
            '    """\n    \u5c06 Location \u6539\u5199\u4e3a\u7ecf\u7f51\u5173\u8bbf\u95ee\u7684 URL\uff08\u7c7b\u4f3c nginx proxy_redirect\uff09\u3002\n\n    \u652f\u6301\u7edd\u5bf9/\u76f8\u5bf9\u8def\u5f84\u3001\u6307\u5411\u4e0a\u6e38\u7684 URL\uff0c\u4ee5\u53ca loopback \u4e92\u8ba4\u573a\u666f\u3002\n    """',
        ),
        (
            '    """??????? Location ????????"""',
            '    """\u662f\u5426\u4e3a\u9700\u8981\u6539\u5199 Location \u7684\u91cd\u5b9a\u5411\u72b6\u6001\u7801\u3002"""',
        ),
        (
            '    """???/??????? Location?Set-Cookie ?????? (name, value) ???"""',
            '    """\u5bf9\u6d41\u5f0f/\u7f13\u51b2\u54cd\u5e94\u5934\u5e94\u7528\u6539\u5199\uff0c\u8fd4\u56de (name, value) \u5217\u8868\u3002"""',
        ),
        (
            '    """??? Set-Cookie ????? Django response.cookies?"""',
            '    """\u5c06\u5355\u6761 Set-Cookie \u89e3\u6790\u540e\u5199\u5165 Django response.cookies\u3002"""',
        ),
        (
            '    """???????????Set-Cookie ?? set_cookie ??????"""',
            '    """\u5c06\u6539\u5199\u540e\u7684\u5934\u5199\u5165\u54cd\u5e94\uff1bSet-Cookie \u4f7f\u7528 set_cookie \u4ee5\u652f\u6301\u591a\u6761\u3002"""',
        ),
    ],
)
