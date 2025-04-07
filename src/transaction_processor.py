"""
Transaction Processor - Core functionality for processing financial transactions.

This module provides utilities to load, process and categorize financial transactions
from CSV files according to predefined rules and user input.
"""

import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from difflib import SequenceMatcher
import re

class TransactionProcessor:
    """Process and categorize financial transactions from CSV data."""
    
    def __init__(self, category_file: str = None):
        """
        Initialize the transaction processor.
        
        Args:
            category_file: Path to category database JSON file. If not provided,
                           uses default categories.
        """
        self.category_db = self._load_category_db(category_file)
        
    def _load_category_db(self, category_file: Optional[str]) -> Dict:
        """
        Load category database from file or create default if not provided.
        
        Args:
            category_file: Path to category database JSON file
            
        Returns:
            Dictionary containing categorization data
        """
        if category_file and os.path.exists(category_file):
            try:
                with open(category_file, 'r') as f:
                    db = json.load(f)
                
                # Validate that all lists have the same length
                if not (len(db["descriptions"]) == len(db["business_labels"]) == len(db["retailer_labels"])):
                    print("Warning: Category database has mismatched list lengths. Using default values.")
                    # Fall back to default values
                    category_file = None
                else:
                    return db
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading category database: {e}. Using default values.")
                # Fall back to default values
                category_file = None
        
        # Default category database with only the initial mapping rules
        # Each entry is a tuple of (description, business_type, retailer)
        # Empty strings are omitted for clarity
        mapping_rules = [
            ("oakhurst", "Oakhurst", None),
            ("pleasanton", "Personal", None),
            ("san ramon", "Personal", None),
            ("dublin", "Personal", None),
            ("amazon", None, "Amazon"),
            ("costco", None, "Costco")
        ]
        
        descriptions = []
        business_labels = []
        retailer_labels = []
        
        for desc, business, retailer in mapping_rules:
            descriptions.append(desc)
            business_labels.append(business if business else "")
            retailer_labels.append(retailer if retailer else "")
        
        # Create default database
        db = {
            "descriptions": descriptions,
            "business_labels": business_labels,
            "retailer_labels": retailer_labels
        }
        
        # Save it immediately to ensure consistent state
        if category_file:
            os.makedirs(os.path.dirname(category_file), exist_ok=True)
            with open(category_file, 'w') as f:
                json.dump(db, indent=2, fp=f)
        
        return db
    
    def save_category_db(self, filename: str) -> None:
        """
        Save current category database to a JSON file.
        
        Args:
            filename: Path to save the category database
        """
        with open(filename, 'w') as f:
            json.dump(self.category_db, f, indent=2)
            
    def add_business_type(self, business_type: str) -> None:
        """
        Add a new business type without changing the predefined mapping rules.
        
        This method doesn't modify the descriptions or mapping rules,
        it's just used to track available business type labels for the UI.
        
        Args:
            business_type: Business type label to add
        """
        # Do nothing - business types are just tracked in the UI now
        pass
    
    def load_transactions(self, csv_path: str) -> pd.DataFrame:
        """
        Load transactions from a CSV file.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            DataFrame containing transaction data
        """
        df = pd.read_csv(csv_path)
        required_columns = ["Status", "Date", "Description", "Debit", "Credit", "Member Name"]
        
        # Validate that all required columns exist
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"CSV file missing required columns: {', '.join(missing_cols)}")
            
        # Add categorization columns if they don't exist
        if "Business Type" not in df.columns:
            df["Business Type"] = ""
        if "Retailer" not in df.columns:
            df["Retailer"] = ""
            
        return df

    def _match_description(self, description: str) -> List[int]:
        """
        Find all matching categories for a transaction description.
        
        Args:
            description: Transaction description
            
        Returns:
            List of indices of matching categories
        """
        description = description.lower()
        matches = []
        
        for idx, key_phrase in enumerate(self.category_db["descriptions"]):
            # Make case-insensitive and space-insensitive comparison
            if key_phrase.lower().replace(" ", "") in description.replace(" ", ""):
                matches.append(idx)
                
        return matches
    
    def categorize_transaction(self, description: str) -> Tuple[str, str]:
        """
        Categorize a single transaction by description.
        
        Args:
            description: Transaction description
            
        Returns:
            Tuple of (business_type, retailer)
        """
        # Validate category_db structure
        if (len(self.category_db["descriptions"]) != len(self.category_db["business_labels"]) or
            len(self.category_db["descriptions"]) != len(self.category_db["retailer_labels"])):
            print("Warning: Category database has mismatched list lengths. This may cause errors.")
            print(f"Descriptions: {len(self.category_db['descriptions'])}")
            print(f"Business Labels: {len(self.category_db['business_labels'])}")
            print(f"Retailer Labels: {len(self.category_db['retailer_labels'])}")
            # Return empty values to avoid errors
            return "", ""
            
        matches = self._match_description(description)
        
        business_type = ""
        retailer = ""
        
        for idx in matches:
            # Safety check to avoid index errors
            if idx >= len(self.category_db["business_labels"]) or idx >= len(self.category_db["retailer_labels"]):
                print(f"Warning: Index {idx} out of bounds for category database")
                continue
                
            # Apply business type if available and not already set
            if self.category_db["business_labels"][idx] and not business_type:
                business_type = self.category_db["business_labels"][idx]
            
            # Apply retailer if available and not already set
            if self.category_db["retailer_labels"][idx] and not retailer:
                retailer = self.category_db["retailer_labels"][idx]
                
        return business_type, retailer
        
    def categorize_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply categorization to all transactions in the dataframe.
        
        Args:
            df: DataFrame containing transactions
            
        Returns:
            DataFrame with categorized transactions
        """
        # Make a copy to avoid modifying the original
        result = df.copy()
        
        # Apply categorization where not already set
        for i, row in result.iterrows():
            if not row["Business Type"] or not row["Retailer"]:
                business, retailer = self.categorize_transaction(row["Description"])
                
                # Only update if empty
                if not row["Business Type"] and business:
                    result.at[i, "Business Type"] = business
                if not row["Retailer"] and retailer:
                    result.at[i, "Retailer"] = retailer
                    
        return result
    
    def find_similar_descriptions(self, df: pd.DataFrame, threshold: float = 0.6) -> List[List[int]]:
        """
        Group similar transaction descriptions.
        
        Args:
            df: DataFrame containing transactions
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            List of lists, where each inner list contains indices of similar transactions
        """
        # Only consider transactions with unlabeled business type
        # The DataFrame passed should already be filtered
        if df.empty:
            return []
            
        # Get descriptions and their indices in the original dataframe
        descriptions = df["Description"].tolist()
        indices = df.index.tolist()
        
        # Track which descriptions have been grouped
        grouped = set()
        groups = []
        
        # Group similar descriptions
        for i, desc1 in enumerate(descriptions):
            if i in grouped:
                continue
                
            group = [indices[i]]
            grouped.add(i)
            
            for j, desc2 in enumerate(descriptions):
                if i == j or j in grouped:
                    continue
                    
                # Calculate similarity
                similarity = SequenceMatcher(None, desc1, desc2).ratio()
                if similarity >= threshold:
                    group.append(indices[j])
                    grouped.add(j)
                    
            if len(group) > 1:  # Only add groups with at least 2 items
                groups.append(group)
                
        return groups
    
    def save_transactions(self, df: pd.DataFrame, output_path: str) -> None:
        """
        Save processed transactions to a CSV file.
        
        Args:
            df: DataFrame containing processed transactions
            output_path: Path to save the CSV file
        """
        df.to_csv(output_path, index=False)