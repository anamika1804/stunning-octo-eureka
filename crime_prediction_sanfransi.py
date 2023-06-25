# -*- coding: utf-8 -*-
"""crime-prediction-sanFransi.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1PiEmUdbjhl_HXHXs-p54muMpyM1cN7ca
"""

pip show scikit-learn

!pip install scikit-optimize

import numpy as np
import pandas as pd

import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib import style

# Algorithms
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB

# Preprocessing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

from sklearn.cluster import KMeans

# Metrics
from sklearn.metrics import log_loss
from sklearn.model_selection import cross_val_score

import skopt
from skopt.space  import Real, Categorical, Integer
import math

train_df = pd.read_csv('train.csv.zip')
test_df = pd.read_csv('test.csv.zip')

train_df.info()

train_df.head(8)

train_df.columns.values

# set show nulls to True
train_df.info(verbose=True, null_counts=True)

## Count number of observations for each crime
train_df['Category'].value_counts()

## Count number of observations of crime for each PD District
train_df['PdDistrict'].value_counts()

## Count number of observations for each day of week
train_df['DayOfWeek'].value_counts()

## Count number of observations for Resolution feature
train_df['Resolution'].value_counts()

train_df[['X','Y']].describe()

train_df[train_df['Y'] == train_df['Y'].max()]

train_df['Y'].replace(to_replace= train_df['Y'].max() ,value=np.nan, inplace=True)
train_df['X'].replace(to_replace= train_df['X'].max() ,value=np.nan, inplace=True)
test_df['Y'].replace(to_replace= test_df['Y'].max() ,value=np.nan, inplace=True)
test_df['X'].replace(to_replace= test_df['X'].max() ,value=np.nan, inplace=True)

train_df.isnull().sum()

test_df.isnull().sum()

train_df[['X', 'Y']].describe()

len(train_df)

test_df[['X', 'Y']].describe()

len(test_df)

"""# Feature Engineering

## Temporal Features
"""

# Transform the Date into a python datetime object.
train_df["Dates"] = pd.to_datetime(train_df["Dates"], format="%Y-%m-%d %H:%M:%S")
test_df["Dates"] = pd.to_datetime(test_df["Dates"], format="%Y-%m-%d %H:%M:%S")

# Minute
train_df["Minute"] = train_df["Dates"].map(lambda x: x.minute)
test_df["Minute"] = test_df["Dates"].map(lambda x: x.minute)

# Hour
train_df["Hour"] = train_df["Dates"].map(lambda x: x.hour)
test_df["Hour"] = test_df["Dates"].map(lambda x: x.hour)

# Day
train_df["Day"] = train_df["Dates"].map(lambda x: x.day)
test_df["Day"] = test_df["Dates"].map(lambda x: x.day)

# Month
train_df["Month"] = train_df["Dates"].map(lambda x: x.month)
test_df["Month"] = test_df["Dates"].map(lambda x: x.month)

# Year
train_df["Year"] = train_df["Dates"].map(lambda x: x.year)
test_df["Year"] = test_df["Dates"].map(lambda x: x.year)

# Hour Zone 0 - Pass midnight, 1 - morning, 2 - afternoon, 3 - dinner / sun set, 4 - night
def get_hour_zone(hour):
    if hour >= 2 and hour < 8:
        return 0
    elif hour >= 8 and hour < 12:
        return 1
    elif hour >= 12 and hour < 18:
        return 2
    elif hour >= 18 and hour < 22:
        return 3
    elif hour < 2 or hour >= 22:
        return 4

train_df["Hour_Zone"] = train_df["Hour"].map(get_hour_zone)
test_df["Hour_Zone"] = test_df["Hour"].map(get_hour_zone)

# Add Week of Year
train_df["WeekOfYear"] = train_df["Dates"].map(lambda x: int(x.weekofyear / 2) - 1)
test_df["WeekOfYear"] = test_df["Dates"].map(lambda x: int(x.weekofyear / 2))

print(sorted(train_df['WeekOfYear'].unique()))
print(sorted(test_df['WeekOfYear'].unique()))

train_df.head()

"""### Holiday Feature

- Certain crimes may be more apparent on holidays
"""

from pandas.tseries.holiday import USFederalHolidayCalendar as calendar

# Training set
cal = calendar()
holidays = cal.holidays(start=train_df['Dates'].min(), end=train_df['Dates'].max())
train_df['Holiday'] = train_df['Dates'].dt.date.astype('datetime64').isin(holidays)

# Test set
cal = calendar()
holidays = cal.holidays(start=test_df['Dates'].min(), end=test_df['Dates'].max())
test_df['Holiday'] = test_df['Dates'].dt.date.astype('datetime64').isin(holidays)

len(train_df[train_df['Holiday'] == True])

len(test_df[test_df['Holiday'] == True])

## 1 is typical business hours [8:00AM - 6:00PM] 0 is not business hours [6:01PM - 7:59 AM]
from datetime import datetime, time

