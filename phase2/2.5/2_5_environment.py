# -*- coding: utf-8 -*-
"""2.5 Environment.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1dqKhg8BQnm6yh14l4vcBZRZG0cZpqJIb
"""

import numpy as np
import pandas as pd
import pickle
import gym
from google.colab import files
import tensorflow as tf
from tensorflow import keras

# https://github.com/openai/gym/tree/master/gym/spaces

files.upload()

pickle_in = open("scalerX.pickle","rb")
scalerX = pickle.load(pickle_in)
pickle_in = open("scalery.pickle","rb")
scalery = pickle.load(pickle_in)

Call_model = tf.keras.models.load_model('2.5Call_LR0.01.h5')
Call_data = pd.read_csv("Call_data.csv")

class OptionsTradingEnv(gym.Env):
    """
    An Options trading environment for OpenAI gym
    """
    # - human: render to the current display or terminal and return nothing. 
    # Usually for human consumption.
    metadata = {'render.modes': ['human']}

    def __init__(self, df):
        super(OptionsTradingEnv, self).__init__()
        self.df = df
        self.days = df['START_DATE'].unique()
        self.underlying_asset_price = df['UNDERLYING'].unique()

    # private method
    def _next_observation(self): 
        # Get the Options chain 
        observation = self.df[self.df['START_DATE'] == self.days[self.current_step]]
        self.observation = observation

        return observation

    def _take_action(self, action):
        # # action in dict type with keys buy and sell
        # contracts_to_buy = action['Buy']
        # contracts_to_sell = action['Sell']
        for i in range(len(action)):
            # Assume the bought price is the ask price
            options_price = self.observation['ASK'].iloc[action[i]]
            if self.balance >= options_price:
                contract = {
                    'START_DATE': self.observation['START_DATE'].iloc[action[i]],
                    'SKRIKE': self.observation['SKRIKE'].iloc[action[i]],
                    'ASK': options_price,
                    'END_DATE': self.observation['END_DATE'].iloc[action[i]]
                }
                self.Bought_contracts.append(contract)
                self.balance -= options_price

    def step(self, action):
        # Execute one time step within the environment
        self._take_action(action)
        self.current_step += 1

        if self.current_step >= len(self.days):
            done = True
            return [], self.net_worth, done
        
        number_of_contracts = len(self.Bought_contracts)
        contracts_to_sell = []
        contracts_profit = 0
        if number_of_contracts > 0:
            for i in range(number_of_contracts):
                # Profit for call options
                profit = max(0, self.underlying_asset_price[self.current_step] - self.Bought_contracts[i]['SKRIKE'])
                if self.Bought_contracts[i]['END_DATE'] == self.days[self.current_step]:
                    # This is at the expiration date
                    self.balance += profit
                    # Delete the contract from the list
                    contracts_to_sell.append(i)
                elif profit - self.Bought_contracts[i]['ASK'] > 0:
                    # Exercise the contract with probability ACT_RATE
                    if np.random.binomial(n = 1, p = self.act_rate) == 1:
                        self.balance += profit
                        contracts_to_sell.append(i)
                else:
                    contracts_profit += profit
 
        self.net_worth = self.balance + contracts_profit
        # Delete all the exercised contracts
        self.Bought_contracts = [self.Bought_contracts[i] for i in range(number_of_contracts) if i not in contracts_to_sell]

        done = self.net_worth <= 0
        obs = self._next_observation()

        return obs, self.net_worth, done

    def reset(self):
        # Reset the state of the environment to an initial state
        self.balance = INITIAL_ACCOUNT_BALANCE
        self.net_worth = INITIAL_ACCOUNT_BALANCE
        self.act_rate = ACT_RATE

        # Set the current step to 0
        self.current_step = 0
        self.Bought_contracts = []

        return self._next_observation()

    def render(self, mode = 'human', show = False):
        # Render the environment to the screen
        print(self.current_step)
        # print(self.Bought_contracts)
        print(self.balance)
        print('The current net worth is', self.net_worth)

INITIAL_ACCOUNT_BALANCE = 1000
Features = ['UNDERLYING', 'SKRIKE', 'MATURITY', 'DELTA', 'BID', 'ASK', 'IMPLIED_VOL', 'LIQUIDITY', 'INTEREST_RATE']

profit_list = []
for ACT_RATE in np.arange(0.5, 1, 0.05):
    profit = []
    for _ in range(20):
        Env = OptionsTradingEnv(Call_data)
        cur_state = Env.reset()
        done = False
        while not done:
            X = scalerX.transform(cur_state[Features].values)
            Options_price_pred = scalery.inverse_transform(Call_model.predict(X))
            # Buy undervalued call options
            price_diff = Options_price_pred.reshape(-1) - cur_state['ASK'].values
            if sum(price_diff > 0) > 5:
                action = np.argsort(price_diff)[::-1][:5]
            else:
                action = np.argsort(price_diff)[::-1][:sum(price_diff > 0)]
            cur_state, NETWORTH, done = Env.step(action)
            # Env.render()
        profit.append(Env.net_worth - INITIAL_ACCOUNT_BALANCE)
    profit_list.append((np.mean(profit), np.std(profit)))
profit_list

profit_list = []
for ACT_RATE in np.arange(0.5, 1, 0.05):
    profit = []
    for _ in range(20):
        Env = OptionsTradingEnv(Call_data)
        cur_state = Env.reset()
        done = False
        while not done:
            action = np.random.choice(np.arange(cur_state.shape[0]), size = 5, replace = False)
            cur_state, NETWORTH, done = Env.step(action)
            # Env.render()
        profit.append(Env.net_worth - INITIAL_ACCOUNT_BALANCE)
    profit_list.append((np.mean(profit), np.std(profit)))
profit_list