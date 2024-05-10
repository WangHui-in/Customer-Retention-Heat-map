import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Load datasets
# Load datasets
sales_data = pd.read_csv('Online_Sales.csv')
tax_data = pd.read_csv('Tax_amount.csv')
discount_coupon_data = pd.read_csv('Discount_Coupon.csv')
marketing_spend_data = pd.read_csv('Marketing_Spend.csv')
customers_data = pd.read_csv('CustomersData.csv')

# Data cleaning and preparation

# Convert 'Transaction_Date' to datetime
sales_data['Transaction_Date'] = pd.to_datetime(sales_data['Transaction_Date'])

# Extract the month from the 'Transaction_Date' and create a new 'Month' column
sales_data['Month'] = sales_data['Transaction_Date'].dt.month
# Check 
print(sales_data.head())

# Use number replace month
month_mapping = {
    'Jan': 1,'Feb': 2,'Mar': 3,'Apr': 4,'May': 5,'Jun': 6,'Jul': 7, 'Aug': 8, 'Sep': 9,'Oct': 10,'Nov': 11,'Dec': 12
}
# Assuming the column with month names is called 'Month'
discount_coupon_data['Month'] = discount_coupon_data['Month'].replace(month_mapping)

# Merge with other datasets
merged_data1 = pd.merge(sales_data, tax_data, on='Product_Category', how='left')
merged_data2 = pd.merge(merged_data1, discount_coupon_data, on=['Product_Category','Month'], how='left')
merged_data3 = pd.merge(merged_data2, customers_data, on='CustomerID', how='left')

# Drop duplicates
merged_data3.drop_duplicates(inplace=True)

# Convert 'GST' from object to float
column_name = 'GST' 
if merged_data3[column_name].dtype == 'object':
    # Convert percentage string to float directly in merged_data3
    merged_data3[column_name] = merged_data3[column_name].str.replace('%', '').astype(float) / 100
else:
    # If 'GST' is already a number (float or int) but formatted as a percentage, divide by 100 directly in merged_data3.
    merged_data3[column_name] = merged_data3[column_name].astype(float) / 100


# Convert 'Discount_pct( Discount Percentage for given coupon)' from percentage value to a decimal which can use to calculate.
column_name2 = 'Discount_pct' 
merged_data3[column_name2] = merged_data3[column_name2].astype(float) / 100


merged_data3['Discount_pct'].fillna(0, inplace = True)

# Calculate invoice value for each transaction 
merged_data3['Invoice_Value'] = ((merged_data3['Quantity'] * merged_data3['Avg_Price']) * 
                                (1.0 - merged_data3['Discount_pct']) * 
                                (1.0 + merged_data3['GST'])) + merged_data3['Delivery_Charges']

# Calculate invoice value for each customer each date
invoice_value_each_customer_each_date = merged_data3. groupby (['CustomerID','Transaction_Date'])['Invoice_Value'].sum().reset_index()
print(invoice_value_each_customer_each_date.head())


 #Perform customer segmentation
from datetime import datetime
current_date = datetime.now()



# Ensure 'Transaction_Date' is a datetime type
merged_data3['Transaction_Date'] = pd.to_datetime(merged_data3['Transaction_Date'])

# Create a column 'CohortMonth' that represents the month of the first purchase for each customer
merged_data3['CohortMonth'] = merged_data3.groupby('CustomerID')['Transaction_Date'].transform('min').dt.to_period('M')

# Create a column 'TransactionMonth' that represents the month of each transaction
merged_data3['TransactionMonth'] = merged_data3['Transaction_Date'].dt.to_period('M')

# Create a cohort group by 'CohortMonth' and 'TransactionMonth'
cohort_data = merged_data3.groupby(['CohortMonth', 'TransactionMonth']).agg(n_customers=('CustomerID', 'nunique')).reset_index()

# Create a period number which represents the number of periods between the cohort month and the transaction month
cohort_data['PeriodNumber'] = (cohort_data['TransactionMonth'] - cohort_data['CohortMonth']).apply(lambda x: x.n)

# Pivot the cohort data to create the retention matrix
cohort_counts = cohort_data.pivot_table(index='CohortMonth', columns='PeriodNumber', values='n_customers')

# Re-index the DataFrame to fill in the missing months for plotting
all_months = pd.period_range(cohort_counts.index.min(), cohort_counts.index.max(), freq='M')
cohort_counts = cohort_counts.reindex(all_months)

# Calculate the retention rate
cohort_sizes = cohort_counts.iloc[:,0] # The number of customers in the first column is the size of each cohort
retention_matrix = cohort_counts.divide(cohort_sizes, axis=0)
print(cohort_data)


# Plot the retention matrix using seaborn's heatmap
plt.figure(figsize=(12, 8))
sns.heatmap(retention_matrix, annot=True, fmt='.0%', cmap='Blues')
plt.title('Customer Retention Month on Month',fontsize=25)
plt.ylabel('Cohort Month',fontsize=25)
plt.xlabel('Months Since First Purchase',fontsize=25)
plt.xticks(rotation=0,fontsize=20)
plt.yticks(rotation=0,fontsize=20)
# Adjust x-axis ticks to start from 1 instead of 0
plt.xticks(np.arange(0.5, len(cohort_counts.columns) + 0.5), np.arange(1, len(cohort_counts.columns) + 1))
plt.show()