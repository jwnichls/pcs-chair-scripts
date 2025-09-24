import argparse
import csv
import sys
from datetime import datetime

def process_declined_reviews(file_path, oldest_date_str):
    """
    Processes a CSV file to find submissions where a subject has declined to review.

    It filters by date and extracts the submission number and the name of
    the person who declined.

    Args:
        file_path (str): The path to the input CSV file.
        oldest_date_str (str): The oldest date to include, in 'YYYY-MM-DD' format.
    """
    try:
        # Convert the oldest date string to a datetime object for comparison
        oldest_date = datetime.strptime(oldest_date_str, '%Y-%m-%d').date()
    except ValueError:
        print(f"Error: Invalid date format. Please use YYYY-MM-DD.", file=sys.stderr)
        return

    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            header = next(reader)  # Read the header row

            # Find the indices of the required columns
            try:
                date_col_index = header.index("Date")
                submission_col_index = header.index("Submission")
                subject_col_index = next(
                    i for i, col in enumerate(header) if col.startswith("Subject")
                )
            except (ValueError, StopIteration):
                print("Error: The CSV file must contain 'Date', 'Submission', and a column starting with 'Subject'.", file=sys.stderr)
                return

            # Prepare the output CSV writer to standard output
            writer = csv.writer(sys.stdout)
            writer.writerow(["Submission", "Name"])

            # Get the current year to use for parsing dates without a year
            current_year = datetime.now().year

            # Process each row in the CSV
            for row in reader:
                # Ensure the row has enough columns to avoid IndexError
                if len(row) > max(date_col_index, submission_col_index, subject_col_index):
                    try:
                        # Parse the date from the row. The new format assumes the current year.
                        row_date_str = f"{row[date_col_index]} {current_year}"
                        row_date = datetime.strptime(row_date_str, '%b %d %H:%M %Y').date()                        
                        # Get the subject content
                        subject_content = row[subject_col_index]

                        # Check if the date is recent enough and if the subject declined
                        if row_date >= oldest_date and "declines to review" in subject_content:
                            # Extract the name from the subject string
                            name = subject_content.split(" declines to review")[0].strip()
                            submission = row[submission_col_index]

                            # Write the result to standard output
                            writer.writerow([submission, name])

                    except ValueError as e:
                        # Handle potential errors with date parsing in a row
                        print(f"Warning: Could not parse date in row '{row}'. Skipping. Error: {e}", file=sys.stderr)
                    except IndexError as e:
                         print(f"Warning: Row '{row}' has an unexpected number of columns. Skipping. Error: {e}", file=sys.stderr)

    except FileNotFoundError:
        print(f"Error: The file at '{file_path}' was not found.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)


if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description="Extracts names and submission numbers for declined reviews from a CSV file."
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="The path to the input CSV file."
    )
    parser.add_argument(
        "oldest_date",
        type=str,
        help="The oldest date to search from, in YYYY-MM-DD format."
    )
    
    args = parser.parse_args()
    
    # Call the main function with the parsed arguments
    process_declined_reviews(args.file_path, args.oldest_date)
