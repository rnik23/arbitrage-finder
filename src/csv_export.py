# Handles CSV exporting

import csv

class CSVExport:
    @staticmethod
    def export_to_csv(bets, csv_file_path='data/arbitrage_output.csv'):
        if bets:
            keys = set()
            for bet in bets:
                keys.update(bet.keys())
            keys = list(keys)
            with open(csv_file_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=keys)
                writer.writeheader()
                writer.writerows(bets)
            print(f"Arbitrage output saved to {csv_file_path}")
        else:
            print("No arbitrage opportunities found to export.")
