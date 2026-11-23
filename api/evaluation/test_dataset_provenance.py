import sys
import unittest
from pathlib import Path

import pandas as pd

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.core.exceptions import InvalidResponseError
from app.services.rag_service import get_dish_info


class DatasetProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.foods = pd.DataFrame([
            {"name": "Món A", "calories": 123, "protein_g": 4, "carbs_g": 5,
             "fat_g": 6, "cost_vnd": 7000, "source_citation": "Tài liệu A",
             "valid_period": "2023", "limitation_type": "Giới hạn A"},
            {"name": "Món B", "calories": 456, "protein_g": 7, "carbs_g": 8,
             "fat_g": 9, "cost_vnd": 10000, "source_citation": "Tài liệu B",
             "valid_period": "2024", "limitation_type": "Giới hạn B"},
        ])

    def test_selected_dish_keeps_its_own_source(self):
        dish = get_dish_info("Món B", self.foods)
        self.assertEqual(dish["calories"], 456)
        self.assertEqual(dish["source_citation"], "Tài liệu B")
        self.assertEqual(dish["valid_period"], "2024")

    def test_unknown_dish_does_not_borrow_another_dish_source(self):
        with self.assertRaises(InvalidResponseError):
            get_dish_info("Món C", self.foods)


if __name__ == "__main__":
    unittest.main()
