# -*- coding: utf-8 -*-
"""
Doubao Seedance 2.0 视频生成：按网关 JSON 体封装 POST。

依赖: pip install requests

环境变量（与 TTSv3HttpDemo 对齐，便于同一套密钥）:
  VOLC_SEEDANCE20_URL — 提交任务 POST 地址（默认 /v1/video/generations）
  VOLC_SEEDANCE20_RESULT_URL — 查询结果 POST 地址（默认 /v1/video/result，body: model + task_id）
  VOLC_SEEDANCE_POLL_INTERVAL_SEC — 轮询间隔秒，默认 5
  VOLC_SEEDANCE_POLL_TIMEOUT_SEC — 轮询总超时秒，默认 600
  VOLC_SEEDANCE_MAX_AUDIOS — byPass.audios 条数上限，默认 3（与 VOLC_TTS_MAX_STORYBOARD_AUDIO_REFS 同源）
  VOLC_SEEDANCE_API_KEY — 优先；否则依次尝试 VOLC_TTS_API_KEY、VOLC_CHAT_API_KEY；均未设时用 zeelin_gateway.DEFAULT_API_KEY
  VOLC_REQUESTS_TRUST_ENV — 可选；1/true 时使用系统 HTTP(S)_PROXY；默认直连（避免 HTTPS 代理 SSL 报错）
  VOLC_SEEDANCE_EXTRA_HEADERS_JSON — 可选，JSON 对象合并进请求头
  VOLC_TTS_EXTRA_HEADERS_JSON — 若上一项未设，则沿用主 demo 的扩展头
  VOLC_SEEDANCE_AUDIO_UPLOAD_URL — 可选；multipart 上传本地 TTS 文件，返回 JSON 中的公网 URL 写入 byPass.audios
  VOLC_SEEDANCE_AUDIO_UPLOAD_FIELD — 表单字段名，默认 file
  VOLC_SEEDANCE_AUDIO_UPLOAD_RESPONSE_URL_KEY — 从上传响应 JSON 取 URL 的点分路径，默认 url（可设 data.url 等）
  VOLC_SEEDANCE_AUDIO_UPLOAD_HEADERS_JSON — 可选；上传请求的额外 HTTP 头（勿含 Content-Type，由 requests 自动带 boundary）

请求头默认与 TTS 一致：``Authorization`` 为 ``sk-...`` 原样（无 Bearer 前缀），
``Content-Type: application/json``；若网关要求 Bearer，请在扩展头里覆盖。
"""
from __future__ import annotations

import json
import mimetypes
import os
import sys
import time
from typing import Any, Dict

import requests

from zeelin_gateway import DEFAULT_API_KEY as _DEFAULT_ZEELIN_API_KEY
from zeelin_gateway import create_requests_session

# 网关 body 中的 model 字段示例名
SEEDANCE20_MODEL_DEFAULT = "Doubao-Seedance-2.0"
# Seedance 2.0 ``byPass.audios`` 上传条数上限（与分镜 TTS 段数一致）
SEEDANCE20_MAX_AUDIOS_DEFAULT = 3

# 与 Zeelin 其它 v1 接口同域时的占位默认；实际路径请以网关文档为准并用环境变量覆盖
DEFAULT_SEEDANCE20_URL = "https://getways-jumu.zeelin.cn/v1/video/generations"
DEFAULT_SEEDANCE20_RESULT_URL = "https://getways-jumu.zeelin.cn/v1/video/result"

# 轮询查询 task_id 时尝试解析视频 URL 的 JSON 点分路径（按序）
_VIDEO_URL_JSON_PATHS = (
    "video_url",
    "output_url",
    "url",
    "data.video_url",
    "data.output_url",
    "data.url",
    "result.video_url",
    "result.url",
    "content.video_url",
    "content.url",
)

# 提交/查询响应中解析 task_id 的点分路径（按序）
_TASK_ID_JSON_PATHS = (
    "task_id",
    "taskId",
    "data.task_id",
    "data.taskId",
    "data.id",
    "result.task_id",
    "content.task_id",
)


