import pandas as pd

# Create a sample DataFrame with two columns
df = pd.DataFrame({'A': [1, 2, 3, 4, 5], 'B': [5, 4, 3, 2, 1]})

# Create a new column that calculates the difference between column A and column B
df['diff'] = df['A'] - df['B']

# Create a new column that calculates the sign of the difference
df['sign'] = df['diff'].apply(lambda x: '+' if x > 0 else '-')

# Create a new column that detects when the two integers cross each other
df['cross'] = df['sign'] != df['sign'].shift()

# Print the resulting DataFrame
print(df)
