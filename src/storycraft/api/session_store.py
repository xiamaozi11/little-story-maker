"""会话状态管理，供 REST API 与移动端使用。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from storycraft.config import OUTPUT_DIR


class SessionStore:
    """基于文件持久化的会话存储。"""

    def __init__(self, base_dir: str = OUTPUT_DIR):
        self.base_dir = Path(base_dir)

    def _session_path(self, session_id: str) -> Path:
        return self.base_dir / session_id / "session.json"

    def create(
        self,
        session_id: str,
        idea: str,
        character: str,
        num_scenes: int,
        scenes: List[Dict[str, Any]],
        character_description: str = "",
    ) -> Dict[str, Any]:
        session = {
            "session_id": session_id,
            "idea": idea,
            "character": character,
            "num_scenes": num_scenes,
            "scenes": scenes,
            "character_description": character_description,
            "story_generated": True,
            "story_confirmed": False,
            "image_style": None,
            "image_service": None,
            "image_size": None,
            "pdf_path": None,
            "created_at": datetime.now().isoformat(),
        }
        self.save(session_id, session)
        return session

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        path = self._session_path(session_id)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def save(self, session_id: str, session: Dict[str, Any]) -> None:
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        with open(self._session_path(session_id), "w", encoding="utf-8") as f:
            json.dump(session, f, ensure_ascii=False, indent=2)

    def update_scene(self, session_id: str, index: int, text: str) -> Dict[str, Any]:
        session = self.get(session_id)
        if session is None:
            raise KeyError(f"会话不存在: {session_id}")
        if index < 0 or index >= len(session["scenes"]):
            raise IndexError(f"场景索引越界: {index}")
        session["scenes"][index]["text"] = text
        session["scenes"][index].pop("text_en", None)
        self.save(session_id, session)
        return session

    def list_sessions(self) -> List[Dict[str, Any]]:
        results = []
        if not self.base_dir.exists():
            return results
        for d in sorted(self.base_dir.iterdir(), reverse=True):
            if d.is_dir() and (d / "session.json").exists():
                session = self.get(d.name)
                if session:
                    results.append(
                        {
                            "session_id": session["session_id"],
                            "character": session.get("character", ""),
                            "num_scenes": len(session.get("scenes", [])),
                            "has_images": bool(
                                session.get("scenes")
                                and "image_path" in session["scenes"][0]
                            ),
                            "created_at": session.get("created_at", ""),
                        }
                    )
        return results
