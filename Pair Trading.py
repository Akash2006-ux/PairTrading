#This program is used for trading in pairs this is the basic implementation of the program

import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib
try:
    matplotlib.use('QT5Agg')
except:
    pass
import matplotlib.pyplot as plt

def get_data(ticker, period = '4y'):
    stock = yf.Ticker(ticker)
    return stock.history(period)


def run_pairs(ticker_one, ticker_two, period = '4y'):
    series_one = get_data(ticker_one, period)
    series_two = get_data(ticker_two, period)

    df1 = series_one[['Open', 'High', 'Low', 'Close']].add_prefix(f'{ticker_one} ')
    df2 = series_two[['Open', 'High', 'Low', 'Close']].add_prefix(f'{ticker_two} ')

    #This is to combine the dates of the two stocks
    df = pd.concat([df1, df2], axis=1).dropna()
    df = df.reset_index()
    df['Date'] = df['Date'].dt.date

    #This is to calculate the average price
    df[f'{ticker_one} AVG'] = (df[f'{ticker_one} Open'] + df[f'{ticker_one} High'] + df[f'{ticker_one} Low'] +
                               df[f'{ticker_one} Close']) / 4
    df[f'{ticker_two} AVG'] = (df[f'{ticker_two} Open'] + df[f'{ticker_two} High'] + df[f'{ticker_two} Low'] +
                               df[f'{ticker_two} Close']) / 4

    #This is to find the ratio
    df['Ratio'] = np.where(df[f'{ticker_one} AVG'] >= df[f'{ticker_two} AVG'],
                           df[f'{ticker_one} AVG'] / df[f'{ticker_two} AVG'],
                           df[f'{ticker_two} AVG'] / df[f'{ticker_one} AVG'])

    df['5 DMA'] = df['Ratio'].rolling(window=5).mean()
    df['20 DMA'] = df['Ratio'].rolling(window=20).mean()
    df['20 STD'] = df['Ratio'].rolling(window=20).std()
    df['Z-Score'] = (df['5 DMA'] - df['20 DMA']) / df['20 STD']

    #This is the signaling logic
    conditions = [
        (df['Z-Score'] < -1.1),
        (df['Z-Score'] > 1.1)
    ]
    choices = [f'BUY {ticker_two}', f'BUY {ticker_one}']
    df['Signal'] = np.select(conditions, choices, default = 'No Trade')

    #This is the quantity calculation
    df[f'{ticker_one}-Q'] = np.where(df['Signal'] == f'BUY {ticker_one}',1, 0)
    df[f'{ticker_two}-Q'] = np.where(df['Signal'] == f'BUY {ticker_two}',1, 0)

    #This is the amount calculation
    df[f'{ticker_one}-AMT'] = df[f'{ticker_one}-Q'] * df[f'{ticker_one} AVG']
    df[f'{ticker_two}-AMT'] = df[f'{ticker_two}-Q'] * df[f'{ticker_two} AVG']

    #This is to calculate the cumulative quantity
    df[f'{ticker_one}-CUMQ'] = df[f'{ticker_one}-Q'].cumsum()
    df[f'{ticker_two}-CUMQ'] = df[f'{ticker_two}-Q'].cumsum()

    #This is to calculate the cumulative amount
    df['CUM-AMT'] = df[f'{ticker_one}-AMT'].cumsum() + df[f'{ticker_two}-AMT'].cumsum()

    #This is the M2M
    df['M2M'] = (df[f'{ticker_one}-CUMQ'] * df[f'{ticker_one} Close']) + (df[f'{ticker_two}-CUMQ'] *
                                                                          df[f'{ticker_two} Close'])

    #This is the Profit
    df['Profit'] = df['M2M'] - df['CUM-AMT']

    #This is the profit percentage
    df['Profit%'] = np.where(df['CUM-AMT']!=0,((df['M2M'] - df['CUM-AMT'])/df['CUM-AMT']) * 100, 0)

    #This is to display all the columns
    column_view = [
        'Date',
        f'{ticker_one} Open', f'{ticker_one} High', f'{ticker_one} Low', f'{ticker_one} Close',
        f'{ticker_two} Open', f'{ticker_two} High', f'{ticker_two} Low', f'{ticker_two} Close',
        f'{ticker_one} AVG', f'{ticker_two} AVG', 'Ratio', '5 DMA', '20 DMA', '20 STD', 'Z-Score',
        'Signal', f'{ticker_one}-Q', f'{ticker_two}-Q', f'{ticker_one}-AMT', f'{ticker_two}-AMT',
        f'{ticker_one}-CUMQ', f'{ticker_two}-CUMQ', 'CUM-AMT', 'M2M', 'Profit', 'Profit%'
    ]
    print("\n" + "=" * 267)
    print("Pair Trading Results".center(267))
    print("=" * 267)
    print(df[column_view].to_string(index=False, float_format='%.4f'))

    #This is to plot the Z-Score
    # --- Plotting the Z-Score ---
    plt.figure(figsize=(14, 6))
    plt.plot(df['Date'], df['Z-Score'], label='Z-Score', color='blue', linewidth=1)

    # This is to Add horizontal lines for your 1.35 thresholds (Matching the Excel formula)
    plt.axhline(1.1, color='red', linestyle='--', label='Buy (1.1)')
    plt.axhline(-1.1, color='green', linestyle='--', label='Buy (-1.1)')
    plt.axhline(0, color='black', linewidth=0.5)  # Zero line

    # Fill the areas where signals are triggered
    plt.fill_between(df['Date'], df['Z-Score'], 1.1, where=(df['Z-Score'] >= 1.1), color='red', alpha=0.2)
    plt.fill_between(df['Date'], df['Z-Score'], -1.1, where=(df['Z-Score'] <= -1.1), color='green', alpha=0.2)

    # Formatting the chart
    plt.title(f'Z-Score Analysis: {ticker_one} vs {ticker_two} (4 Years)')
    plt.xlabel('Date')
    plt.ylabel('Z-Score')
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.3)

    # Show the plot if you are running in PyCharm/VS Code
    plt.show()



    #This is a separate display of profit and loss
    # Display the summary
    print("\n" + '=' * 59)
    print("Summary:")
    print("=" * 59)
    total_Profit = df["Profit"].sum()
    avg_Profit = df["Profit%"].mean()
    max_Profit = df["Profit%"].max()
    min_Profit = df["Profit%"].min()

    #Print the results
    print(f"Total Profit: ${total_Profit:,.4f}")
    print(f"Avg. Profit%: {avg_Profit:,.2f}%")
    print(f"Max Profit%: {max_Profit:,.2f}%")
    print(f"Min Profit%: {min_Profit:,.2f}%")

    # Define the file name based on the tickers
    #excel_file = f"{ticker_one}_{ticker_two}_Analysis.xlsx"

    # Export to Excel
    # index=False removes the row numbers so it looks clean
    #df.to_excel(excel_file, index=False)

    #print(f"\n" + "=" * 60)
    #print(f"SUCCESS: 4 years of data exported to {excel_file}")
    #print(f"=" * 60)





def main():
    print("-----------------Welcome to Pair Trading!---------------")
    while True:
        print("--------------------------------------------------------")
        ticker_one = input("Enter the 1st ticker to analyze (e.g., AAPL) or Q to quit: ").upper()
        if ticker_one == 'Q':
            return True
        ticker_two = input("Enter the 2nd ticker to analyze (e.g., MSFT) or Q to quit: ").upper()
        if ticker_two == 'Q':
            return True

        run_pairs(ticker_one, ticker_two, period='4y')
        # The quit option after running
        print("\n" + '=' * 59)
        choice = input("Would you like to continue? (Y/N): ").upper()

        if choice == 'N':
            print("\n"+"Thank you for choosing to use Pair Trading. Goodbye!")
            return True


if __name__ == '__main__':
    main()
