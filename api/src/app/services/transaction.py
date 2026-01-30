from typing import List, Callable, Any
from dataclasses import dataclass
from ..models.response import Response

@dataclass
class Operation:
    """操作记录"""
    name: str
    execute: Callable
    rollback: Callable
    args: tuple = ()
    kwargs: dict = None
    result: Any = None

class TransactionManager:
    """事务管理器"""
    def __init__(self):
        self.operations: List[Operation] = []
        self._kwargs = {}

    def add_operation(self, operation: Operation):
        """添加操作"""
        self.operations.append(operation)

    def execute(self) -> Response:
        """执行所有操作"""
        try:
            results = []
            for op in self.operations:
                # 执行操作
                op.result = op.execute(*op.args, **(op.kwargs or {}))
                results.append(op.result)
            return Response.success(data=results)
        except Exception as e:
            # 发生错误时回滚
            self.rollback()
            return Response.error(message=str(e))

    def rollback(self):
        """回滚所有操作"""
        for op in reversed(self.operations):
            try:
                if op.result is not None:  # 只回滚已执行的操作
                    op.rollback(op.result)
            except Exception as e:
                # 记录回滚错误但不中断回滚过程
                print(f"回滚操作 {op.name} 失败: {str(e)}")
