"""
Streamlit application for the Financial Transaction Manager.

This module provides a web interface for processing and categorizing financial transactions.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import json
from typing import List, Dict, Tuple
from transaction_processor import TransactionProcessor

# Set page title and configuration
st.set_page_config(
    page_title="Financial Transaction Manager",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "transactions_df" not in st.session_state:
    st.session_state.transactions_df = None
if "processor" not in st.session_state:
    st.session_state.processor = TransactionProcessor()
if "current_group_idx" not in st.session_state:
    st.session_state.current_group_idx = 0
if "all_groups" not in st.session_state:
    st.session_state.all_groups = []
if "current_group" not in st.session_state:
    st.session_state.current_group = []

# Title and description
st.title("Financial Transaction Manager")
st.markdown("""
This tool helps you categorize financial transactions by adding Business Type and Retailer labels.
Upload a CSV file with your transaction data to get started.
""")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Upload Data", "Automatic Categorization", "Manual Categorization", "Statistics", "Save Results"])

# Sidebar for category database management
st.sidebar.title("Category Database")
if st.sidebar.button("Save Category Database"):
    if not os.path.exists("src"):
        os.makedirs("src")
    st.session_state.processor.save_category_db("src/category_db.json")
    st.sidebar.success("Category database saved!")

if st.sidebar.button("Load Category Database"):
    if os.path.exists("src/category_db.json"):
        st.session_state.processor = TransactionProcessor("src/category_db.json")
        st.sidebar.success("Category database loaded!")
    else:
        st.sidebar.error("Category database file not found!")

# Upload Data page
if page == "Upload Data":
    st.header("Upload Transaction Data")
    
    # File uploader
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            # Save to a temporary file
            with open("temp_upload.csv", "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Load using processor
            st.session_state.transactions_df = st.session_state.processor.load_transactions("temp_upload.csv")
            st.success(f"Successfully loaded {len(st.session_state.transactions_df)} transactions!")
            
            # Display the data
            st.subheader("Transaction Data Preview")
            st.dataframe(st.session_state.transactions_df.head())
            
            # Display column info
            st.subheader("Column Information")
            buffer = io.StringIO()
            st.session_state.transactions_df.info(buf=buffer)
            st.text(buffer.getvalue())
            
            # Clean up temp file
            if os.path.exists("temp_upload.csv"):
                os.remove("temp_upload.csv")
                
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")

# Automatic Categorization page
elif page == "Automatic Categorization":
    st.header("Automatic Transaction Categorization")
    
    if st.session_state.transactions_df is None:
        st.warning("Please upload transaction data first!")
    else:
        if st.button("Apply Automatic Categorization"):
            # Apply categorization
            before_count = st.session_state.transactions_df[(st.session_state.transactions_df["Business Type"] != "") | 
                                                          (st.session_state.transactions_df["Retailer"] != "")].shape[0]
            st.session_state.transactions_df = st.session_state.processor.categorize_transactions(st.session_state.transactions_df)
            after_count = st.session_state.transactions_df[(st.session_state.transactions_df["Business Type"] != "") | 
                                                         (st.session_state.transactions_df["Retailer"] != "")].shape[0]
            
            # Display results
            newly_categorized = after_count - before_count
            st.success(f"Categorized {newly_categorized} new transactions!")
            st.info(f"Total categorized: {after_count} out of {len(st.session_state.transactions_df)}")
        
        # Display categorized transactions
        st.subheader("Categorized Transactions")
        categorized = st.session_state.transactions_df[(st.session_state.transactions_df["Business Type"] != "") | 
                                                     (st.session_state.transactions_df["Retailer"] != "")]
        st.dataframe(categorized)
        
        # Display uncategorized transactions
        st.subheader("Uncategorized Transactions")
        uncategorized = st.session_state.transactions_df[(st.session_state.transactions_df["Business Type"] == "") & 
                                                       (st.session_state.transactions_df["Retailer"] == "")]
        st.dataframe(uncategorized)

# Manual Categorization page
elif page == "Manual Categorization":
    st.header("Manual Transaction Categorization")
    
    if st.session_state.transactions_df is None:
        st.warning("Please upload transaction data first!")
    else:
        # Similarity threshold
        similarity = st.slider("Similarity Threshold", 0.1, 0.9, 0.6, 0.1)
        
        if st.button("Find Similar Transactions"):
            # Find similar groups
            st.session_state.all_groups = st.session_state.processor.find_similar_descriptions(
                st.session_state.transactions_df, similarity)
            st.session_state.current_group_idx = 0
            
            if not st.session_state.all_groups:
                st.info("No similar transaction groups found!")
            else:
                st.success(f"Found {len(st.session_state.all_groups)} groups of similar transactions!")
                st.session_state.current_group = st.session_state.all_groups[0]
        
        # Display current group
        if st.session_state.all_groups and st.session_state.current_group_idx < len(st.session_state.all_groups):
            st.subheader(f"Group {st.session_state.current_group_idx + 1} of {len(st.session_state.all_groups)}")
            
            # Get current group data
            current_group = st.session_state.all_groups[st.session_state.current_group_idx]
            group_df = st.session_state.transactions_df.loc[current_group].copy()
            
            # Display group data
            st.dataframe(group_df[["Description", "Debit", "Credit", "Date"]])
            
            # Get unique values for dropdowns
            business_types = set()
            retailers = set()
            
            # Add values from the category database
            for label in st.session_state.processor.category_db["business_labels"]:
                if label:
                    business_types.add(label)
            
            for label in st.session_state.processor.category_db["retailer_labels"]:
                if label:
                    retailers.add(label)
            
            # Add values from current transactions
            for label in st.session_state.transactions_df["Business Type"].unique():
                if label:
                    business_types.add(label)
            
            for label in st.session_state.transactions_df["Retailer"].unique():
                if label:
                    retailers.add(label)
            
            # Create form for labeling
            with st.form("label_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Select Labels")
                    
                    # Select existing labels
                    business_type = st.selectbox("Business Type", [""] + sorted(list(business_types)))
                    retailer = st.selectbox("Retailer", [""] + sorted(list(retailers)))
                
                with col2:
                    st.subheader("Or Create New Labels")
                    
                    # Create new labels
                    new_business = st.text_input("New Business Type")
                    new_retailer = st.text_input("New Retailer")
                
                # Key phrase for matching
                key_phrase = st.text_input("Key Phrase for Future Matching",
                                         help="Enter a phrase that appears in these transactions for future matching")
                
                # Submit buttons
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Apply & Next")
                with col2:
                    skip = st.form_submit_button("Skip")
            
            # Handle form submission
            if submitted:
                # Get selected values
                business = business_type or new_business
                retailer = retailer or new_retailer
                phrase = key_phrase
                
                if not phrase and (business or retailer):
                    # Use the first description as the key phrase if none provided
                    phrase = st.session_state.transactions_df.loc[current_group[0], "Description"].lower()
                    # Extract a substring that might be common
                    phrase = " ".join(phrase.split()[:2])
                
                if phrase and (business or retailer):
                    # Add to category database
                    st.session_state.processor.add_category(phrase, business, retailer)
                    
                    # Save the updated database
                    if not os.path.exists("src"):
                        os.makedirs("src")
                    st.session_state.processor.save_category_db("src/category_db.json")
                    
                    # Apply to all transactions in the group
                    for idx in current_group:
                        if business:
                            st.session_state.transactions_df.at[idx, "Business Type"] = business
                        if retailer:
                            st.session_state.transactions_df.at[idx, "Retailer"] = retailer
                    
                    st.success(f"Applied labels to {len(current_group)} transactions!")
                
                # Move to next group
                st.session_state.current_group_idx += 1
                st.experimental_rerun()
            
            if skip:
                # Move to next group
                st.session_state.current_group_idx += 1
                st.experimental_rerun()
            
        elif st.session_state.all_groups:
            st.success("All groups processed!")

# Statistics page
elif page == "Statistics":
    st.header("Transaction Statistics")
    
    if st.session_state.transactions_df is None:
        st.warning("Please upload transaction data first!")
    else:
        # Calculate statistics
        total = len(st.session_state.transactions_df)
        categorized = st.session_state.transactions_df[(st.session_state.transactions_df["Business Type"] != "") | 
                                                    (st.session_state.transactions_df["Retailer"] != "")].shape[0]
        uncategorized = total - categorized
        
        # Display basic statistics
        st.subheader("Basic Statistics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Transactions", total)
        col2.metric("Categorized", f"{categorized} ({categorized/total*100:.1f}%)")
        col3.metric("Uncategorized", f"{uncategorized} ({uncategorized/total*100:.1f}%)")
        
        # Create charts
        st.subheader("Distribution Charts")
        col1, col2 = st.columns(2)
        
        with col1:
            # Business Type distribution
            st.markdown("#### Business Type Distribution")
            business_counts = st.session_state.transactions_df["Business Type"].value_counts()
            if "" in business_counts:
                business_counts = business_counts.drop("")
            
            if not business_counts.empty:
                fig, ax = plt.subplots()
                business_counts.plot(kind="pie", ax=ax, autopct="%1.1f%%")
                ax.set_ylabel("")
                st.pyplot(fig)
            else:
                st.info("No Business Types assigned yet")
        
        with col2:
            # Retailer distribution
            st.markdown("#### Retailer Distribution")
            retailer_counts = st.session_state.transactions_df["Retailer"].value_counts()
            if "" in retailer_counts:
                retailer_counts = retailer_counts.drop("")
            
            if not retailer_counts.empty:
                fig, ax = plt.subplots()
                retailer_counts.plot(kind="pie", ax=ax, autopct="%1.1f%%")
                ax.set_ylabel("")
                st.pyplot(fig)
            else:
                st.info("No Retailers assigned yet")

# Save Results page
elif page == "Save Results":
    st.header("Save Categorized Transactions")
    
    if st.session_state.transactions_df is None:
        st.warning("Please upload transaction data first!")
    else:
        # File name input
        filename = st.text_input("Output Filename", "categorized_transactions.csv")
        
        if st.button("Save Transactions"):
            if not filename.endswith(".csv"):
                filename += ".csv"
            
            # Create output directory if it doesn't exist
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            output_path = os.path.join(output_dir, filename)
            
            # Save using processor
            st.session_state.processor.save_transactions(st.session_state.transactions_df, output_path)
            st.success(f"Saved {len(st.session_state.transactions_df)} transactions to {output_path}!")
            
            # Provide download link
            with open(output_path, "rb") as f:
                st.download_button(
                    label="Download CSV File",
                    data=f,
                    file_name=filename,
                    mime="text/csv",
                )

        # Display preview of the data to be saved
        st.subheader("Data Preview")
        st.dataframe(st.session_state.transactions_df)