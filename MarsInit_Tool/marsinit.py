from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

from tkinter import Tk
from tkinter.filedialog import askdirectory
import os


RACK_POSITION = 14
DEALER_POSITION = 17
MAX_SEATS = 8
MAX_SPOTS = 8


@dataclass
class MarsInitConfig:
    seats: int
    seat_spots: List[int]


def normalize_spots(raw: str) -> List[int]:
    if raw is None:
        return []

    raw = raw.strip()
    if not raw:
        return []

    spots: List[int] = []
    for part in raw.split(","):
        value = part.strip()
        if not value:
            continue

        if not value.isdigit():
            raise ValueError(
                f"Invalid spot value: {value!r}. Use comma-separated integers like 1,2,3."
            )

        num = int(value)
        if num < 0 or num > MAX_SPOTS:
            raise ValueError(f"Invalid spot value: {num}. Spots must be between 0 and {MAX_SPOTS}.")

        spots.append(num)

    return sorted(set(spots))


def full_axis_universe() -> List[str]:
    return [f"{seat}.{spot}" for seat in range(0, MAX_SEATS + 1) for spot in range(0, MAX_SPOTS + 1)]


def seat_axes(seat_number: int, spots: List[int]) -> List[str]:
    return [f"{seat_number}.{spot}" for spot in spots]


def sort_axis(axis_values: List[str]) -> List[str]:
    return sorted(axis_values, key=lambda x: (int(x.split(".")[0]), int(x.split(".")[1])))


def format_axis_group(axis_values: List[str]) -> str:
    inner = ",".join(f"'{value}'" for value in axis_values)
    if inner:
        inner += ","
    return f"({inner})"


def format_numeric_group(value: int) -> str:
    return f"({value},)"


def build_group_priority(seats: int) -> str:
    values = [1, 1, 1, 0, 1]
    for _seat in range(4, seats + 1):
        values.append(1)
    values.append(0)
    return "[" + ", ".join(str(v) for v in values) + "]"


def build_axis_label(seats: int) -> str:
    labels = ["'1'", "'2'", "'3'", "'RACK'", "'DEALER'"]
    for seat in range(4, seats + 1):
        labels.append(f"'{seat}'")
    labels.append("'SPARE'")
    return "(" + ",".join(labels) + ")"


def build_mars_init(config: MarsInitConfig) -> str:
    if config.seats < 1 or config.seats > MAX_SEATS:
        raise ValueError(f"Seats must be between 1 and {MAX_SEATS}.")

    if not config.seat_spots:
        raise ValueError("At least one spot number must be entered.")

    used_axis: Set[str] = set()
    seat_groups = {}

    for seat in range(1, config.seats + 1):
        axes = seat_axes(seat, config.seat_spots)
        seat_groups[seat] = axes
        used_axis.update(axes)

    universe = set(full_axis_universe())
    spare = sort_axis(list(universe - used_axis))

    groups: List[str] = [
        format_axis_group(seat_groups.get(1, [])),
        format_axis_group(seat_groups.get(2, [])),
        format_axis_group(seat_groups.get(3, [])),
        format_numeric_group(RACK_POSITION),
        format_numeric_group(DEALER_POSITION),
    ]

    for seat in range(4, config.seats + 1):
        groups.append(format_axis_group(seat_groups.get(seat, [])))

    groups.append(format_axis_group(spare))

    axis_group_count = len(groups)
    axis_in_group = ", ".join(groups)
    group_priority = build_group_priority(config.seats)
    axis_label = build_axis_label(config.seats)

    # Each main section has its own line.
    # Each line except the last intentionally ends with two spaces before the newline.
    return (
        f"AxisGroupCount({axis_group_count})  \n"
        f"AxisInGroup([{axis_in_group}])  \n"
        f"GroupPriority({group_priority})  \n"
        f"AxisLabel{axis_label}"
    )

def prompt_output_folder(default_folder: Path) -> Path:
    print()
    print(f"Detected default output folder:")
    print(default_folder)
    
    use_default = prompt_yes_no("Use this folder? (y/n)")
    
    if use_default:
        return default_folder
        
    print()
    print("Select a folder to save to.")
    
    root = Tk()
    root.withdraw()
    
    selected = askdirectory(
        title = "Select Ouput Folder"
    )
    
    root.destroy()
    
    if not selected: 
        print()
        print("You didn't select a folder.")
        print("Using default. Saving to Desktop")
        return default_folder
        
    return Path(selected)

def default_output_filename(seats: int, spots: List[int]) -> str:
    spot_text = "".join(str(s) for s in spots)
    return f"{seats}seats_{spot_text}.txt"


