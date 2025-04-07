# Financial Transaction Manager

A tool for managing and categorizing financial transactions with automatic and manual labeling.

### Accessing the tool with Binder

.. image:: https://mybinder.org/badge_logo.svg
 :target: https://mybinder.org/v2/gh/KabirDubey/pnl/HEAD

 The interactive notebook is in `transaction_manager.ipynb`

## Features

- **CSV Processing**: Import transaction data from CSV files with a standardized format
- **Automatic Categorization**: Automatically label transactions based on keywords
- **Manual Categorization**: Group similar transactions for efficient manual labeling
- **Visualization**: View statistics and charts of categorized transactions
- **Web Interface**: User-friendly Jupyter notebook interface with interactive widgets

## Requirements

- Python 3.6+
- pandas
- numpy
- ipywidgets
- matplotlib
- Jupyter notebook

## Installation

1. Clone this repository
2. Install required packages:

```
pip install pandas numpy matplotlib ipywidgets jupyter
```

## Usage

1. Launch the Jupyter notebook:

```
jupyter notebook transaction_manager.ipynb
```

2. Follow the interactive steps in the notebook:
   - Upload or select a CSV file with transaction data
   - Apply automatic categorization rules
   - Manually categorize similar transaction groups
   - Save the categorized transactions to a new CSV file
   - View statistics about your categorized transactions

## CSV Format

The input CSV file should have the following columns:
- Status
- Date
- Description
- Debit
- Credit
- Member Name

The output will add two additional columns:
- Business Type
- Retailer

## Web Deployment

You can deploy this tool to the web using:

## License

MIT