# 与网关 JSON ``byPass`` 常见字段一致（驼峰键名由 ``build_seedance20_payload`` 写入）；ratio、resolution、videos、audios 等
Seedance20ByPass = Dict[str, Any]


def max_seedance_audio_uploads() -> int:
    """``byPass.audios`` 条数上限；``VOLC_SEEDANCE_MAX_AUDIOS`` 或 ``VOLC_TTS_MAX_STORYBOARD_AUDIO_REFS``，默认 3。"""
    for key in ("VOLC_SEEDANCE_MAX_AUDIOS", "VOLC_TTS_MAX_STORYBOARD_AUDIO_REFS"):
        raw = os.environ.get(key, "").strip()
        if raw.isdigit():
            return max(1, int(raw))
    return SEEDANCE20_MAX_AUDIOS_DEFAULT


def validate_seedance_audios_limit(
    audios: list[Any] | None,
    *,
    max_audios: int | None = None,
) -> dict[str, Any]:
    """提交前校验 ``byPass.audios`` 条数不超过 Seedance 2.0 上限。"""
    cap = max_audios if max_audios is not None else max_seedance_audio_uploads()
    urls = [u for u in (audios or []) if str(u).strip()]
    n = len(urls)
    if n > cap:
        return {
            "ok": False,
            "error": (
                f"Seedance 2.0 最多上传 {cap} 条音频，当前 {n} 条；"
                "请合并旁白/台词或减少 TTS 段数。"
            ),
            "count": n,
            "max_audios": cap,
            "step": "precheck_seedance_audios",
        }
    return {"ok": True, "count": n, "max_audios": cap}


def _resolve_seedance_api_key(explicit: str | None) -> str:
    return (
        (explicit or "").strip()
        or os.environ.get("VOLC_SEEDANCE_API_KEY", "").strip()
        or os.environ.get("VOLC_TTS_API_KEY", "").strip()
        or os.environ.get("VOLC_CHAT_API_KEY", "").strip()
        or _DEFAULT_ZEELIN_API_KEY.strip()
    )


def _seedance_request_headers(api_key: str) -> dict[str, str]:
    h: dict[str, str] = {
        "Authorization": api_key.strip(),
        "Content-Type": "application/json",
        "Connection": "keep-alive",
    }
    raw = os.environ.get("VOLC_SEEDANCE_EXTRA_HEADERS_JSON", "").strip()
    if not raw:
        raw = os.environ.get("VOLC_TTS_EXTRA_HEADERS_JSON", "").strip()
    if not raw:
        return h
    try:
        extra = json.loads(raw)
    except json.JSONDecodeError:
        return h
    if not isinstance(extra, dict):
        return h
    for k, v in extra.items():
        if not isinstance(k, str) or not k.strip():
            continue
        if v is None:
            continue
        h[k.strip()] = v if isinstance(v, str) else str(v)
    return h


def _resolve_seedance_url(explicit: str | None) -> str:
    u = (explicit or "").strip() or os.environ.get("VOLC_SEEDANCE20_URL", "").strip()
    return u if u else DEFAULT_SEEDANCE20_URL


def _resolve_seedance_result_url(explicit: str | None) -> str:
    u = (explicit or "").strip() or os.environ.get("VOLC_SEEDANCE20_RESULT_URL", "").strip()
    return u if u else DEFAULT_SEEDANCE20_RESULT_URL


def _poll_interval_sec(explicit: float | None) -> float:
    if explicit is not None and float(explicit) > 0:
        return float(explicit)
    raw = os.environ.get("VOLC_SEEDANCE_POLL_INTERVAL_SEC", "").strip()
    if raw:
        try:
            v = float(raw)
            if v > 0:
                return v
        except ValueError:
            pass
    return 5.0


def _poll_timeout_sec(explicit: float | None) -> float:
    if explicit is not None and float(explicit) > 0:
        return float(explicit)
    raw = os.environ.get("VOLC_SEEDANCE_POLL_TIMEOUT_SEC", "").strip()
    if raw:
        try:
            v = float(raw)
            if v > 0:
                return v
        except ValueError:
            pass
    return 600.0


