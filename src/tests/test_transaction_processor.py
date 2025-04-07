"""
Tests for the transaction processor module.
"""

import os
import pandas as pd
import unittest
import json
import tempfile
from src.transaction_processor import TransactionProcessor

class TestTransactionProcessor(unittest.TestCase):
    """Test case for TransactionProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = TransactionProcessor()
        
        # Create a sample data frame for testing
        self.test_df = pd.DataFrame({
            "Status": ["Posted"] * 6,
            "Date": ["2023-01-01"] * 6,
            "Description": [
                "Amazon Prime Subscription",
                "Costco Wholesale #123",
                "OAKHURST DAIRY FARM",
                "STARBUCKS PLEASANTON CA",
                "TARGET DUBLIN CA",
                "WALMART SAN RAMON CA"
            ],
            "Debit": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
            "Credit": ["", "", "", "", "", ""],
            "Member Name": ["Test User"] * 6,
            "Business Type": ["", "", "", "", "", ""],
            "Retailer": ["", "", "", "", "", ""]
        })
        
        # Create a temporary file for testing file operations
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_csv = os.path.join(self.temp_dir.name, "test_transactions.csv")
        self.temp_json = os.path.join(self.temp_dir.name, "test_category_db.json")
        self.test_df.to_csv(self.temp_csv, index=False)
        
    def tearDown(self):
        """Tear down test fixtures."""
        self.temp_dir.cleanup()
        
    def test_default_categories(self):
        """Test that default categories are correctly loaded."""
        db = self.processor.category_db
        self.assertIn("descriptions", db)
        self.assertIn("business_labels", db)
        self.assertIn("retailer_labels", db)
        
        # Check specific mapping rules
        self.assertIn("oakhurst", db["descriptions"])
        
        # Find index of "oakhurst" and check corresponding business label
        idx = db["descriptions"].index("oakhurst")
        self.assertEqual(db["business_labels"][idx], "Oakhurst")
        
    def test_load_transactions(self):
        """Test loading transactions from a CSV file."""
        df = self.processor.load_transactions(self.temp_csv)
        self.assertEqual(len(df), 6)
        self.assertIn("Business Type", df.columns)
        self.assertIn("Retailer", df.columns)
        
    def test_categorize_transactions(self):
        """Test automatic categorization of transactions."""
        result = self.processor.categorize_transactions(self.test_df)
        
        # Check Amazon categorization
        amazon_row = result[result["Description"] == "Amazon Prime Subscription"]
        self.assertEqual(amazon_row["Retailer"].iloc[0], "Amazon")
        
        # Check Costco categorization
        costco_row = result[result["Description"] == "Costco Wholesale #123"]
        self.assertEqual(costco_row["Retailer"].iloc[0], "Costco")
        
        # Check Oakhurst categorization
        oakhurst_row = result[result["Description"] == "OAKHURST DAIRY FARM"]
        self.assertEqual(oakhurst_row["Business Type"].iloc[0], "Oakhurst")
        
        # Check Pleasanton categorization
        pleasanton_row = result[result["Description"] == "STARBUCKS PLEASANTON CA"]
        self.assertEqual(pleasanton_row["Business Type"].iloc[0], "Personal")
        
        # Check Dublin categorization
        dublin_row = result[result["Description"] == "TARGET DUBLIN CA"]
        self.assertEqual(dublin_row["Business Type"].iloc[0], "Personal")
        
        # Check San Ramon categorization
        san_ramon_row = result[result["Description"] == "WALMART SAN RAMON CA"]
        self.assertEqual(san_ramon_row["Business Type"].iloc[0], "Personal")
        
    def test_save_and_load_category_db(self):
        """Test saving and loading the category database."""
        # Add a new category
        self.processor.add_category("walmart", "Retail", "Walmart")
        
        # Save the database
        self.processor.save_category_db(self.temp_json)
        
        # Create a new processor with the saved database
        new_processor = TransactionProcessor(self.temp_json)
        
        # Check if the new category is in the loaded database
        self.assertIn("walmart", new_processor.category_db["descriptions"])
        
        # Find index of "walmart" and check corresponding labels
        idx = new_processor.category_db["descriptions"].index("walmart")
        self.assertEqual(new_processor.category_db["business_labels"][idx], "Retail")
        self.assertEqual(new_processor.category_db["retailer_labels"][idx], "Walmart")
        
    def test_find_similar_descriptions(self):
        """Test finding similar descriptions for manual categorization."""
        # Create a dataframe with similar descriptions
        df = pd.DataFrame({
            "Status": ["Posted"] * 4,
            "Date": ["2023-01-01"] * 4,
            "Description": [
                "WALMART #1234",
                "WALMART #5678",
                "STARBUCKS #1234",
                "CHEVRON GAS"
            ],
            "Debit": [10.0, 20.0, 30.0, 40.0],
            "Credit": ["", "", "", ""],
            "Member Name": ["Test User"] * 4,
            "Business Type": ["", "", "", ""],
            "Retailer": ["", "", "", ""]
        })
        
        groups = self.processor.find_similar_descriptions(df, threshold=0.6)
        # Should group the two Walmart entries
        self.assertTrue(any(len(group) >= 2 for group in groups))
        
if __name__ == "__main__":
    unittest.main()