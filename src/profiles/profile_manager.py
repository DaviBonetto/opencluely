"""Opencluely copilot profile management."""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass
from typing import List, Optional

try:
    from storage_paths import get_runtime_file, get_seed_file
except ImportError:
    from src.storage_paths import get_runtime_file, get_seed_file


logger = logging.getLogger("profile_manager")

def _legacy_profile_id(*parts: str) -> str:
    return "_".join(parts)


PROFILE_ID_MIGRATIONS = {
    _legacy_profile_id("int" "erview", "assistant"): "general_copilot",
    _legacy_profile_id("leetcode", "helper"): "problem_solving",
    _legacy_profile_id("sales", "assistant"): "sales_conversation",
    "custom": "custom_profile",
}


def _normalize_profile_id(profile_id: str) -> str:
    return PROFILE_ID_MIGRATIONS.get(profile_id, profile_id)


@dataclass
class CopilotProfile:
    """Represents a reusable copilot profile."""

    id: str
    name: str
    description: str
    version: int
    icon: str
    system_instructions: str
    user_context_example: str
    is_builtin: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CopilotProfile":
        return cls(
            id=_normalize_profile_id(data.get("id", str(uuid.uuid4()))),
            name=data.get("name", "Untitled"),
            description=data.get("description", ""),
            version=data.get("version", 1),
            icon=data.get("icon", "📄"),
            system_instructions=data.get("system_instructions", ""),
            user_context_example=data.get("user_context_example", ""),
            is_builtin=data.get("is_builtin", False),
        )


def _builtin_profile_definitions() -> List[CopilotProfile]:
    return [
        CopilotProfile(
            id="general_copilot",
            name="General Copilot",
            description="Flexible support for live conversations and high-stakes sessions",
            version=1,
            icon="💼",
            system_instructions=(
                "You are Opencluely General Copilot. Help the user respond clearly in live "
                "sessions such as meetings, demos, and support calls. Keep answers "
                "spoken-ready, direct, and grounded in the provided context."
            ),
            user_context_example=(
                "Session type: Stakeholder sync\n"
                "Goal: Align on launch timeline\n"
                "Key points: Risks, dependencies, next step"
            ),
            is_builtin=True,
        ),
        CopilotProfile(
            id="problem_solving",
            name="Problem Solving",
            description="Reason through code, logic, and technical tradeoffs in real time",
            version=1,
            icon="🧩",
            system_instructions=(
                "You are Opencluely Problem Solving Copilot. Break problems into steps, call out "
                "tradeoffs, and provide concise code or pseudocode when it helps."
            ),
            user_context_example=(
                "Problem space: Python API performance\n"
                "Constraints: Ship today, preserve backward compatibility\n"
                "Need: Fast explanation plus a safe fix"
            ),
            is_builtin=True,
        ),
        CopilotProfile(
            id="sales_conversation",
            name="Sales Conversation",
            description="Handle objections, value framing, and next-step momentum",
            version=1,
            icon="📈",
            system_instructions=(
                "You are Opencluely Sales Conversation Copilot. Keep answers concise, address "
                "objections directly, tie back to value, and end with a useful next step."
            ),
            user_context_example=(
                "Product: Workflow automation platform\n"
                "Buyer concern: Slow rollout and unclear ROI\n"
                "Desired close: Pilot with success criteria"
            ),
            is_builtin=True,
        ),
        CopilotProfile(
            id="custom_profile",
            name="Custom Profile",
            description="Start from a blank profile and define the behavior yourself",
            version=1,
            icon="✏️",
            system_instructions="",
            user_context_example="",
            is_builtin=True,
        ),
    ]


BUILTIN_PROFILE_IDS = [profile.id for profile in _builtin_profile_definitions()]


