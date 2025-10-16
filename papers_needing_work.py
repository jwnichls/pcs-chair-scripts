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
        overcommitted_reviewer_counts = defaultdict(int)
        pc_completed_reviews_counts = defaultdict(int)
        completed_reviews_counts = defaultdict(int)
        reviewer_subcommittee = defaultdict(str)
        total_processed_rows = 0

        with open(input_filepath, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            header = next(reader)  # Read the header row

            # Find the indices of Pname, Decision, and all E<number>name/E<number>score columns
            s1_name_index = -1
            decision_index = -1
            subcommittee_index = -1
            pc_columns = [] # A list of tuples: (name_index, score_index)
            reviewer_columns = [] # A list of tuples: (name_index, score_index)

            for i, column_name in enumerate(header):
                if column_name == 'Pname':
                    s1_name_index = i
                elif column_name == 'Decision':
                    decision_index = i
                elif column_name == 'Subcommittee':
                    subcommittee_index = i
                elif re.match(r'S\d+name', column_name):
                    # Extract the number from the column name (e.g., 'E1name' -> '1')
                    number = re.search(r'S(\d+)name', column_name).group(1)
                    score_column = f'S{number}score'
                    try:
                        score_index = header.index(score_column)
                        pc_columns.append((i, score_index))
                    except ValueError:
                        # Skip if the corresponding score column is not found
                        continue
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
                    overcommitted_reviewer_counts[s1_name_value] = 0
                    pc_completed_reviews_counts[s1_name_value] = 0
                    completed_reviews_counts[s1_name_value] = 0
                    reviewer_subcommittee[s1_name_value] = row[subcommittee_index]
                    

                confirmed_reviewers = 0
                tentative_reviewers = 0
                completed_reviewers = 0
                pc_completed = 0

                # Iterate through all identified reviewer columns to count confirmed reviewers
                for name_idx, score_idx in reviewer_columns:
                    # Check if the name field is not empty and the score field does not contain "T"
                    if (row[name_idx].strip() != ''):
                        score = row[score_idx].strip()
                        if ('T' == score):
                            tentative_reviewers += 1
                        else:
                            confirmed_reviewers += 1
                            
                            if re.match(r'\d+\.\d+', score):
                                completed_reviewers += 1

                # Iterate through all PC columns to count completed pc reviews
                for name_idx, score_idx in pc_columns:
                    # Check if the name field is not empty and the score field does not contain "T"
                    if (row[name_idx].strip() != ''):
                        score = row[score_idx].strip()
                        if re.match(r'\d+\.\d+', score):
                            pc_completed += 1

                # If the number of confirmed reviewers is less than 2, increment the counter
                missing_reviewer_counts[s1_name_value] += max(0, 2 - (confirmed_reviewers+tentative_reviewers))
                total_reviewer_counts[s1_name_value] += confirmed_reviewers
                tentative_reviewer_counts[s1_name_value] += tentative_reviewers
                total_paper_counts[s1_name_value] += 1
                if confirmed_reviewers < 2:
                    # print(f"{row[1]} does not have enough confirmed reviewers - {s1_name_value}")
                    low_reviewer_counts[s1_name_value] += 1
                elif confirmed_reviewers > 2:
                    overcommitted_reviewer_counts[s1_name_value] += (confirmed_reviewers - 2)
                    
                pc_completed_reviews_counts[s1_name_value] += pc_completed
                completed_reviews_counts[s1_name_value] += completed_reviewers

        # Write the results to standard output
        writer = csv.writer(sys.stdout)
        writer.writerow([
            'Primary', 
            'Subcommittee', 
            'Papers Needing Reviewers', 
            'Overcommitted Papers', 
            'Total Papers', 
            'Tentative Reviewers', 
            'Missing Reviewers', 
            'Assigned Reviewers', 
            'Completed External Reviews', 
            'Completed PC Reviews'])
        for s1_name, count in sorted(low_reviewer_counts.items()):
            writer.writerow([
                s1_name,
                reviewer_subcommittee[s1_name],
                count,
                overcommitted_reviewer_counts[s1_name],
                total_paper_counts[s1_name],
                tentative_reviewer_counts[s1_name],
                missing_reviewer_counts[s1_name],
                total_reviewer_counts[s1_name],
                completed_reviews_counts[s1_name],
                pc_completed_reviews_counts[s1_name],
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
