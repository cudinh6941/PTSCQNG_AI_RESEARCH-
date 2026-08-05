"""
Sync Prompts từ Obsidian Vault vào Code.

Script này đọc prompt notes từ Obsidian vault và show ra console
để developer copy/update vào code.

Usage:
    python scripts/sync_prompts_from_obsidian.py

Obsidian Vault Path được lấy từ .env (OBSIDIAN_VAULT_PATH)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def read_obsidian_prompts(vault_path: str) -> list[dict]:
    """Đọc tất cả prompt notes từ Obsidian vault."""
    prompts_dir = Path(vault_path) / "Lab&Research" / "Prompts"

    if not prompts_dir.exists():
        print(f"❌ Prompts directory not found: {prompts_dir}")
        return []

    prompts = []
    for md_file in prompts_dir.glob("*.md"):
        if md_file.name.startswith("_"):
            continue

        content = md_file.read_text(encoding="utf-8")

        # Parse frontmatter
        frontmatter = {}
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        frontmatter[key.strip()] = val.strip()

        prompts.append({
            "file": md_file.name,
            "frontmatter": frontmatter,
            "content": content,
        })

    return prompts


def main():
    """Main entry point."""
    from core.common.config import settings

    vault_path = settings.obsidian_vault_path
    print(f"📖 Reading prompts from: {vault_path}")
    print("=" * 60)

    prompts = read_obsidian_prompts(vault_path)

    if not prompts:
        print("📝 Chưa có prompt nào trong Obsidian.")
        print(f"   Tạo prompt mới tại: {vault_path}/Lab&Research/Prompts/")
        print("   Sử dụng template: Tpl_Prompt.md")
        return

    for p in prompts:
        name = p["frontmatter"].get("name", p["file"])
        status = p["frontmatter"].get("status", "Unknown")
        agent = p["frontmatter"].get("linked_agent", "N/A")

        print(f"\n📝 {name}")
        print(f"   Status: {status} | Agent: {agent}")
        print(f"   File: {p['file']}")
        print("-" * 40)

    print(f"\n✅ Tìm thấy {len(prompts)} prompts trong Obsidian vault.")
    print("💡 Copy prompt content vào agents/*/prompts.py tương ứng.")


if __name__ == "__main__":
    main()