def extract_task_id_from_response(data: Any) -> str | None:
    """从提交/查询 JSON 中解析 ``task_id``。"""
    if isinstance(data, str) and data.strip():
        return data.strip()
    if not isinstance(data, dict):
        return None
    for key in ("task_id", "taskId", "taskID", "id"):
        v = data.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    for path in _TASK_ID_JSON_PATHS:
        v = _dig_json_key(data, path)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def extract_video_url_from_result(data: Any) -> str | None:
    """从查询结果 JSON 中解析成片 ``http(s)`` URL。"""
    if isinstance(data, str) and data.strip().lower().startswith(("http://", "https://")):
        return data.strip().split()[0]
    if isinstance(data, list):
        for item in data:
            u = extract_video_url_from_result(item)
            if u:
                return u
        return None
    if not isinstance(data, dict):
        return None
    # Zeelin 查询成功常见：{"data": [{"url": "https://...mp4?..."}], "task_id": "..."}
    nested = data.get("data")
    if isinstance(nested, list):
        for item in nested:
            if isinstance(item, dict):
                u = item.get("url")
                if isinstance(u, str) and u.strip().lower().startswith(("http://", "https://")):
                    return u.strip()
    for path in _VIDEO_URL_JSON_PATHS:
        v = _dig_json_key(data, path)
        if isinstance(v, str) and v.strip().lower().startswith(("http://", "https://")):
            return v.strip()
    return None


def _normalize_task_status(raw: Any) -> str:
    s = str(raw or "").strip().lower()
    if s in ("success", "succeeded", "completed", "complete", "done", "finish", "finished", "succeed"):
        return "succeeded"
    if s in ("fail", "failed", "failure", "error", "cancelled", "canceled", "timeout"):
        return "failed"
    if s in (
        "pending",
        "processing",
        "process",
        "running",
        "run",
        "queued",
        "queue",
        "waiting",
        "in_progress",
        "in progress",
        "submitted",
    ):
        return "pending"
    return "unknown"


def classify_seedance_task_state(data: Any) -> tuple[str, str | None]:
    """
    解析任务状态。

    返回 ``(state, message)``，``state`` 为 ``pending`` | ``succeeded`` | ``failed`` | ``unknown``。
    """
    video_url = extract_video_url_from_result(data)
    if video_url:
        return "succeeded", None

    if not isinstance(data, dict):
        return "unknown", None

    for path in ("error", "message", "msg", "data.error", "data.message"):
        err = _dig_json_key(data, path)
        if isinstance(err, str) and err.strip():
            st = _normalize_task_status(err)
            if st == "failed":
                return "failed", err.strip()
        if isinstance(err, dict):
            em = err.get("message") or err.get("msg")
            if isinstance(em, str) and em.strip():
                return "failed", em.strip()

    for path in ("status", "state", "task_status", "data.status", "data.state", "result.status"):
        raw = _dig_json_key(data, path)
        if raw is not None:
            st = _normalize_task_status(raw)
            if st != "unknown":
                msg = None
                if st == "failed":
                    msg = str(_dig_json_key(data, "message") or _dig_json_key(data, "data.message") or "")
                    msg = msg.strip() or None
                return st, msg

    code = data.get("code")
    if code is not None:
        try:
            c = int(code)
            if c == 0 and video_url:
                return "succeeded", None
            if c != 0:
                em = data.get("message") or data.get("msg")
                return "failed", str(em).strip() if em else f"code={c}"
        except (TypeError, ValueError):
            pass

    return "unknown", None


def _http_json_response(resp: requests.Response, *, url: str) -> dict[str, Any]:
    text = resp.text or ""
    parsed: Any = None
    err: str | None = None
    try:
        if text.strip():
            parsed = resp.json()
    except json.JSONDecodeError:
        parsed = None
        if not resp.ok:
            err = f"HTTP {resp.status_code}，响应非 JSON"

    if not resp.ok and err is None:
        err = f"HTTP {resp.status_code}"
        if isinstance(parsed, dict) and parsed.get("error"):
            err = f"{err}: {parsed.get('error')}"
        elif text.strip():
            err = f"{err}: {text[:2000]}"

    return {
        "ok": 200 <= resp.status_code < 300,
        "status_code": resp.status_code,
        "json": parsed,
        "text": text,
        "error": err,
        "url": url,
    }


