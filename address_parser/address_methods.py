# -*- coding: utf-8 -*-

### Import libraries
from fuzzywuzzy import fuzz
import numpy as np
import os, sys, inspect
import pandas as pd
import pickle
import re

# Import submodules
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(\
                inspect.getfile( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
     sys.path.insert(0, cmd_folder)

import resource_manager
from address_parser_class import AddressParser


def load_sample():
    return ResourceManager().load_sample()


def parse_street_series(series, target_df=None):
    """ Run AddressParser().parse_street
    Args:
        series (pd.Series): series containing address info
        target_df (pd.DataFrame): df containing results

    Returns:
        five pd.Series objects:
            (steet_number, street_name, street_prefix, street_suffix, other).
            If target_df is not None, these will be stored in
            (target_df['Street Number'], target_df['Street Name'],
            target_df['Street Prefix'], target_df['Street Suffix'],
            target_df['Other Address'])
    """
    parse_street = AddressParser().parse_street

    if target_df is not None:
        target_df['Street Number'], target_df['Street Name'], \
        target_df['Street Prefix'], target_df['Street Suffix'], \
        target_df['Other Address'] = \
            zip(*series.fillna("").apply(parse_street))
        return target_df
    else:
        return zip(*series.fillna("").apply(parse_street))


def combine_address_row(row):
    """ Combines street addresses on a row level
    Args:
        one row that contains variables "Street Prefix", "Street Number",
            "Street Name", "Street Suffix"
    Returns:
        str with one combined address
    """
    if row['Street Prefix'] == "":
        ans = row['Street Number'] + ' ' + row['Street Name'] + ' ' + row['Street Suffix']
    else:
        ans = row['Street Number'] + ' ' + row['Street Prefix'] + ' ' + \
        row['Street Name'] + ' ' + row['Street Suffix']
    return ans.strip()


def combine_address_df(df):
    """ Combines street addresses on a row level
    Args:
        one row that contains variables "Street Prefix", "Street Number",
            "Street Name", "Street Suffix"
    Returns:
        df such that df['Addres_s'] is the combined addreess
    """
    df = df.apply(combine_address_row, axis=1)
    return df


def get_unique(df, col_name):
    """ Return all unique street names
    Args:
        df (pd.DataFrame): input df.
        col_name (str): column name in df.
    Returns:
        set containing all unique values in this column
    """
    return set(df[col_name].unique())


def get_combinations_as_df(df, cols):
    """ Return all unique combinations of values in columns
    Args:
        df (pd.DataFrame): input df.
        cols (list): column names in df.
    Returns:
        df containing all unique combinations with frequency of each
    """
    return df[cols].groupby(cols).size().reset_index()


def get_combinations_as_set(df, cols):
    """ Return all unique combinations of values in columns
    Args:
        df (pd.DataFrame): input df.
        cols (list): column names in df.
    Returns:
        set containing all unique combinations. Each combination is a tuple
    """
    cols = list(cols)
    return set(df[cols].groupby(cols).size().index)


def get_combinations_as_dict(df, cols):
    """ Return all unique combinations of values in columns
    Args:
        df (pd.DataFrame): input df.
        cols (list): 2 or more column names
    Returns:
        d (dict): for a value v in cols[1:], d[v] = dict,
                  where d[v][value] = set containing all distinct values of v correponsing to value
    """

    grouped = df[cols].groupby(cols[0])[cols[1:]].agg(lambda x: set(x))[cols[1]]
    return grouped.to_dict()


def gen_close_match_row(name_col, suffix_col,
                        standard_address_set, standard_name_set,
                        name_to_suffix_dict):
    """ Apply close_match method AddressParser() on row
    Args:
        name_col (str): col containing Street Name
        suffix_col (str): col containing Street Suffix
        standard_address_set (set): all standard full addresses
        standard_name_set (set): all standard full name
        name_to_suffix_dict (dict): name to suffix dict

    Return:
        a callable function that takes a row and returns the tuple
            (matched_name, matched_suffix, ratio)
    """

    def callable(row):
        return AddressParser().close_match(
                                row[name_col], row[suffix_col],
                                standard_address_set, standard_name_set,
                                name_to_suffix_dict)
    return callable

def get_freq(series):
    """ Return frequency of values in series
    Args:
        series (pd.Series)
    Returns:
        d (dict). d[value] = count
    """
    return series.value_counts().to_dict()


def gen_fill_suffix_row(row, name_to_suffix_dict,
                        street_name_col, street_suffix_col,
                        suggested_name_col=None, suggested_suffix_col=None):
    """ Returns a callable that suggests suffix based on row information
    Args:
        row: a row in DataFrame
        name_to_suffix_dict (dict)
        street_name_col (str)
        street_suffix_col (str)
        suggested_name_col (str)
        suggested_suffix_col (str)

    Returns:
        a callable that takes row as argument and returns suggested suffix
    """

    # If suffix is not missing, return suffix
    if (row[street_suffix_col] != ""):
        return row[street_suffix_col]

    # If suffix is missing, find match
    if suggested_name_col is None:
        suggested_name_col = street_name_col
    if suggested_suffix_col is None:
        suggested_suffix_col = street_suffix_col
    name = ''
    if (row[suggested_name_col] != ""):
        name = row[suggested_name_col]
    else:
        name = row[street_name_col]

    # Generate callable
    def callable(row):
        ans = AddressParser().fill_suffix(name, name_to_suffix_dict)
        if ans == "":
            return AddressParser().strip(row[suggested_suffix_col])
        else:
            return ans

    return callable


def get_pin_len(df, pin_col_name='Parcel Number'):
    if pin_col_name not in df.columns:
        pin_col_name = 'PIN'
    df['PIN_len'] = df[pin_col_name].apply(lambda x: len(str(x)))
    return df

######################################################################
########## The following are used to merge transaction data with
########## public record data
######################################################################

def gen_raw_index(df):
    return df.reset_index().rename(columns={'index':'index_raw'})

def gen_PIN_len(df):
    df['PIN_len'] = df['PIN'].apply(lambda x: len(str(x)))
    return df

def clean_PIN_by_row(row):
    try:
      if row['PIN_len']==12 and str(row['PIN'])[:2]=='50':
        return str(row['PIN'])[2:]
    except:
        pass
    return str(row['PIN'])

def split_mult_PIN(x):
    if any([c.isnumeric() for c in x]):
        temp = re.split("[^\d]", x)
        ans = []
        for i,p in enumerate(temp):
            if len(p)>0:
                ans.append(temp[0][:-len(p)] + p)
        return ans
    else:
        return [x]

def gen_mult_PIN_list(df):
    df['PIN'] = df.apply(clean_PIN_by_row, axis=1)
    df['temp'] = df['PIN'].astype('str').apply(split_mult_PIN)
    return df

def split_PIN_list(df):
    return pd.DataFrame({col: np.repeat( df[col].values, df['temp'].str.len() ) \
            for col in df.columns.drop('temp') })\
            .assign(**{'temp':np.concatenate(df['temp'].values)})[df.columns]

def gen_index(df):
    return df.reset_index().rename(columns={'index':'index_clean'})

def clean_temp_col(df):
    df['PIN'] = df['temp']
    return df.drop(columns=['PIN_len','temp']).drop_duplicates(subset=['Address_x', 'PIN'])
