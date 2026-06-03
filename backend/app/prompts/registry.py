"""Prompt registry for TopicAI v4.0.

Manages prompt versioning: scanning, loading, and version resolution.
Structure: prompts/{module}/v{N}/system.md (required), user.md (optional).
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PROMPTS_ROOT = Path(__file__).resolve().parent


class PromptRegistry:
    """Prompt version management registry.

    Scans the prompts directory structure and provides
    version-queryable prompt loading.
    """

    _cache: dict[str, dict[str, str]] = {}

    @classmethod
    def _get_root(cls) -> Path:
        return _PROMPTS_ROOT

    @classmethod
    def list_modules(cls) -> set[str]:
        """List all available prompt modules.

        Returns:
            Set of module names.
        """
        root = cls._get_root()
        modules = set()
        for item in root.iterdir():
            if item.is_dir() and not item.name.startswith("_") and not item.name.startswith("."):
                # Check it has version subdirectories
                versions = [d for d in item.iterdir() if d.is_dir() and d.name.startswith("v")]
                if versions:
                    modules.add(item.name)
        return modules

    @classmethod
    def list_versions(cls, module: str) -> list[str]:
        """List all available versions for a module.

        Args:
            module: Module name.

        Returns:
            Sorted list of version strings (e.g., ['v1', 'v2']).
        """
        module_dir = cls._get_root() / module
        if not module_dir.exists():
            return []
        versions = []
        for item in module_dir.iterdir():
            if item.is_dir() and item.name.startswith("v"):
                versions.append(item.name)
        return sorted(versions)

    @classmethod
    def get_latest_version(cls, module: str) -> str:
        """Get the latest version for a module.

        Args:
            module: Module name.

        Returns:
            Latest version string.

        Raises:
            FileNotFoundError: If module has no versions.
        """
        versions = cls.list_versions(module)
        if not versions:
            raise FileNotFoundError(f"No versions found for module: {module}")
        return versions[-1]

    @classmethod
    def get_prompt(
        cls, module: str, version: str = "latest", file_name: str = "system.md"
    ) -> str:
        """Load a prompt file.

        Args:
            module: Module name.
            version: Version string or 'latest'.
            file_name: Prompt file name (default: system.md).

        Returns:
            Prompt file contents as string.

        Raises:
            FileNotFoundError: If module, version, or file not found.
        """
        if version == "latest":
            version = cls.get_latest_version(module)

        prompt_path = cls._get_root() / module / version / file_name
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {module}/{version}/{file_name}"
            )

        if prompt_path.suffix == ".md":
            return prompt_path.read_text(encoding="utf-8")
        return prompt_path.read_bytes().decode("utf-8")

    @classmethod
    def validate_version(cls, module: str, version: str) -> bool:
        """Validate that a version exists for a module.

        Args:
            module: Module name.
            version: Version string.

        Returns:
            True if valid, False otherwise.
        """
        if not version.startswith("v"):
            return False
        module_dir = cls._get_root() / module
        version_dir = module_dir / version
        system_file = version_dir / "system.md"
        return version_dir.exists() and system_file.exists()
