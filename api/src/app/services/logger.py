import logging
import sys
from pathlib import Path
from datetime import datetime

class Logger:
    """日志服务"""
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # 文件处理器
        log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)

    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)

    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)

# 创建全局日志实例
logger = Logger("self-host-server")
