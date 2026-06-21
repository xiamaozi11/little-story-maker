# -*- coding: utf-8 -*-
"""Zeelin 网关 HTTP 会话与默认密钥（供 seedance20_client 使用）。"""
from __future__ import annotations

import os

import requests

# Authorization 头原样 sk-…，无 Bearer 前缀；环境变量 VOLC_SEEDANCE_API_KEY 等可覆盖（见 seedance20_client）。
DEFAULT_API_KEY = os.environ.get("VOLC_SEEDANCE_API_KEY", "").strip()


def create_requests_session() -> requests.Session:
    sess = requests.Session()
    trust = os.environ.get("VOLC_REQUESTS_TRUST_ENV", "").strip().lower()
    if trust not in ("1", "true", "yes"):
        sess.trust_env = False
    return sess
