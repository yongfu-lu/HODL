from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.client import TradingClient

from algorithm import Algorithm

import os
import psycopg2

def main():

    try:   
        # print(os.environ)
        conn = psycopg2.connect(
                            host="",
                            database="",
                            user="",
                            password=""
        )
        cur = conn.cursor()
        print("Connected to PostgreSQL database!\n")

        # execute SQL query to get table names
        # cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ")

        # table_names = [row[0] for row in cur.fetchall()]

        # print(table_names)
        # print("\n")

        cur.execute("""SELECT id, username, api_key, secret_key FROM user_customuser
                                                            WHERE (api_key != '' OR api_key IS NULL)
                                                            AND (secret_key != '' OR secret_key IS NULL)""")
        users = cur.fetchall()
        for user in users:
            print(user)
            try:
                hist_client = StockHistoricalDataClient(user[2], user[3])
                trad_client = TradingClient(user[2], user[3], paper=True)

                user_algos = Algorithm(user[2], hist_client, trad_client, 5)

                cur.execute("""SELECT * FROM user_activatedalgorithm WHERE user_id={id}""".format(id = user[0]))

                act_algos = cur.fetchall()

                for act_algo in act_algos:
                    print(act_algo)
                    # Goes through each act_algo and runs the corresponding execute algo function
                    if act_algo[1] == 'moving-average':
                        user_algos.execute_ma(act_algo[2], act_algo[3], act_algo[4], act_algo[5])

                    elif act_algo[1] == 'relative-strength-indicator':
                        user_algos.execute_rsi(act_algo[2], act_algo[3], act_algo[6], act_algo[7], act_algo[8])

                    elif act_algo[1] == 'bollinger-bands':
                        user_algos.execute_bb(act_algo[2], act_algo[3], act_algo[6], act_algo[9])

                    elif act_algo[1] == 'average-true-range':
                        user_algos.execute_atr(act_algo[2], act_algo[3], act_algo[4], act_algo[5])

                    elif act_algo[1] == 'MACD-with-fibonacci-levels':
                        user_algos.execute_fib(act_algo[2], act_algo[3], act_algo[4], act_algo[5])
            
            except:
                continue

            print('\n')

        print('\n')
    
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        print(error.with_traceback)
    
    finally:
        # closes the database connection
        if (conn):
            cur.close()
            conn.close()
            print("\nPostgreSQL connection is closed")


main()