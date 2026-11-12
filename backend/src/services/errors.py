"""复核业务异常。"""


class ReviewConflictError(Exception):
    """乐观锁冲突：两个复核员同时提交同一笔交易的结论。

    携带服务端当前版本与最新结论，前端据此提示冲突，避免静默覆盖前人判断。
    """

    def __init__(self, message: str, current_version: int, latest_decision: dict | None):
        self.message = message
        self.current_version = current_version
        self.latest_decision = latest_decision
        super().__init__(message)
