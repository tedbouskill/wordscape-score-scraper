"""
Manage Team Players
===================
Interactive CLI tool to maintain the team roster in the players table.

Usage:
    python manage_team_players.py

Workflow:
    1. Prompts for player tags one at a time (Enter on empty line to finish).
    2. For each entered tag:
       - If the player doesn't exist → creates them with start_date = next Friday.
       - If the player exists but is not on the team → re-activates them.
    3. Any current on_team players NOT in the entered list are removed:
       - on_team set to 0
       - leave_date set to the last weekend_date where they scored points.
    4. Prints a summary of all changes.
"""

import logging
import sys

from datetime import date, datetime, timedelta

try:
    from cls_env_config import EnvConfigSingleton as EnvConfig
    from cls_env_tools import EnvTools
    from cls_db_tools import DbRepositorySingleton
except ImportError as e:
    logging.error(f"Error importing required modules: {e}")
    sys.exit(1)


# ── helpers ──────────────────────────────────────────────────────────────────

def compute_next_friday() -> str:
    """Return the next upcoming Friday as YYYY-MM-DD.

    If today *is* Friday the tournament hasn't started yet, so we return today.
    Otherwise we advance to the next Friday.
    """
    today = date.today()
    days_ahead = (4 - today.weekday()) % 7  # Monday=0 … Friday=4
    if days_ahead == 0 and today.weekday() == 4:
        # Today is Friday — use it
        return today.strftime("%Y-%m-%d")
    if days_ahead == 0:
        days_ahead = 7
    next_friday = today + timedelta(days=days_ahead)
    return next_friday.strftime("%Y-%m-%d")


def get_last_scored_weekend(db_conn, player_id: int) -> str | None:
    """Return the most recent weekend_date where the player scored > 0,
    or None if they have no scoring records."""
    cursor = db_conn.cursor()
    cursor.execute(
        "SELECT MAX(weekend_date) FROM tournament_results "
        "WHERE player_id = ? AND score > 0",
        (player_id,),
    )
    row = cursor.fetchone()
    return row[0] if row and row[0] else None


def set_player_off_team_with_date(db_conn, player_id: int, leave_date: str):
    """Set on_team = 0 and leave_date to a specific date."""
    cursor = db_conn.cursor()
    cursor.execute(
        "UPDATE players SET on_team = 0, leave_date = ? WHERE id = ?",
        (leave_date, player_id),
    )
    db_conn.commit()


# ── input collection ─────────────────────────────────────────────────────────

def prompt_for_player_tags() -> list[str]:
    """Interactively collect player tags from the user.

    Returns a deduplicated list of tags in the order they were entered.
    """
    tags: list[str] = []
    seen: set[str] = set()

    print("\n── Manage Team Players ─────────────────────────")
    print("Enter each player tag and press Enter.")
    print("Press Enter on an empty line when done.\n")

    while True:
        raw = input("  Player tag: ").strip()
        if not raw:
            break

        key = raw.lower()
        if key in seen:
            print(f"    ⚠  '{raw}' already entered — skipping duplicate.")
            continue

        seen.add(key)
        tags.append(raw)

    return tags


# ── main logic ───────────────────────────────────────────────────────────────

def main():
    # ── initialise ───────────────────────────────────────────────────────
    env_config = EnvConfig()
    repo_root = EnvTools.find_repo_root()

    db_path_config = env_config.merged_config["constants"]["db_path"]
    db_path = db_path_config.replace("{repo_root}", str(repo_root))

    db_repository = DbRepositorySingleton(db_path)
    db_conn = db_repository.connection  # direct sqlite3 connection for custom queries

    friday_date = compute_next_friday()

    # ── collect input ────────────────────────────────────────────────────
    entered_tags = prompt_for_player_tags()

    if not entered_tags:
        print("\nNo player tags entered. Nothing to do.")
        return

    print(f"\n  Entered {len(entered_tags)} player(s): {', '.join(entered_tags)}")
    print(f"  Next Friday (for new players): {friday_date}\n")

    # ── reconcile entered tags against the database ──────────────────────
    added: list[str] = []        # brand-new players
    reactivated: list[str] = []  # existing players put back on team

    entered_keys: set[str] = set()  # lowercase keys for later comparison

    for tag in entered_tags:
        entered_keys.add(tag.lower())

        player_id = db_repository.get_player_id(tag)

        if player_id is None:
            # New player — create with next Friday as start_date
            db_repository.get_player_id_create_if_new(tag, friday_date)
            added.append(tag)
            print(f"  ✚  Added new player '{tag}' (start_date={friday_date})")
        else:
            # Player exists — make sure they are on the team
            # get_team_members returns (id, player_tag, is_active) for on_team=1
            # We need a quick check whether this player is already on_team
            cursor = db_conn.cursor()
            cursor.execute("SELECT on_team FROM players WHERE id = ?", (player_id,))
            row = cursor.fetchone()
            if row and row[0] != 1:
                db_repository.set_player_on_team(player_id)
                reactivated.append(tag)
                print(f"  ↺  Reactivated '{tag}' (on_team=1, leave_date cleared)")
            else:
                print(f"  ✓  '{tag}' already on team")

    # ── deactivate players no longer on the team ─────────────────────────
    removed: list[tuple[str, str]] = []  # (tag, leave_date)

    current_team = db_repository.get_team_members()  # list of (id, player_tag, is_active)

    for player_id, player_tag, _is_active in current_team:
        if player_tag.lower() not in entered_keys:
            last_weekend = get_last_scored_weekend(db_conn, player_id)
            leave_date = last_weekend if last_weekend else date.today().strftime("%Y-%m-%d")

            set_player_off_team_with_date(db_conn, player_id, leave_date)
            removed.append((player_tag, leave_date))
            print(f"  ✖  Removed '{player_tag}' (on_team=0, leave_date={leave_date})")

    # ── summary ──────────────────────────────────────────────────────────
    print("\n── Summary ─────────────────────────────────────")
    print(f"  Added:       {len(added)}")
    if added:
        for t in added:
            print(f"               + {t}")
    print(f"  Reactivated: {len(reactivated)}")
    if reactivated:
        for t in reactivated:
            print(f"               ↺ {t}")
    print(f"  Removed:     {len(removed)}")
    if removed:
        for t, d in removed:
            print(f"               ✖ {t}  (leave_date={d})")
    print(f"  Unchanged:   {len(entered_tags) - len(added) - len(reactivated)}")
    print("────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