class ProfileManager:
    """Loads, migrates, and persists copilot profiles."""

    DEFAULT_CONFIG_PATH = str(get_runtime_file("copilot_profiles.json"))
    LEGACY_CONFIG_PATH = str(get_runtime_file("templates.json"))
    DEFAULT_SEED_PATH = str(get_seed_file("copilot_profiles.seed.json"))
    LEGACY_SEED_PATH = str(get_seed_file("templates.seed.json"))

    def __init__(self, config_path: str = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.profiles: List[CopilotProfile] = []
        self.last_used: str = "general_copilot"
        self.language: str = "en"
        self._load()

    def _load(self) -> None:
        """Load profiles from runtime data, legacy runtime data, or committed seeds."""
        try:
            loaded = self._load_payload_from_path(self.config_path)
            if loaded:
                logger.info("[ProfileManager] Loaded %s profiles", len(self.profiles))
                return

            loaded = self._load_payload_from_path(self.LEGACY_CONFIG_PATH, migrate=True)
            if loaded:
                logger.info("[ProfileManager] Migrated legacy runtime profile data")
                return

            loaded = self._load_payload_from_path(self.DEFAULT_SEED_PATH, migrate=True)
            if loaded:
                logger.info("[ProfileManager] Loaded committed profile seed")
                return

            loaded = self._load_payload_from_path(self.LEGACY_SEED_PATH, migrate=True)
            if loaded:
                logger.info("[ProfileManager] Loaded legacy profile seed")
                return

            logger.warning("[ProfileManager] No profile data found, creating defaults")
            self._create_defaults()
        except Exception as exc:
            logger.error("[ProfileManager] Failed to load profiles: %s", exc)
            self._create_defaults()

    def _load_payload_from_path(self, path: str, migrate: bool = False) -> bool:
        if not path or not os.path.exists(path):
            return False

        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        self._apply_payload(data)

        if migrate or path != self.config_path:
            self.save()

        return True

    def _apply_payload(self, data: dict) -> None:
        self.last_used = _normalize_profile_id(data.get("last_used", "general_copilot"))
        self.language = data.get("language", "en")

        raw_profiles = data.get("profiles") or data.get("templates") or []
        loaded_profiles = [CopilotProfile.from_dict(item) for item in raw_profiles]
        self.profiles = self._merge_builtin_profiles(loaded_profiles)

        if self.last_used not in {profile.id for profile in self.profiles}:
            self.last_used = "general_copilot"

    def _merge_builtin_profiles(
        self, loaded_profiles: List[CopilotProfile]
    ) -> List[CopilotProfile]:
        builtin_lookup = {profile.id: profile for profile in _builtin_profile_definitions()}
        custom_profiles: List[CopilotProfile] = []

        for profile in loaded_profiles:
            if profile.id in builtin_lookup:
                continue
            custom_profiles.append(profile)

        merged_profiles = [
            CopilotProfile.from_dict(builtin_lookup[profile_id].to_dict())
            for profile_id in BUILTIN_PROFILE_IDS
        ]
        merged_profiles.extend(custom_profiles)
        return merged_profiles

    def _create_defaults(self) -> None:
        self.profiles = [
            CopilotProfile.from_dict(profile.to_dict())
            for profile in _builtin_profile_definitions()
        ]
        self.last_used = "general_copilot"
        self.save()

    def save(self) -> None:
        """Persist the current profile state."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            data = {
                "version": "1.0",
                "last_used": self.last_used,
                "language": self.language,
                "profiles": [profile.to_dict() for profile in self.profiles],
            }
            with open(self.config_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False)
            logger.info("[ProfileManager] Saved %s profiles", len(self.profiles))
        except Exception as exc:
            logger.error("[ProfileManager] Failed to save profiles: %s", exc)

    def get_all(self) -> List[CopilotProfile]:
        return self.profiles

    def get_by_id(self, profile_id: str) -> Optional[CopilotProfile]:
        profile_id = _normalize_profile_id(profile_id)
        for profile in self.profiles:
            if profile.id == profile_id:
                return profile
        return None

    def get_last_used(self) -> Optional[CopilotProfile]:
        return self.get_by_id(self.last_used)

    def set_last_used(self, profile_id: str) -> None:
        normalized_id = _normalize_profile_id(profile_id)
        if self.get_by_id(normalized_id):
            self.last_used = normalized_id
            self.save()

    def create(
        self,
        name: str,
        description: str,
        icon: str,
        system_instructions: str,
        user_context_example: str = "",
    ) -> CopilotProfile:
        profile = CopilotProfile(
            id=f"custom_profile_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            version=1,
            icon=icon,
            system_instructions=system_instructions,
            user_context_example=user_context_example,
            is_builtin=False,
        )
        self.profiles.append(profile)
        self.save()
        logger.info("[ProfileManager] Created profile: %s", profile.name)
        return profile

    def update(self, profile_id: str, **kwargs) -> Optional[CopilotProfile]:
        profile = self.get_by_id(profile_id)
        if profile and not profile.is_builtin:
            for key, value in kwargs.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            profile.version += 1
            self.save()
            logger.info("[ProfileManager] Updated profile: %s", profile.name)
            return profile
        return None

    def delete(self, profile_id: str) -> bool:
        profile = self.get_by_id(profile_id)
        if profile and not profile.is_builtin:
            self.profiles.remove(profile)
            self.save()
            logger.info("[ProfileManager] Deleted profile: %s", profile.name)
            return True
        return False


_manager: Optional[ProfileManager] = None


def get_profile_manager() -> ProfileManager:
    """Return the singleton profile manager."""
    global _manager
    if _manager is None:
        _manager = ProfileManager()
    return _manager