def query_seedance20_video_result(
    task_id: str,
    *,
    model: str | None = None,
    result_url: str | None = None,
    api_key: str | None = None,
    timeout: float = 60.0,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """
    查询异步任务结果：POST ``/v1/video/result``，body ``{model, task_id}``。
    """
    tid = (task_id or "").strip()
    if not tid:
        return {"ok": False, "error": "task_id 为空", "status_code": 0, "json": None, "text": "", "url": ""}

    key = _resolve_seedance_api_key(api_key)
    if not key:
        return {
            "ok": False,
            "error": "未设置 api_key",
            "status_code": 0,
            "json": None,
            "text": "",
            "url": _resolve_seedance_result_url(result_url),
        }

    endpoint = _resolve_seedance_result_url(result_url)
    headers = _seedance_request_headers(key)
    body = {
        "model": (model or "").strip() or SEEDANCE20_MODEL_DEFAULT,
        "task_id": tid,
    }

    own_session = session is None
    sess = session or create_requests_session()
    try:
        resp = sess.post(endpoint, headers=headers, json=body, timeout=timeout)
    except requests.RequestException as e:
        if own_session:
            sess.close()
        return {
            "ok": False,
            "status_code": 0,
            "json": None,
            "text": "",
            "error": str(e),
            "url": endpoint,
        }

    out = _http_json_response(resp, url=endpoint)
    if own_session:
        sess.close()

    state, state_msg = classify_seedance_task_state(out.get("json"))
    out["task_state"] = state
    out["state_message"] = state_msg
    out["video_url"] = extract_video_url_from_result(out.get("json"))
    out["task_id"] = tid
    return out


def poll_seedance20_task(
    task_id: str,
    *,
    model: str | None = None,
    result_url: str | None = None,
    api_key: str | None = None,
    poll_interval_sec: float | None = None,
    poll_timeout_sec: float | None = None,
    query_timeout: float = 60.0,
    session: requests.Session | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    """
    按固定间隔轮询 ``task_id``，直至成功、失败或超时。

    返回含 ``ok``、``task_id``、``video_url``、``poll_attempts``、``last_poll``、``poll_history``（简要）等。
    """
    tid = (task_id or "").strip()
    if not tid:
        return {"ok": False, "error": "task_id 为空", "step": "poll"}

    interval = _poll_interval_sec(poll_interval_sec)
    timeout_total = _poll_timeout_sec(poll_timeout_sec)
    deadline = time.monotonic() + timeout_total
    attempts = 0
    last: dict[str, Any] = {}
    history: list[dict[str, Any]] = []

    own_session = session is None
    sess = session or create_requests_session()
    try:
        while time.monotonic() < deadline:
            attempts += 1
            last = query_seedance20_video_result(
                tid,
                model=model,
                result_url=result_url,
                api_key=api_key,
                timeout=query_timeout,
                session=sess,
            )
            state = last.get("task_state") or "unknown"
            history.append(
                {
                    "attempt": attempts,
                    "task_state": state,
                    "video_url": last.get("video_url"),
                    "error": last.get("error"),
                }
            )
            if verbose:
                vu = last.get("video_url") or ""
                tail = f" video_url={vu[:80]}…" if len(vu) > 80 else (f" video_url={vu}" if vu else "")
                print(
                    f"  [Seedance 轮询 #{attempts}] task_state={state}{tail}",
                    flush=True,
                )

            if state == "succeeded":
                return {
                    "ok": True,
                    "task_id": tid,
                    "video_url": last.get("video_url"),
                    "poll_attempts": attempts,
                    "last_poll": last,
                    "poll_history": history,
                    "poll_interval_sec": interval,
                    "poll_timeout_sec": timeout_total,
                }
            if state == "failed":
                msg = last.get("state_message") or last.get("error") or "任务失败"
                return {
                    "ok": False,
                    "task_id": tid,
                    "error": msg,
                    "poll_attempts": attempts,
                    "last_poll": last,
                    "poll_history": history,
                    "step": "poll_failed",
                }

            if time.monotonic() + interval > deadline:
                break
            time.sleep(interval)
    finally:
        if own_session:
            sess.close()

    return {
        "ok": False,
        "task_id": tid,
        "error": f"轮询超时（>{timeout_total:.0f}s，共 {attempts} 次）",
        "poll_attempts": attempts,
        "last_poll": last,
        "poll_history": history,
        "step": "poll_timeout",
    }


def post_seedance20_and_wait(
    prompt: str,
    *,
    poll: bool = True,
    poll_interval_sec: float | None = None,
    poll_timeout_sec: float | None = None,
    model: str | None = None,
    submit_url: str | None = None,
    result_url: str | None = None,
    api_key: str | None = None,
    submit_timeout: float = 120.0,
    query_timeout: float = 60.0,
    session: requests.Session | None = None,
    verbose: bool = True,
    **post_kwargs: Any,
) -> dict[str, Any]:
    """
    提交 Seedance 2.0 任务；若 ``poll=True``（默认）则轮询 ``/v1/video/result`` 直至成片或失败。

    返回 ``submit``（提交响应）、``task_id``、``video_url``（成功时）、``ok``（最终是否拿到成片）。
    """
    submit = post_seedance20(
        prompt,
        model=model,
        url=submit_url,
        api_key=api_key,
        timeout=submit_timeout,
        session=session,
        **post_kwargs,
    )
    out: dict[str, Any] = {"submit": submit, "ok": False}

    if not submit.get("ok"):
        out["error"] = submit.get("error") or "提交失败"
        out["step"] = "submit"
        return out

    task_id = submit.get("task_id") or extract_task_id_from_response(submit.get("json"))
    video_sync = extract_video_url_from_result(submit.get("json"))
    if video_sync:
        out["ok"] = True
        out["task_id"] = task_id
        out["video_url"] = video_sync
        out["sync_response"] = True
        return out

    if not task_id:
        out["error"] = "提交成功但未解析到 task_id，且响应中无 video_url"
        out["step"] = "submit_parse_task_id"
        return out

    out["task_id"] = task_id
    if verbose:
        print(f"【Seedance 2.0】已提交 task_id={task_id}，开始轮询结果…\n", flush=True)

    if not poll:
        out["poll_skipped"] = True
        out["ok"] = True
        return out

    poll_r = poll_seedance20_task(
        task_id,
        model=model,
        result_url=result_url,
        api_key=api_key,
        poll_interval_sec=poll_interval_sec,
        poll_timeout_sec=poll_timeout_sec,
        query_timeout=query_timeout,
        session=session,
        verbose=verbose,
    )
    out["poll"] = poll_r
    out["ok"] = bool(poll_r.get("ok"))
    out["video_url"] = poll_r.get("video_url")
    if not out["ok"]:
        out["error"] = poll_r.get("error")
        out["step"] = poll_r.get("step") or "poll"
    return out


def _dig_json_key(obj: Any, dotted: str) -> Any:
    cur: Any = obj
    for part in (dotted or "").strip().split("."):
        if not part:
            continue
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _upload_extra_headers() -> dict[str, str]:
    raw = os.environ.get("VOLC_SEEDANCE_AUDIO_UPLOAD_HEADERS_JSON", "").strip()
    if not raw:
        return {}
    try:
        extra = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(extra, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in extra.items():
        if isinstance(k, str) and k.strip() and v is not None:
            out[k.strip()] = v if isinstance(v, str) else str(v)
    return out


def upload_local_audio_via_multipart(
    local_path: str,
    upload_url: str,
    *,
    field_name: str | None = None,
    response_url_key: str | None = None,
    api_key: str | None = None,
    timeout: float = 180.0,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """
    将本地音频以 ``multipart/form-data`` POST 到业务上传接口，从响应中解析公网 URL（供 Seedance ``byPass.audios``）。

    响应为 JSON 时，用 ``response_url_key`` 或环境变量 ``VOLC_SEEDANCE_AUDIO_UPLOAD_RESPONSE_URL_KEY``
    （点分路径，默认 ``url``）取出字符串 URL。响应为纯文本且整行为 ``http(s)://...`` 时也接受。

    可选请求头：``VOLC_SEEDANCE_AUDIO_UPLOAD_HEADERS_JSON``；若传入 ``api_key`` 且未在该 JSON 里写 Authorization，
    则自动加 ``Authorization: <api_key>``（与 TTS 头一致，无 Bearer 前缀）。
    """
    path = os.path.abspath(local_path)
    ep = (upload_url or "").strip()
    if not ep:
        return {"ok": False, "url": None, "error": "upload_url 为空"}
    if not os.path.isfile(path):
        return {"ok": False, "url": None, "error": f"文件不存在: {path}"}

    field = (field_name or "").strip() or os.environ.get("VOLC_SEEDANCE_AUDIO_UPLOAD_FIELD", "").strip() or "file"
    url_key = (response_url_key or "").strip() or os.environ.get(
        "VOLC_SEEDANCE_AUDIO_UPLOAD_RESPONSE_URL_KEY", ""
    ).strip() or "url"

    mime, _ = mimetypes.guess_type(path)
    if not mime:
        ext = os.path.splitext(path)[1].lower()
        mime = "audio/mpeg" if ext in (".mp3", ".mpeg") else "application/octet-stream"

    headers = _upload_extra_headers()
    key = _resolve_seedance_api_key(api_key)
    if key and not any(k.lower() == "authorization" for k in headers):
        headers = {**headers, "Authorization": key}

    own_session = session is None
    sess = session or create_requests_session()
    resp: Any = None
    try:
        with open(path, "rb") as f:
            files = {field: (os.path.basename(path), f, mime)}
            resp = sess.post(ep, files=files, headers=headers or None, timeout=timeout)
    except OSError as e:
        return {"ok": False, "url": None, "error": str(e)}
    except requests.RequestException as e:
        return {"ok": False, "url": None, "error": str(e)}
    finally:
        if own_session:
            sess.close()

    if resp is None:
        return {"ok": False, "url": None, "error": "上传无响应"}

    text = (resp.text or "").strip()
    if not (200 <= resp.status_code < 300):
        return {
            "ok": False,
            "url": None,
            "error": f"HTTP {resp.status_code}: {text[:800]}",
            "status_code": resp.status_code,
        }

    if text.lower().startswith("http://") or text.lower().startswith("https://"):
        return {"ok": True, "url": text.split()[0], "status_code": resp.status_code}

    try:
        data = json.loads(text) if text else None
    except json.JSONDecodeError:
        return {
            "ok": False,
            "url": None,
            "error": f"上传响应非 URL 文本且非 JSON: {text[:400]!r}",
            "status_code": resp.status_code,
        }

    if not isinstance(data, dict):
        return {"ok": False, "url": None, "error": "上传响应 JSON 非对象", "status_code": resp.status_code}

    raw_url = _dig_json_key(data, url_key)
    if raw_url is None and url_key != "url":
        raw_url = _dig_json_key(data, "url")
    if isinstance(raw_url, str) and raw_url.strip().lower().startswith(("http://", "https://")):
        return {"ok": True, "url": raw_url.strip(), "status_code": resp.status_code}

    return {
        "ok": False,
        "url": None,
        "error": f"无法在响应 JSON 中解析 URL（键 {url_key!r}）: {str(data)[:600]}",
        "status_code": resp.status_code,
    }


def build_seedance20_payload(
    prompt: str,
    *,
    duration: int = 10,
    size: str = "720x1280",
    generate_audio: bool = True,
    generate_mode: int = 1,
    by_pass: Seedance20ByPass | dict[str, Any] | None = None,
    images: list[str] | None = None,
    model: str | None = None,
    extra_top_level: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    构造与文档一致的请求体（顶层 ``byPass`` 使用驼峰键名）。

    ``by_pass`` 为 Python 侧参数名，写入 JSON 时转为 ``byPass``。
    ``extra_top_level`` 可附加网关未列出的顶层字段（会浅合并，后者覆盖前者同键）。
    """
    body: dict[str, Any] = {
        "model": (model or "").strip() or SEEDANCE20_MODEL_DEFAULT,
        "prompt": prompt,
        "duration": duration,
        "size": size,
        "generate_audio": generate_audio,
        "generate_mode": generate_mode,
    }
    if by_pass is not None:
        body["byPass"] = dict(by_pass)
    if images is not None:
        body["images"] = list(images)
    if extra_top_level:
        body.update(extra_top_level)
    return body


def build_seedance20_prompt_with_refs(
    base: str,
    *,
    image_labels: list[str] | None = None,
    audio_labels: list[str] | None = None,
    video_labels: list[str] | None = None,
) -> str:
    """
    拼接 ``prompt``：约定 **参考占位在前、剧本文本在后**（``@图片1`` 等与 ``images`` 数组下标对应）。

    顺序：参考图片段（``参考图片1\\n@图片1`` …）→ 参考音频段 → 参考视频段 → ``base`` 剧本。
    ``base`` 可为空，则仅输出参考段；``image_labels`` 等为空则跳过对应段。
    """
    parts: list[str] = []
    b = (base or "").strip()

    def _append(kind_cn: str, at_prefix: str, labels: list[str] | None) -> None:
        if not labels:
            return
        for i, lab in enumerate(labels, start=1):
            line = f"参考{kind_cn}{i}\n@{at_prefix}{i}"
            if str(lab).strip():
                line += f"  {str(lab).strip()}"
            parts.append(line)

    _append("图片", "图片", image_labels)
    _append("音频", "音频", audio_labels)
    _append("视频", "视频", video_labels)
    if b:
        parts.append(b)
    return "\n".join(parts).strip()


def post_seedance20(
    prompt: str,
    *,
    duration: int = 10,
    size: str = "1920x1080",
    generate_audio: bool = True,
    generate_mode: int = 1,
    by_pass: Seedance20ByPass | dict[str, Any] | None = None,
    images: list[str] | None = None,
    model: str | None = None,
    url: str | None = None,
    api_key: str | None = None,
    timeout: float = 120.0,
    session: requests.Session | None = None,
    extra_top_level: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    调用 Seedance 2.0：POST JSON，返回统一结构（便于脚本判断）。

    返回字段：``ok``（2xx 且解析未抛错）、``status_code``、``json``（若响应为 JSON）、
    ``text``（原始文本，截断前全量）、``error``（失败说明）、``url``（实际请求地址）。
    """
    key = _resolve_seedance_api_key(api_key)
    if not key:
        return {
            "ok": False,
            "status_code": 0,
            "json": None,
            "text": "",
            "error": "未设置 api_key（传 api_key= 或 VOLC_SEEDANCE_API_KEY / VOLC_TTS_API_KEY / VOLC_CHAT_API_KEY；未设环境变量时使用 zeelin_gateway.DEFAULT_API_KEY）",
            "url": _resolve_seedance_url(url),
        }

    audios_in = None
    if isinstance(by_pass, dict):
        audios_in = by_pass.get("audios")
    pre = validate_seedance_audios_limit(
        list(audios_in) if isinstance(audios_in, (list, tuple)) else None
    )
    if not pre.get("ok"):
        return {
            "ok": False,
            "status_code": 0,
            "json": None,
            "text": "",
            "error": pre.get("error"),
            "url": _resolve_seedance_url(url),
            "step": pre.get("step"),
        }

    endpoint = _resolve_seedance_url(url)
    headers = _seedance_request_headers(key)
    payload = build_seedance20_payload(
        prompt,
        duration=duration,
        size=size,
        generate_audio=generate_audio,
        generate_mode=generate_mode,
        by_pass=by_pass,
        images=images,
        model=model,
        extra_top_level=extra_top_level,
    )

    print("【Seedance 2.0】即将 POST，prompt 全文如下：", flush=True)
    print("-" * 56, flush=True)
    print((payload.get("prompt") or prompt or "").strip() or "(空)", flush=True)
    print("-" * 56, flush=True)

    own_session = session is None
    sess = session or create_requests_session()
    try:
        resp = sess.post(endpoint, headers=headers, json=payload, timeout=timeout)
    except requests.RequestException as e:
        if own_session:
            sess.close()
        return {
            "ok": False,
            "status_code": 0,
            "json": None,
            "text": "",
            "error": str(e),
            "url": endpoint,
        }

    text = resp.text or ""
    parsed: Any = None
    err: str | None = None
    try:
        if text.strip():
            parsed = resp.json()
    except json.JSONDecodeError:
        parsed = None
        if not resp.ok:
            err = f"HTTP {resp.status_code}，响应非 JSON"

    if not resp.ok and err is None:
        err = f"HTTP {resp.status_code}"
        if isinstance(parsed, dict) and parsed.get("error"):
            err = f"{err}: {parsed.get('error')}"
        elif text.strip():
            err = f"{err}: {text[:2000]}"

    if own_session:
        sess.close()

    out = {
        "ok": 200 <= resp.status_code < 300,
        "status_code": resp.status_code,
        "json": parsed,
        "text": text,
        "error": err,
        "url": endpoint,
    }
    if isinstance(parsed, dict):
        tid = extract_task_id_from_response(parsed)
        if tid:
            out["task_id"] = tid
        vurl = extract_video_url_from_result(parsed)
        if vurl:
            out["video_url"] = vurl
    return out


def _cli(argv: list[str]) -> int:
    import argparse

    p = argparse.ArgumentParser(description="POST Doubao-Seedance-2.0（打印 JSON 响应摘要）")
    p.add_argument("--prompt", default="", help="主 prompt；不设则用文档示例句式")
    p.add_argument("--dry-run", action="store_true", help="仅打印请求体 JSON，不发起 HTTP")
    p.add_argument("--url", default="", help="覆盖 VOLC_SEEDANCE20_URL")
    p.add_argument("--no-poll", action="store_true", help="仅提交，不轮询 /v1/video/result")
    p.add_argument("--poll-interval", type=float, default=None, help="轮询间隔秒")
    p.add_argument("--poll-timeout", type=float, default=None, help="轮询总超时秒")
    args = p.parse_args(argv)

    example_by_pass: Seedance20ByPass = {
        "ratio": "16:9",
        "resolution": "720p",
        # "videos": [
        #     "https://jumuai.oss-cn-hangzhou.aliyuncs.com/skillsTmpFiles/1/video/2026/04/26/"
        #     "8891629038ae0d5e6c90ca48e1605addc4dfee09438912159c6fbe8b86ad5b32.mp4"
        # ],
        # "audios": [
        #     "https://jumuai.oss-cn-hangzhou.aliyuncs.com/skillsTmpFiles/1/audio/2026/04/27/"
        #     "815af17a9b3d59a06ddc8a0f2d54781ea983460ba0f5c49d968aa0e16d241494.mp3"
        # ],
    }
    example_images = [
        "https://jumuai.oss-cn-hangzhou.aliyuncs.com/skillsTmpFiles/1/image/2026/04/27/"
        "e29af67a08cdf9aeb9e1bc6d647a6e1dbe268f2dc01c8b40a271951ccd401175.png"
    ]
    pr = (args.prompt or "").strip() or (
        "口水鸡，红油与芝麻，川味凉菜\n"
        "根据参考图生成约2秒短视频：先特写鸡肉与红油质感，再展示整体摆盘；口播突出鲜香麻辣、开胃下饭。"
    )
    body = build_seedance20_payload(
        pr,
        duration=10,
        size="1920x1080",
        generate_audio=True,
        generate_mode=1,
        by_pass=example_by_pass,
        images=example_images,
    )
    if args.dry_run:
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return 0

    u = (args.url or "").strip() or None
    out = post_seedance20_and_wait(
        pr,
        duration=10,
        size="1920x1080",
        generate_audio=True,
        generate_mode=1,
        by_pass=example_by_pass,
        images=example_images,
        submit_url=u,
        poll=not args.no_poll,
        poll_interval_sec=args.poll_interval,
        poll_timeout_sec=args.poll_timeout,
    )
    show = {k: v for k, v in out.items() if k != "text"}
    if out.get("text") and not out.get("json"):
        show["text_preview"] = (out["text"] or "")[:800]
    print(json.dumps(show, ensure_ascii=False, indent=2))
    return 0 if out.get("ok") else 2


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
