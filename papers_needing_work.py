import csv
import sys
import re
from collections import defaultdict

def analyze_csv(input_filepath):
    """
    Analyzes a CSV file to count rows with less than 2 confirmed reviewers
    for each unique value in the 'Pname' column.

    A confirmed reviewer is defined as a name in an 'E<number>name' column
    where the corresponding 'E<number>score' column does not contain "T".
    This analysis is now limited to rows where the 'Decision' column is
    either "RER" or "ERER".

    Args:
        input_filepath (str): The path to the input CSV file.
    """
    try:
        # Dictionary to store the count for each unique Pname
        # The key is the Pname, the value is the count of rows with < 2 confirmed reviewers
        low_reviewer_counts = defaultdict(int)
        total_paper_counts = defaultdict(int)
        tentative_reviewer_counts = defaultdict(int)
        missing_reviewer_counts = defaultdict(int)
        total_reviewer_counts = defaultdict(int)
        total_processed_rows = 0

        with open(input_filepath, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            header = next(reader)  # Read the header row

            # Find the indices of Pname, Decision, and all E<number>name/E<number>score columns
            s1_name_index = -1
            decision_index = -1
            reviewer_columns = [] # A list of tuples: (name_index, score_index)

            for i, column_name in enumerate(header):
                if column_name == 'Pname':
                    s1_name_index = i
                elif column_name == 'Decision':
                    decision_index = i
                elif re.match(r'E\d+name', column_name):
                    # Extract the number from the column name (e.g., 'E1name' -> '1')
                    number = re.search(r'E(\d+)name', column_name).group(1)
                    score_column = f'E{number}score'
                    try:
                        score_index = header.index(score_column)
                        reviewer_columns.append((i, score_index))
                    except ValueError:
                        # Skip if the corresponding score column is not found
                        continue

            if s1_name_index == -1:
                print("Error: The CSV file must contain an 'Pname' column.", file=sys.stderr)
                return
            if decision_index == -1:
                print("Error: The CSV file must contain a 'Decision' column.", file=sys.stderr)
                return

            # Process each row of the CSV file
            for row in reader:

                # Check the Decision column before processing the row
                decision_value = row[decision_index].strip()
                if decision_value not in ["RER", "ERER"]:
                    continue  # Skip this row if the decision is not RER or ERER

                s1_name_value = row[s1_name_index]
                if s1_name_value not in low_reviewer_counts:
                    total_paper_counts[s1_name_value] = 0
                    low_reviewer_counts[s1_name_value] = 0
                    tentative_reviewer_counts[s1_name_value] = 0
                    missing_reviewer_counts[s1_name_value] = 0
                    total_reviewer_counts[s1_name_value] = 0

                confirmed_reviewers = 0
                tentative_reviewers = 0

                # Iterate through all identified reviewer columns to count confirmed reviewers
                for name_idx, score_idx in reviewer_columns:
                    # Check if the name field is not empty and the score field does not contain "T"
                    if (row[name_idx].strip() != ''):
                        if ('T' == row[score_idx].strip()):
                            tentative_reviewers += 1
                        else:
                            confirmed_reviewers += 1

                # If the number of confirmed reviewers is less than 2, increment the counter
                missing_reviewer_counts[s1_name_value] += max(0, 2 - (confirmed_reviewers+tentative_reviewers))
                total_reviewer_counts[s1_name_value] += confirmed_reviewers
                tentative_reviewer_counts[s1_name_value] += tentative_reviewers
                total_paper_counts[s1_name_value] += 1
                if confirmed_reviewers < 2:
                    # print(f"{row[1]} does not have enough confirmed reviewers - {s1_name_value}")
                    low_reviewer_counts[s1_name_value] += 1

        # Write the results to standard output
        writer = csv.writer(sys.stdout)
        writer.writerow(['Primary', 'Papers Needing Reviewers', 'Total Papers', 'Tentative Reviewers', 'Missing Reviewers', 'Assigned Reviewers'])
        for s1_name, count in sorted(low_reviewer_counts.items()):
            writer.writerow([
                s1_name,
                count,
                total_paper_counts[s1_name],
                tentative_reviewer_counts[s1_name],
                missing_reviewer_counts[s1_name],
                total_reviewer_counts[s1_name],
            ])

    except FileNotFoundError:
        print(f"Error: The file at '{input_filepath}' was not found.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_csv.py <input_file_path.csv>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    analyze_csv(input_path)
