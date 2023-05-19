import asyncio
from inspect import isfunction
from typing import Callable, Coroutine, List, Optional, Set, TypeVar

from .dom import DOM

T = TypeVar("T")


class Travel:
    "遍历"

    @staticmethod
    def preorder(node: T, depth: int, parent: T) -> Optional[bool]:
        "前序遍历"

        return True

    @staticmethod
    def postorder(node: T, depth: int, parent: T) -> Optional[bool]:
        "后续遍历"

        return True
    
    @staticmethod
    def getchildren(node: DOM) -> List[DOM]:
        "获取子元素列表"

        # 这里默认返回 dom 的子元素
        # 有需要可以自己重载这个函数
        # 或者在装饰器上传 getchildren 参数
        return node.childNodes


def bfs(
    root: Optional[T] = None,
    getchildren: Callable[[T], List[T]] = None,
):
    """
    ### 广度优先搜索
    
    root: 起点 不为空时自动启动一次
    
    getchildren: 获取子节点函数
    """

    def warpper(cls: Travel):
        
        if isfunction(cls):
            travel = Travel()
            travel.preorder = cls
        else:
            travel = cls()

        if getchildren is not None:
            travel.getchildren = getchildren

        def run(root: T):
            depth = 0
            parent = None
            used: Set[T] = set()
            nodes: List[Optional[T]] = [root, None]
            while nodes:
                node = nodes.pop(0)
                if node is None:
                    depth += 1
                    if nodes:
                        nodes.append(None)
                elif node in used:
                    travel.postorder(parent, depth-1, None)
                    # 这里 None 是因为我想不到怎么获取前一个 parent 的 parent 了
                    # 理论上是可以从 used 中找到的 但是我懒了
                    parent = node
                else:
                    if travel.preorder(node, depth, parent) is not False:
                        # 返回 False 说明当前 node 不是 T 类型 不再进行后续 bfs
                        used.add(node)
                        nodes.append(node)
                        nodes.extend(travel.getchildren(node))
        if root is not None:
            run(root)
        return run
    return warpper


def dfs(
    root: Optional[T] = None,
    getchildren: Callable[[T], List[T]] = None,
):
    """
    ### 深度优先搜索
    
    root: 起点 不为空时自动启动一次
    
    getchildren: 获取子节点函数
    """

    def warpper(cls: Travel):
        
        if isfunction(cls):
            travel = Travel()
            travel.preorder = cls
        else:
            travel = cls()

        if getchildren is not None:
            travel.getchildren = getchildren

        def run(root: T):
            depth = 0
            parents: List[T] = [None]
            nodes: List[Optional[T]] = [root]
            while nodes:
                node = nodes.pop(0)
                if node is None:
                    depth -= 1
                    node = parents.pop()
                    travel.postorder(node, depth, parents[-1])
                else:
                    if travel.preorder(node, depth, parents[-1]) is not False:
                        nodes = [*travel.getchildren(node), None, *nodes]
                        depth += 1
                        parents.append(node)

        if root is not None:
            run(root)
        return run
    return warpper


# 以下偷自 bilibili-api-python

def __ensure_event_loop() -> None:
    try:
        asyncio.get_event_loop()

    except:
        asyncio.set_event_loop(asyncio.new_event_loop())


def sync(coroutine: Coroutine):
    """
    同步执行异步函数，使用可参考 [同步执行异步代码](https://nemo2011.github.io/bilibili-api/#/sync-executor)

    Args:
        coroutine (Coroutine): 异步函数

    Returns:
        该异步函数的返回值
    """
    __ensure_event_loop()
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)