def time_in_range(start, end, x):
    """Return true if x is in the inclusive range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end

def map_business_hours(date):

    # Convert military time to AM & PM
    time_parsed = date.time()
    business_start = time(8, 0, 0)
    business_end = time(18, 0, 0)

    if time_in_range(business_start, business_end, time_parsed):
        return 1
    else:
        return 0

train_df['BusinessHour'] = train_df['Dates'].map(map_business_hours).astype('uint8')
test_df['BusinessHour'] = test_df['Dates'].map(map_business_hours).astype('uint8')

train_df['BusinessHour'].value_counts()

train_df.head(10)

"""### Season

The season feature may affect what type of crimes are commited.
- 1 = Winter, 2 = Spring, 3 = Summer, 4 = Fall
"""

train_df['Season']=(train_df['Month']%12 + 3)//3
test_df['Season']=(test_df['Month']%12 + 3)//3

train_df.head()

# Weekend Feature

# Weekday = 0, Weekend = 1
days = {'Monday':0 ,'Tuesday':0 ,'Wednesday':0 ,'Thursday':0 ,'Friday':0, 'Saturday':1 ,'Sunday':1}

train_df['Weekend'] = train_df['DayOfWeek'].replace(days).astype('uint8')
test_df['Weekend'] = test_df['DayOfWeek'].replace(days).astype('uint8')

"""### Street Type."""

train_df['Address'].value_counts().index

import re


def find_streets(address):
    street_types = ['AV', 'ST', 'CT', 'PZ', 'LN', 'DR', 'PL', 'HY',
                    'FY', 'WY', 'TR', 'RD', 'BL', 'WAY', 'CR', 'AL', 'I-80',
                    'RW', 'WK','EL CAMINO DEL MAR']
    street_pattern = '|'.join(street_types)
    streets = re.findall(street_pattern, address)
    if len(streets) == 0:
        # Debug
#         print(address)
        return 'OTHER'
    elif len(streets) == 1:
        return streets[0]
    else:
#         print(address)
        return 'INT'

train_df['StreetType'] = train_df['Address'].map(find_streets)
test_df['StreetType'] = test_df['Address'].map(find_streets)

train_df['StreetType'].value_counts()

# Check for null values
train_df['StreetType'].isnull().sum()

train_df.head(8)

"""## Block Features (Removed)

- Let's explore and create the block feature, since we saw it a lot in the address features
- Binary feature
    - Categorize address that contains 'Block', as having a block, and if no block exists, we will assign to 0.
- 617231 addresses with blocks
- 260818 addresses with no blocks
"""

# def find_block(address):
#     block_pattern = 'Block'
#     blocks = re.search(block_pattern, address)
#     if blocks:
# #         print(address)
#         return 1
#     else:
# #         print(address)
#         return 0


# train_df['Block'] = train_df['Address'].map(find_block)
# test_df['Block'] = test_df['Address'].map(find_block)

# train_df['Block'].value_counts()

"""## Block Number Feature

- Let's explore the block number from address
- Block number has ordinal data type (order matters), and has spatial significance
- It seems all the block numbers are in intervals of 100
- How to categorize
    - Addresses that do not have a block number will be categorized as 0
    - Addresses with block number will be divided by 100, and added by 1 for mapping (0 is saved for addresses with no block number)
- 85 unique block numbers (including 1 where there is no block number)
"""

def find_block_number(address):
    block_num_pattern = '[0-9]+\s[Block]'
    block_num = re.search(block_num_pattern, address)
    if block_num:
