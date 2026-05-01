import logging
import os
import sys

from datetime import datetime, timedelta

try:
    from cls_env_config import EnvConfigSingleton as EnvConfig
    from cls_env_tools import EnvTools
    from cls_db_tools import DbRepositorySingleton
except ImportError as e:
    logging.error(f"Error importing required modules: {e}")
    sys.exit(1)


def ensure_sunday(date_str: str) -> str:
    """
    Verify the date is a Sunday; if not, adjust to the nearest tournament Sunday.
    Tournament runs Friday-Sunday:
    - If the date is Mon-Thu, returns the previous Sunday.
    - If the date is Fri-Sat, returns the upcoming Sunday.
    - If the date is already Sunday, returns it as-is.
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = dt.weekday()  # Mon=0, Tue=1, ..., Sun=6

    if weekday == 6:  # Already Sunday
        return date_str

    if weekday <= 3:  # Monday (0) through Thursday (3)
        days_back = (weekday + 1) % 7
        sunday = dt - timedelta(days=days_back)
    else:  # Friday (4), Saturday (5)
        days_forward = 6 - weekday
        sunday = dt + timedelta(days=days_forward)

    return sunday.strftime("%Y-%m-%d")


def get_friday_date(sunday_str: str) -> str:
    """Return the Friday before the given Sunday date."""
    sunday = datetime.strptime(sunday_str, "%Y-%m-%d")
    friday = sunday - timedelta(days=2)
    return friday.strftime("%Y-%m-%d")


def prompt_for_date() -> str:
    """Prompt the user for a date and convert it to the tournament Sunday."""
    while True:
        raw = input("\nEnter tournament date (YYYY-MM-DD): ").strip()
        if not raw:
            print("No date entered. Exiting.")
            sys.exit(0)

        try:
            datetime.strptime(raw, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            continue

        sunday_date = ensure_sunday(raw)

        if raw != sunday_date:
            day_name = datetime.strptime(raw, "%Y-%m-%d").strftime("%A")
            print(f"  {raw} is a {day_name} — adjusted to Sunday {sunday_date}")
        else:
            print(f"  Confirmed Sunday: {sunday_date}")

        return sunday_date


def prompt_for_scores(db_repository, sunday_date: str, friday_date: str):
    """
    Interactively prompt for player name and score pairs.
    Type 'done' or press Enter on an empty line to finish.
    """
    entries = []

    print(f"\nEntering scores for weekend: {sunday_date}")
    print("Type player name and score (e.g. 'Dewey 5054'), or 'done' to finish.\n")

    while True:
        raw = input("  Player Score: ").strip()

        if not raw or raw.lower() == "done":
            break

        parts = raw.rsplit(maxsplit=1)
        if len(parts) != 2 or not parts[1].isdigit():
            print("    ⚠ Expected format: PlayerName Score (e.g. 'Dewey 5054')")
            continue

        player_tag, score_str = parts
        score = int(score_str)

        player_id = db_repository.get_player_id(player_tag)
        if player_id is None:
            print(f"    Player '{player_tag}' not found. Creating new player with start date {friday_date}...")
            player_id = db_repository.get_player_id_create_if_new(player_tag, friday_date)

        if player_id is None:
            print(f"    ✗ Failed to create player '{player_tag}'. Skipping.")
            continue

        db_repository.upsert_weekend_player_score(sunday_date, player_id, score)
        entries.append((player_tag, score, player_id))
        print(f"    ✓ {player_tag} (ID: {player_id}) — score: {score}")

    return entries


def main():
    env_config = EnvConfig()
    repo_root = EnvTools.find_repo_root()

    db_path_config = env_config.merged_config['constants']['db_path']
    db_path = db_path_config.replace("{repo_root}", str(repo_root))

    db_repository = DbRepositorySingleton(db_path)

    try:
        while True:
            sunday_date = prompt_for_date()
            friday_date = get_friday_date(sunday_date)

            entries = prompt_for_scores(db_repository, sunday_date, friday_date)

            if entries:
                print(f"\n--- Saved {len(entries)} score(s) for {sunday_date} ---")
                for player_tag, score, player_id in entries:
                    print(f"  {player_tag} (ID: {player_id}): {score}")

                print("\nUpdating ranks...")
                db_repository.update_ranks_for_weekend_date(sunday_date)
                print("Done.")
            else:
                print("\nNo scores entered.")

            again = input("\nEnter scores for another weekend? (y/n): ").strip().lower()
            if again != "y":
                break

    except KeyboardInterrupt:
        print("\n\nCancelled.")
    finally:
        db_repository.cleanup()

if __name__ == "__main__":
    main()