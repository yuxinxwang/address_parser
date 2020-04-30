# -*- coding: utf-8 -*-

### Import libraries
from fuzzywuzzy import fuzz
import numpy as np
import os
import pandas as pd
import pickle
import re
import sys

from .resource_manager import ResourceManager
from .address_parser import AddressParser

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

    grouped = df[cols].groupby(cols[0])[cols[1:]].agg(lambda x: set(x))
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
