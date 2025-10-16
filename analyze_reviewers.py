import csv
import sys
import re
from collections import Counter

def analyze_reviewers(file_path):
    """
    Reads a CSV file, collects values from 'Reviewer 1', 'Reviewer 2', and 'Reviewer 3'
    columns, and any columns matching the pattern 'E<number>name'. It handles
    comma-separated lists, and prints a single, combined, and sorted list
    of unique values and their counts, where the count from the static columns
    is subtracted from the count of the dynamic columns.

    Args:
        file_path (str): The path to the CSV file.
    """
    all_reviewers = []
    all_e_reviewers = []
    static_columns_to_analyze = ["Reviewer 1", "Reviewer 2", "Reviewer 3"]

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Dynamically find columns that match the E<number>name pattern
            e_columns_to_analyze = [col for col in reader.fieldnames if re.match(r'E\d+name', col)]

            # Combine all columns to check for existence
            all_required_columns = static_columns_to_analyze + e_columns_to_analyze
            if not all(col in reader.fieldnames for col in all_required_columns):
                missing_cols = [col for col in all_required_columns if col not in reader.fieldnames]
                print(f"Error: The following required columns are missing from the CSV file: {', '.join(missing_cols)}")
                return

            # Iterate over each row in the CSV file
            for row in reader:
                if row.get("Decision", "") != "RER" and row.get("Decision", "") != "ERER":
                    continue

                # Process static Reviewer columns
                for column in static_columns_to_analyze:
                    value = row.get(column, "").strip()
                    if value:
                        # Split by comma and extend the list
                        reviewers_in_cell = [name.strip() for name in value.split(',')]
                        all_reviewers.extend(reviewers_in_cell)

                # Process E<number>name columns
                for column in e_columns_to_analyze:
                    value = row.get(column, "").strip()
                    if value:
                        # Split by comma and extend the list
                        e_reviewers_in_cell = [name.strip() for name in value.split(',')]
                        all_e_reviewers.extend(e_reviewers_in_cell)

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

    # Use a Counter to get the unique values and their counts for both groups
    reviewer_counts = Counter(all_reviewers)
    e_reviewer_counts = Counter(all_e_reviewers)

    # Subtract the reviewer counts from the e-reviewer counts
    final_counts = reviewer_counts
    final_counts.subtract(e_reviewer_counts)

    # Print the results in CSV format
    if final_counts:
        print("name,count")
        # Sort the items (name, count) alphabetically by name
        sorted_reviewers = sorted(final_counts.items())
        for reviewer, count in sorted_reviewers:
            # Use double quotes to handle names with commas if they exist
            print(f'"{reviewer}",{count}')
    else:
        print("No reviewer data found to combine.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reviewer_analysis.py <path_to_csv_file>")
        sys.exit(1)

    csv_file_path = sys.argv[1]
    analyze_reviewers(csv_file_path)
