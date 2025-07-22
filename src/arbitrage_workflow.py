# Handles arbitrage finding

from lib.arbmath import ArbitrageFinder
import json

class ArbitrageWorkflow:
    def __init__(self, database):
        self.arb_finder = ArbitrageFinder(database)

    def find_arbitrage(self):
        arbs = self.arb_finder.find_arbitrage()
        with open('data/all_arbs.json', 'w') as outfile:
            json.dump(arbs, outfile, indent=4)
        return arbs
