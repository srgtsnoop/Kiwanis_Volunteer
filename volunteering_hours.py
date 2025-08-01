import csv
import os
from datetime import datetime

CSV_FILE = "data/volunteer_hours.csv"
FIELDNAMES = ["Date", "Volunteer Name", "Event", "Start Time", "End Time", "Total Hours", "Notes"]

def ensure_csv_exists():
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()

def log_hours():
    print("\n--- Log Volunteer Hours ---")
    name = input("Volunteer Name: ").strip()
    event = input("Event/Task: ").strip()
    date_str = input("Date (YYYY-MM-DD) [Leave blank for today]: ").strip()
    start = input("Start Time (HH:MM in 24-hr): ").strip()
    end = input("End Time (HH:MM in 24-hr): ").strip()
    notes = input("Optional Notes: ").strip()

    try:
        date = date_str if date_str else datetime.today().strftime('%Y-%m-%d')
        start_dt = datetime.strptime(f"{date} {start}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date} {end}", "%Y-%m-%d %H:%M")
        total_hours = round((end_dt - start_dt).seconds / 3600, 2)
    except Exception as e:
        print("❌ Error with date/time format:", e)
        return

    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writerow({
            "Date": date,
            "Volunteer Name": name,
            "Event": event,
            "Start Time": start,
            "End Time": end,
            "Total Hours": total_hours,
            "Notes": notes
        })

    print(f"✅ Logged {total_hours} hours for {name} on {date}.")

def log_hours_bulk():
    print("\n--- Bulk Log Volunteer Hours ---")
    event = input("Event/Task: ").strip()
    date_str = input("Date (YYYY-MM-DD) [Leave blank for today]: ").strip()
    start = input("Start Time (HH:MM in 24-hr): ").strip()
    end = input("End Time (HH:MM in 24-hr): ").strip()
    notes = input("Optional Notes: ").strip()
    names_input = input("Volunteer Names (comma separated): ").strip()
    names = [name.strip() for name in names_input.split(",") if name.strip()]

    if not names:
        print("❌ No volunteer names entered.")
        return

    try:
        date = date_str if date_str else datetime.today().strftime('%Y-%m-%d')
        start_dt = datetime.strptime(f"{date} {start}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date} {end}", "%Y-%m-%d %H:%M")
        total_hours = round((end_dt - start_dt).seconds / 3600, 2)
    except Exception as e:
        print("❌ Error with date/time format:", e)
        return

    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        for name in names:
            writer.writerow({
                "Date": date,
                "Volunteer Name": name,
                "Event": event,
                "Start Time": start,
                "End Time": end,
                "Total Hours": total_hours,
                "Notes": notes
            })
            print(f"✅ Logged {total_hours} hours for {name} on {date}.")

def view_entries():
    print("\n--- All Volunteer Entries ---")
    if not os.path.exists(CSV_FILE):
        print("No entries yet.")
        return
    with open(CSV_FILE, newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            print(f"{row['Date']} | {row['Volunteer Name']} | {row['Event']} | {row['Total Hours']} hrs")

def summary():
    print("\n--- Volunteer Summary ---")
    totals = {}
    if not os.path.exists(CSV_FILE):
        print("No entries yet.")
        return
    with open(CSV_FILE, newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row["Volunteer Name"]
            hours = float(row["Total Hours"])
            totals[name] = totals.get(name, 0) + hours
    for name, hours in totals.items():
        print(f"{name}: {hours:.2f} hours")

def main():
    ensure_csv_exists()
    while True:
        print("\n=== Volunteer Tracker ===")
        print("1. Log Hours")
        print("2. Bulk Log Hours")
        print("3. View All Entries")
        print("4. View Summary")
        print("5. Exit")
        choice = input("Choose an option: ").strip()
        if choice == '1':
            log_hours()
        elif choice == '2':
            log_hours_bulk()
        elif choice == '3':
            view_entries()
        elif choice == '4':
            summary()
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice.")

if __name__ == "__main__":
    main()