def get_desktop_path() -> Path:
    """
    Find the user's Desktop safely.

    Why this exists:
    - Some PCs use a normal local Desktop:
      C:\\Users\\Name\\Desktop

    - Some company PCs redirect Desktop into OneDrive:
      C:\\Users\\Name\\OneDrive - Company\\Desktop

    This function checks common Windows locations without hardcoding a specific user
    or company folder name.
    """

    candidates: List[Path] = []

    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        candidates.append(Path(userprofile) / "Desktop")

    # OneDrive business accounts often use OneDriveCommercial.
    onedrive_commercial = os.environ.get("OneDriveCommercial")
    if onedrive_commercial:
        candidates.append(Path(onedrive_commercial) / "Desktop")

    # Personal or generic OneDrive path.
    onedrive = os.environ.get("OneDrive")
    if onedrive:
        candidates.append(Path(onedrive) / "Desktop")

    # Fallback based on Python's home path.
    candidates.append(Path.home() / "Desktop")

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    # Final fallback: user home folder.
    return Path.home()


def next_available_filename(folder: Path, filename: str) -> Path:
    base = Path(filename).stem
    suffix = Path(filename).suffix or ".txt"

    candidate = folder / f"{base}{suffix}"
    if not candidate.exists():
        return candidate

    counter = 2
    while True:
        candidate = folder / f"{base}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def safe_write_text(path: Path, text: str) -> bool:
    try:
        path.write_text(text, encoding="utf-8")
        return True
    except PermissionError:
        print()
        print(f"Permission denied while writing:")
        print(path)
        print("The file may be open, locked, or blocked by Windows permissions.")
        return False
    except OSError as exc:
        print()
        print(f"Unable to write file:")
        print(path)
        print(f"Reason: {exc}")
        return False


def prompt_int(prompt: str, min_value: int, max_value: int) -> int:
    while True:
        raw = input(prompt).strip()
        if not raw.isdigit():
            print(f"Please enter a whole number between {min_value} and {max_value}.")
            continue

        value = int(raw)
        if value < min_value or value > max_value:
            print(f"Please enter a whole number between {min_value} and {max_value}.")
            continue

        return value


def prompt_yes_no(prompt: str) -> bool:
    while True:
        raw = input(prompt).strip().lower()
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Please enter y or n.")


def prompt_spots(prompt: str) -> List[int]:
    while True:
        raw = input(prompt)
        try:
            return normalize_spots(raw)
        except ValueError as exc:
            print(exc)


def prompt_filename(default_name: str) -> str:
    raw = input("Press Enter to use default filename, or type a custom filename: ").strip()

    filename = raw or default_name

    if not filename.lower().endswith(".txt"):
        filename += ".txt"

    invalid_chars = '<>:"/\\|?*'
    for ch in invalid_chars:
        filename = filename.replace(ch, "_")

    return filename


def save_output(result: str, default_name: str) -> None:
    default_folder = get_desktop_path()
    Output_folder = prompt_output_folder(default_folder)
    
    print()
    print(f"Detected output folder: {output_folder}")
    print(f"Default output filename: {default_name}")

    filename = prompt_filename(default_name)
    target_path = output_folder / filename

    if target_path.exists():
        print()
        print(f"File already exists:")
        print(target_path)

        replace = prompt_yes_no("Replace existing file? (y/n): ")
        if not replace:
            target_path = next_available_filename(output_folder, filename)
            print(f"Creating new file instead: {target_path.name}")

    if not safe_write_text(target_path, result):
        print()
        print("Trying automatic rename...")
        retry_path = next_available_filename(output_folder, filename)
        if safe_write_text(retry_path, result):
            print(f"Saved to: {retry_path}")
        else:
            print("Save failed. Copy the output from the screen manually.")
        return

    print(f"Saved to: {target_path}")


def main():
    print("=== MarsInit Generator ===")
    print("This tool generates the MarsInit string for Holy Grail.")
    print("All active seats use the same spot pattern.")
    print()

    seats = prompt_int(f"Enter number of seats (1-{MAX_SEATS}): ", 1, MAX_SEATS)
    spots = prompt_spots("Enter spot numbers used by each active seat (example: 1,2,3): ")

    config = MarsInitConfig(seats=seats, seat_spots=spots)
    result = build_mars_init(config)

    print()
    print("=== Generated MarsInit ===")
    print()
    print(result)
    print()

    default_name = default_output_filename(seats, spots)

    if prompt_yes_no("Save output to file? (y/n): "):
        save_output(result, default_name)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled by user.")
    except Exception as exc:
        print(f"\nUnexpected error: {exc}")
        input("Press Enter to exit...")
