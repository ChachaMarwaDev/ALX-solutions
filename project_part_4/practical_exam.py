# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from collections import Counter

# CSV is in the same folder as my python file
df = pd.read_csv("MD_agric_exam-4313.csv")

# Overview of our data
# df.head(5)
# df.describe()
# df.columns
# df.shape
df.columns = df.columns.str.lower()
df.columns
# %%
# Write code to determine the number of unique crop types in the dataset?
unique_crops = df['crop_type'].nunique()
print(f"Number of unique crop types: {unique_crops}")

# %%
# Identify the maximum annual yield for "wheat" crop type in the dataset (rounded to 2 decimal places).
# Max yield
wheat_yield = df[df['crop_type'] == 'wheat']['annual_yield'].max()

# Rounded yield
wheat_rounded = round(wheat_yield, 2)
print(f"Maximum annual yield: {wheat_rounded}")

# %%
# Find the total rainfall for crop types where the average pollution level is above 0.2.
total_rainfall = df[df['crop_type'].isin(df.groupby('crop_type')['pollution_level'].mean()[lambda x: x > 0.2].index)]['rainfall'].sum()

print(f"Total rainfall: {total_rainfall}")

# %%
# Write a function to calculate the temperature range (Max_temperature_C - Min_temperature_C) for each farmer's field. Then, call the function with the following `Field_ID`: `1458`, `1895`, and `5443`. What are the results of these 3 calls?
def calculate_temp_range(field_id):
    """
    Calculate temperature range (Max - Min) for a given field ID.
    
    Parameters:
    field_id: The Field_ID to look up
    
    Returns:
    Temperature range in degrees Celsius
    """
    # Filter the DataFrame for the specific field
    field_data = df[df['field_id'] == field_id]
    
    # Check if field exists
    if field_data.empty:
        return f"Field_ID {field_id} not found in dataset"
    
    # Calculate temperature range
    temp_range = field_data['max_temperature_c'].values[0] - field_data['min_temperature_c'].values[0]
    
    # Round to 2 decimal places for cleaner output
    return round(temp_range, 2)

# Call the function for the specified field IDs
field_ids = [1458, 1895, 5443]

for fid in field_ids:
    result = calculate_temp_range(fid)
    print(f"field_ID {fid}: temperature range = {result}°C")

# %%
# Write code to calculate the total plot size for plots where the pH is less than 5.5.
total_plot_size = df[df['ph'] < 5.5]['plot_size'].sum()

print(f"Total plot size for plots with pH < 5.5: {total_plot_size}")
# %%
# Using Pandas, create a dataframe that includes entries with a 'Min_temperature_C’< -5 and a 'Max_temperature_C' > 30. How many rows are in the filtered dataset?
filtered_df = df[(df['min_temperature_c'] < -5) & (df['max_temperature_c'] > 30)]

# Count the number of rows
row_count = len(filtered_df)

print(f"Number of rows with min_temp < -5 and max_temp > 30: {row_count}")
# %%
# Using Numpy, calculate the standard deviation of the 'Rainfall' for plots where the 'Plot_size' is larger than the median plot size of the dataset (round to 2 decimal places).
# Calculate the median plot size
median_plot_size = np.median(df['plot_size'])

# Filter for plots with plot_size > median
filtered_rainfall = df[df['plot_size'] > median_plot_size]['rainfall'].values

# Calculate standard deviation using NumPy
rainfall_std = np.std(filtered_rainfall)

# Round to 2 decimal places
rainfall_std_rounded = round(rainfall_std, 2)

print(f"Median plot size: {median_plot_size:.2f}")
print(f"Standard deviation of rainfall for plots with plot_size > median: {rainfall_std_rounded}")

# %%
# If you concatenate the first three digits of the most common ‘Max_temperature_C’ with the last three letters of the least common 'Crop_type', what string do you get?
# Note: Use the first mode if there are multiple modes
# 1. Find the most common Max_temperature_C
most_common_temp = df['max_temperature_c'].mode()[0]  # First mode if multiple
first_three_digits = str(most_common_temp)[:3]  # First 3 digits as string

# 2. Find the least common Crop_type
# Get frequency of each crop type
crop_counts = df['crop_type'].value_counts()
least_common_crop = crop_counts.idxmin()  # Crop with lowest frequency
last_three_letters = least_common_crop[-3:]  # Last 3 letters

# 3. Concatenate
result_string = first_three_digits + last_three_letters

print(f"Most common Max_temperature_C: {most_common_temp}")
print(f"First three digits: '{first_three_digits}'")
print(f"Least common Crop_type: '{least_common_crop}'")
print(f"Last three letters: '{last_three_letters}'")
print(f"Concatenated string: '{result_string}'")


# %%
"""
QUESTION 
"""
bins = [-float('inf'), 300, 600, float('inf')]
labels = ['Low', 'Medium', 'High']
df['elevation_category'] = pd.cut(df['elevation'], bins=bins, labels=labels)

# Create violin plot
plt.figure(figsize=(10, 6))
sns.violinplot(x='elevation_category', y='annual_yield', data=df,
               order=['Low', 'Medium', 'High'],
               palette='viridis')

plt.title('Distribution of Annual Yield Across Elevation Ranges', fontsize=14)
plt.xlabel('Elevation Category', fontsize=12)
plt.ylabel('Annual Yield (kg)', fontsize=12)
plt.tight_layout()
plt.show()

# %%

# Get unique crop types
unique_crops = df['crop_type'].unique().tolist()

# Recursive function to sum the lengths of strings in a list
def sum_string_lengths(crop_list, index=0):
    """
    Recursively sums the lengths of strings in a list.
    
    Parameters:
    crop_list: List of crop type strings
    index: Current position in the list
    
    Returns:
    Total sum of string lengths
    """
    # Base case: if we've processed all elements
    if index >= len(crop_list):
        return 0
    
    # Recursive case: add length of current string + sum of remaining
    return len(crop_list[index]) + sum_string_lengths(crop_list, index + 1)

# Calculate the sum
total_sum = sum_string_lengths(unique_crops)

print(f"Unique crop types: {unique_crops}")
print(f"Sum of lengths of all unique crop type names: {total_sum}")

# %%

# Filter data for coffee and banana
coffee_yield = df[df['crop_type'] == 'coffee']['annual_yield']
banana_yield = df[df['crop_type'] == 'banana']['annual_yield']

# Perform independent t-test
t_stat, p_value = stats.ttest_ind(coffee_yield, banana_yield, equal_var=True)

# Round p-value to 3 decimal places
p_value_rounded = round(p_value, 3)

print(f"T-statistic: {t_stat:.4f}")
print(f"P-value: {p_value:.4f}")
print(f"P-value (rounded to 3 decimal places): {p_value_rounded}")
# %%
