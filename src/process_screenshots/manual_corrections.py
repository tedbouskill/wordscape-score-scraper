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


<<<<<<< HEAD
def ensure_sunday(date_str: str) -> str:
=======
# Adding a weekend date
<<<<<<< HEAD
weekend_date = "2025-02-23"
if weekend_date not in weekend_data:
    weekend_data[weekend_date] = set()  # Create an empty set for the weekend date

=======
weekend_date = "2025-07-27"
if weekend_date not in weekend_data:
    weekend_data[weekend_date] = set()  # Create an empty set for the weekend date

weekend_data[weekend_date].add(("loulou", 1901))

>>>>>>> bc82a28aaf306b45a51bca175410bffb23322f53
#weekend_data[weekend_date].add(("Nirazz", 94))
#weekend_data[weekend_date].add(("trrr", 22))
#weekend_data[weekend_date].add(("Punches616", 0))
#weekend_data[weekend_date].add(("vfo", 78))
#weekend_data[weekend_date].add(("justme", 43))
<<<<<<< HEAD
#weekend_data[weekend_date].add(("cariann", 0))
=======
#weekend_data[weekend_date].add(("cariann", 1045))
>>>>>>> bc82a28aaf306b45a51bca175410bffb23322f53
#weekend_data[weekend_date].add(("jon", 0))
#weekend_data[weekend_date].add(("Da'man", 57))
#weekend_data[weekend_date].add(("val", 0))
#weekend_data[weekend_date].add(("Hobbes", 0))
#weekend_data[weekend_date].add(("Stormy", 0))
<<<<<<< HEAD
weekend_data[weekend_date].add(("fin", 3145))
=======
#weekend_data[weekend_date].add(("fin", 3145))
#weekend_data[weekend_date].add(("Weeminx", 15005))
#weekend_data[weekend_date].add(("Dewey", 5054))
#weekend_data[weekend_date].add(("JoCo", 4998))
#weekend_data[weekend_date].add(("Sienna", 4819))
#weekend_data[weekend_date].add(("Siley", 3796))
#weekend_data[weekend_date].add(("Mar", 3732))
#weekend_data[weekend_date].add(("Jay", 3661))
#weekend_data[weekend_date].add(("Gardener", 3269))
#weekend_data[weekend_date].add(("Suriel", 3029))
#weekend_data[weekend_date].add(("Burpalot", 2894))
#weekend_data[weekend_date].add(("Laura", 2874))
#weekend_data[weekend_date].add(("Pop", 2693))
#weekend_data[weekend_date].add(("Grandmaphyll", 2392))
#weekend_data[weekend_date].add(("Springerpup", 2193))
#weekend_data[weekend_date].add(("ZMewis", 1819))
#weekend_data[weekend_date].add(("FleurDeLys", 1711))
#weekend_data[weekend_date].add(("Mary", 1653))
#weekend_data[weekend_date].add(("Marbl", 1566))
#weekend_data[weekend_date].add(("Tedbilly", 1470))
#weekend_data[weekend_date].add(("Stranger", 1398))
#weekend_data[weekend_date].add(("Kay", 1374))
#weekend_data[weekend_date].add(("Spudly", 1343))
#weekend_data[weekend_date].add(("Mike", 1302))
#weekend_data[weekend_date].add(("Fin", 1184))
#weekend_data[weekend_date].add(("Wilbur", 1106))
#weekend_data[weekend_date].add(("Quinn", 1006))
#weekend_data[weekend_date].add(("Cheech", 920))
#weekend_data[weekend_date].add(("Maggie", 900))
#weekend_data[weekend_date].add(("justme", 883))
#weekend_data[weekend_date].add(("Ami", 665))
#weekend_data[weekend_date].add(("Trick", 664))
#weekend_data[weekend_date].add(("Soggy", 619))
#weekend_data[weekend_date].add(("Hunny", 423))
#weekend_data[weekend_date].add(("Murphy", 359))
#weekend_data[weekend_date].add(("Nvk", 334))
#weekend_data[weekend_date].add(("Akp", 271))
#weekend_data[weekend_date].add(("Giddyupjenny", 219))
>>>>>>> bc82a28aaf306b45a51bca175410bffb23322f53

def get_weekend_dates(file_date_str: str) -> tuple:
>>>>>>> origin/main
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


<<<<<<< HEAD
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
=======
        for player_tag, score in tuples:
<<<<<<< HEAD
            player_id = db_repository.get_player_id(player_tag)
            if player_id is None:
                print(f"Player ID not found for tag: {player_tag}, adding for weekend date: {weekend_date} with start date: {friday_date}")
                db_repository.update_player_start_date(player_tag, friday_date)

            print(f"Insert Player ID: {player_id}, Score: {score} for weekend date: {weekend_date}")
=======
>>>>>>> origin/main
            player_id = db_repository.get_player_id_create_if_new(player_tag, friday_date)

<<<<<<< HEAD
        if player_id is None:
            print(f"    ✗ Failed to create player '{player_tag}'. Skipping.")
            continue
=======
            db_repository.update_player_start_date(player_tag.lower(), friday_date)
            print(f"Insert Player {player_tag} ID: {player_id}, Score: {score} for weekend date: {weekend_date}")
>>>>>>> bc82a28aaf306b45a51bca175410bffb23322f53
            db_repository.upsert_weekend_player_score(sunday_date, player_id, score)
>>>>>>> origin/main

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