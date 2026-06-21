import logging
from pathlib import Path

def setup_logger(name: str = "to_kindle", log_file: str = "output/app.log"):
    """设置日志记录器"""
    Path(log_file).parent.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
