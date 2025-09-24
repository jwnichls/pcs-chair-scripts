# This script processes submission and email log data by
# orchestrating two other Python scripts.
#
# Usage:
# python process_data.py <date_to_filter> <submissions_csv_path> <email_log_csv_path>

import argparse
import subprocess
import csv
import os
import sys
from collections import Counter
import io

def main():
    """
    Main function to parse command-line arguments and run the data processing logic.
    """
    parser = argparse.ArgumentParser(description='Process submission and email log data.')
    parser.add_argument('date_to_filter', type=str, help='A date string to filter the email log file.')
    parser.add_argument('submissions_csv_path', type=str, help='Path to the submissions CSV file.')
    parser.add_argument('email_log_csv_path', type=str, help='Path to the email log CSV file.')

    args = parser.parse_args()

    # Get the directory of the current script to find the other scripts
    script_dir = os.path.dirname(os.path.abspath(__file__))

    try:
        # Step 1: Call analyze_reviewers.py and capture its stdout
        analyze_script_path = os.path.join(script_dir, "analyze_reviewers.py")
        reviewers_process = subprocess.run(
            [sys.executable, analyze_script_path, args.submissions_csv_path],
            check=True,  # This will raise an exception if the script fails
            capture_output=True,
            text=True
        )
        reviewers_output = reviewers_process.stdout
        
        # Step 2: Call extract_review_declines.py and capture its stdout
        extract_script_path = os.path.join(script_dir, "extract_review_declines.py")
        declines_process = subprocess.run(
            [sys.executable, extract_script_path, args.email_log_csv_path, args.date_to_filter],
            check=True,
            capture_output=True,
            text=True
        )
        declines_output = declines_process.stdout

        # Step 3: Process the output from both scripts
        
        # Read the reviewers data (names and counts) from stdout
        reviewer_counts = {}
        with io.StringIO(reviewers_output) as f:
            reader = csv.DictReader(f)
            for row in reader:
                reviewer_counts[row['name']] = int(row['count'])

        # Read the review declines data (names and submission IDs) from stdout
        declined_names = []
        with io.StringIO(declines_output) as f:
            reader = csv.DictReader(f)
            for row in reader:
                declined_names.append(row['Name'])

        # Use Counter to count occurrences of each name in the declines list
        declined_name_counts = Counter(declined_names)

# Step 4: Output the final results to stdout as a CSV
        found_matches = False
        writer = csv.DictWriter(sys.stdout, fieldnames=['name', 'declines_count', 'reviewer_count'])
        writer.writeheader()

        for name, count in declined_name_counts.items():
            # Check if the name exists in the reviewers data with a count > 0
            if reviewer_counts.get(name, 0) > 0:
                writer.writerow({
                    'name': name,
                    'declines_count': count,
                    'reviewer_count': reviewer_counts.get(name)
                })
                found_matches = True
        
        if not found_matches:
            print("No matching names found with a reviewer count greater than zero.")

    except FileNotFoundError as e:
        print(f"Error: A required script or file was not found. Please ensure all files exist. {e}")
    except subprocess.CalledProcessError as e:
        print(f"Error: A subprocess failed with a non-zero exit code.")
        print(f"Stderr: {e.stderr}")

if __name__ == "__main__":
    main()
