from data_loader import load_dataset
from cleaning_rules import clean_data
from reporting import generate_report

def main():
    print("=" * 50)
    print(" Business Data Cleaning & Reporting Tool ")
    print("=" * 50)

    file_path = input("\nEnter CSV or Excel file path: ")

    try:
        # Step 1: Load Dataset
        print("\nLoading dataset...")
        df = load_dataset(file_path)
        print("Dataset loaded successfully.")

        # Step 2: Clean Dataset
        print("\nCleaning dataset...")
        cleaned_df = clean_data(df)

        # Step 3: Save Cleaned Dataset
        cleaned_df.to_csv("cleaned_data.csv", index=False)
        print("Cleaned dataset saved as 'cleaned_data.csv'.")

        # Step 4: Generate Summary Report
        summary = generate_report(cleaned_df)

        print("\nSummary Report")
        print("-" * 40)
        print(summary)

        print("\nSummary report saved as 'summary_report.xlsx'.")

        print("\nProject Completed Successfully!")

    except FileNotFoundError as e:
        print(f"\nError: {e}")

    except ValueError as e:
        print(f"\nError: {e}")

    except Exception as e:
        print(f"\nUnexpected Error: {e}")


if __name__ == "__main__":
    main()