#         print(address)
        num_pattern = '[0-9]+'
        block_no_pos = re.search(num_pattern, address)
        # Get integer of found regular expression
        block_no = int(block_no_pos.group())
        # Convert block number by dividing by 100 and adding 1 (0 = addresses with no block)
        block_map = (block_no // 100) + 1
#         print(block_map)
        return block_map
    else:
#         print(address)
        #
        return 0


train_df['BlockNo'] = train_df['Address'].map(find_block_number)
test_df['BlockNo'] = test_df['Address'].map(find_block_number)

train_df['BlockNo'].value_counts()

"""## Drop Features

- We have already extracted all the necessary features from the `Address` attribute, so drop
- We don't need `Resolution` or `Descript` features since it is not included in the training data
"""

# Drop Address feature from both train and test set
train_df.drop(['Address'], axis=1, inplace=True)
test_df.drop(['Address'], axis=1, inplace=True)

# We don't need Dates column anymore
train_df.drop(['Dates'], axis=1, inplace=True)
test_df.drop(['Dates'], axis=1, inplace=True)

# Drop Resolution column since test set does not have this column
train_df.drop(['Resolution'], axis=1, inplace=True)

# Drop Descript column since test set does not have this column
train_df.drop(['Descript'], axis=1, inplace=True)

# Let's quickly view the data
train_df.head()

"""# Feature Encoding

- Convert categorical data to numeric data

### Pd Districts

- convert Pd District categorical feature to numeric
"""

pd_districts = {'SOUTHERN':0, 'MISSION':1, 'NORTHERN':2, 'CENTRAL':3, 'BAYVIEW':4, 'INGLESIDE':5,
                'TENDERLOIN':6, 'TARAVAL':7, 'PARK':8, 'RICHMOND':9}

train_df['PdDistrict'].replace(pd_districts, inplace=True)
test_df['PdDistrict'].replace(pd_districts, inplace=True)

train_df.head()

train_df.info()

"""### Year

- Year is an **ordinal** variable, so let's keep that ordering and mapping
- convert Year categorical feature to numeric
"""

data = [train_df, test_df]

for dataset in data:
    year_le = LabelEncoder()
    year_le.fit(dataset['Year'].unique())
    print(list(year_le.classes_))

    dataset['Year']=year_le.transform(dataset['Year'])

train_df['Year'].unique()

# So we know the mapping (important)
dict(zip(year_le.classes_, year_le.transform(year_le.classes_)))

train_df.head()

train_df.info()

"""### DayOfWeek

- we are going to use sklearn's LabelEncoder to encode the categorical data to numeric
- Day of week is considered a categorical and nominal variable
"""

data = [train_df, test_df]

for dataset in data:
    dow_le = LabelEncoder()
    dow_le.fit(dataset['DayOfWeek'].unique())
    print(list(dow_le.classes_))
    dataset['DayOfWeek']=dow_le.transform(dataset['DayOfWeek'])

train_df['DayOfWeek'].unique()

# So we know the mapping (important)
dict(zip(dow_le.classes_, dow_le.transform(dow_le.classes_)))

train_df.head()

train_df.info()

"""### Street Type

- we are going to use sklearn's LabelEncoder to encode the categorical data to numeric
"""

data = [train_df, test_df]

for dataset in data:
    st_le = LabelEncoder()
    st_le.fit(dataset['StreetType'].unique())
    print(list(st_le.classes_))
    dataset['StreetType']=st_le.transform(dataset['StreetType'])

train_df['StreetType'].unique()

train_df.head()

train_df.info()

"""### Holiday

- Encode the binary feature
"""

# Encode to 0 and 1

train_df['Holiday'].replace(False, 0, inplace=True)
train_df['Holiday'].replace(True, 1, inplace=True)
test_df['Holiday'].replace(False, 0, inplace=True)
test_df['Holiday'].replace(True, 1, inplace=True)

train_df['Holiday'] = train_df['Holiday'].astype('uint8')
train_df['Holiday'] = train_df['Holiday'].astype('uint8')

train_df[train_df['Holiday'] == 1].head()

test_df[test_df['Holiday'] == 1].head()

"""### Category

- we are going to use sklearn's LabelEncoder to encode the categorical data to numeric
"""

data = [train_df]

for dataset in data:
    cat_le = LabelEncoder()
    cat_le.fit(dataset['Category'].unique())
    print(list(cat_le.classes_))
    dataset['Category']=cat_le.transform(dataset['Category'])

len(train_df['Category'].unique())

# So we know the mapping (important)
dict(zip(cat_le.classes_, cat_le.transform(cat_le.classes_)))

train_df.head()

train_df.info()

"""## View Information about Data

- One last check before training
"""

train_df.info()

"""# Building Machine Learning Models

1. Logistic
2. Random Forest
3. Naive Bayes Classifier
"""

# Set training data (drop labels) and training labels
X_train = train_df.drop("Category", axis=1).copy()
Y_train = train_df["Category"].copy()

# Set testing data (drop Id)
X_test = test_df.drop("Id", axis=1).copy()

def one_hot_encode(train_data):
    '''One Hot Encode the categorical features'''
    encoded_train_data = train_data

    encoded_train_data = pd.concat([encoded_train_data,
                                    pd.get_dummies(pd.Series(encoded_train_data['PdDistrict']), prefix='PdDistrict')], axis=1)
    encoded_train_data = pd.concat([encoded_train_data,
                                    pd.get_dummies(pd.Series(encoded_train_data['DayOfWeek']), prefix='DayOfWeek')], axis=1)
    encoded_train_data = pd.concat([encoded_train_data,
                                    pd.get_dummies(pd.Series(encoded_train_data['StreetType']), prefix='StreetType')], axis=1)
    encoded_train_data = pd.concat([encoded_train_data,
                                    pd.get_dummies(pd.Series(encoded_train_data['Season']), prefix='Season')], axis=1)
    encoded_train_data = pd.concat([encoded_train_data,
                                    pd.get_dummies(pd.Series(encoded_train_data['Hour_Zone']), prefix='Hour_Zone')], axis=1)
    encoded_train_data = pd.concat([encoded_train_data,
                                    pd.get_dummies(pd.Series(encoded_train_data['Cluster']), prefix='Cluster')], axis=1)
    encoded_train_data = encoded_train_data.drop(['Cluster','StreetType', 'Season', 'Hour_Zone', 'DayOfWeek', 'PdDistrict'], axis=1)

    return encoded_train_data

#X_encoded_train = one_hot_encode(X_train)

# Use these for ML algorithms that can handle categorical data without OHE
mini_train_data, mini_dev_data, mini_train_labels, mini_dev_labels = train_test_split(X_train,
                                                                                      Y_train,
                                                                                      stratify=Y_train,
                                                                                      test_size=0.5,
                                                                                      random_state=1)