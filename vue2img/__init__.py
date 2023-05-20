from typing import List
from .app import Plugin, createApp, image
from .attribute import *
from .dom import *
from .manager import FontManager
from .operation import getCuttedBody, radiusMask, word2cloud
from .style import *
from .template import Template
from .util import bfs, dfs, Travel


def getComputedStyle(dom: DOM):
    return dom.style


@dfs()
def tree(dom: DOM, depth: int, parent: DOM):
    "树形打印"

    print("  " * depth + f"{dom} (parent={parent})")
