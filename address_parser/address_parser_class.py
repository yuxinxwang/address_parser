# -*- coding: utf-8 -*-

### Import libraries
from fuzzywuzzy import fuzz
import numpy as np
import os, sys, inspect
import pandas as pd
import pickle
import re

cmd_folder = os.path.realpath(os.path.abspath(os.path.split(\
                inspect.getfile( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
     sys.path.insert(0, cmd_folder)

import resource_manager

# !pip install -q fuzzywuzzy
# !pip install -q fuzzywuzzy[speedup]

class AddressParser:

    def __init__(self):
        self.street_name_abbr_dict = resource_manager.load_resource(\
                                            "street_name_abbr_dict.pickle")
        self.mile_road_dict = resource_manager.load_resource(\
                                            "mile_road_dict.pickle")


    def to_first_upper(self,x):
        """ Capitalize first letter in string, keep the remaining lowercase.
        Args:
        x (str): e.g. x = "Road", "ROAD", "road"

        Returns:
        y (str): e.g. "Road"
        """

        try:
            return x.title()
        except:
            return ""


    def strip(self, x):
        """ Strip string if not null
        Args:
            x (str): string to be striped.

        Returns:
            y (str): stripped string.
        """
        if x: return x.strip()
        return ""


    def parse_street(self, address):
        """ Split street address into components
        Args:
            address (str): address to be parsed.

        Returns:
            (steet_number, street_name, street_prefix, street_suffix, other)
        """

        # Handle null cases
        if not address:
            return ("", "", "", "", "")

        # Replace irrelevant information
        address = address.replace('.',' ').replace('#',' ').replace('-',' ')

        # Initiate return variables
        street_number, street_name, street_prefix, street_suffix, other = \
                      None, "", '', "", ""

        # Analyze each component in address
        all_componenets = address.strip().split()
        N = len(all_componenets)

        # Find last potential candidate for street_suffix
        last_suffix_pos = None
        for i,c in enumerate(all_componenets[::-1]):
            if self.to_first_upper(c) in self.street_name_abbr_dict:
              last_suffix_pos = N-1-i
              break

        # Parse all components
        for i,c in enumerate(all_componenets):
            # find numeric component
            if c.isnumeric():
            # check if it's [Number] Mile Road
                if i+1<N and all_componenets[i+1] == "Mile":
                    street_name += self.mile_road_dict[c.strip()]+' '
                # record street_number
                elif i==0:
                    street_number = c
                else:
                    other += c+' '
            # Find other components
            else:
                # Find prefix
                if c.upper() in ["E","W","S","N", "EAST", "WEST", "NORTH",
                                 "SOUTH"]:
                    # if this is street prefix
                    if street_prefix == "":
                        street_prefix = c[0].upper()
                    # already found street_prefix
                    else:
                        other += (c+' ')
                    continue

                # After suffix
                # deals with cases like "11 Michigan Ave Unit 12"
                if (last_suffix_pos is not None) and i > last_suffix_pos:
                    other += (c+' ')
                    continue

                # At suffix position --> check if it's suffix
                # deals with cases like "11 Street"
                if (i==last_suffix_pos):
                    # haven't found street name yet --> this is street name
                    if (street_name==""):
                        street_name += (c+' ')
                    # have a valid street name --> this is suffix
                    else:
                        street_suffix = self.to_first_upper(c)
                    continue
                # Otherwise, this is street name
                street_name += (c+' ')

        return tuple(map(self.strip,
                [street_number, street_name, street_prefix, street_suffix, other]))


    def close_match(self, street_name, street_suffix,
                         standard_address_set, standard_name_set,
                         name_to_suffix_dict):
        """ Find closest match with standard addresses
        Args:
            street_name (str): street name of address
            street_suffix (str): street suffix of address
            standard_address_set (set): all standard full addresses
            standard_name_set (set): all standard full name
            name_to_suffix_dict (dict): name to suffix dict

        Returns:
            (matched_name, matched_suffix, ratio)
        """

        street_name = self.strip(street_name).title()
        street_suffix = self.strip(street_suffix).title()

        # Initialize return values
        matched_name = ""
        matched_suffix = ""
        ratio = 0

        # Look for exact match
        if (street_name, street_suffix) in standard_address_set: 
            return (street_name,street_suffix,100)

        if tuple(street_name.split(' ')) in standard_address_set: 
            return (street_name.split(' ')[0],street_name.split(' ')[1],100)

        if (street_name+" "+street_suffix) in standard_name_set:
            matched_name = (street_name+" "+street_suffix)
            if len(name_to_suffix_dict[matched_name])==1:
                matched_suffix = list(name_to_suffix_dict[matched_name])[0]
            else:
                matched_suffix = ''
            return (matched_name, matched_suffix, 100)

        # Look for full street address match
        for standard_name, standard_suffix in standard_address_set:
            potential_ratio = fuzz.ratio( \
                (street_name+' '+street_suffix).lower(),
                (standard_name+' '+standard_suffix).lower() )
            if (potential_ratio > ratio):
                matched_name = standard_name
                matched_suffix = standard_suffix
                ratio = potential_ratio

        # Look for street address match
        # only when ratio is not good enough
        if (ratio < 90):
            for standard_name in standard_name_set:
                potential_ratio = fuzz.ratio( street_name.lower(),
                                              standard_name.lower() )
                if (potential_ratio > ratio):
                    matched_name = standard_name
                    if len(name_to_suffix_dict[matched_name])==1: 
                        matched_suffix = list(name_to_suffix_dict[matched_name])[0]
                    ratio = potential_ratio
        return (self.strip(matched_name), self.strip(matched_suffix), ratio)



    def fill_suffix(self, street_name, name_to_suffix_dict):
        """ Fill Suffix according to dictionary
        Args:
            street_name (str): street name
            name_to_suffix_dict (dict): dictionary from name to suffix
        Returns:
            suggested_suffix (str): Suggested suffix according to
                                    name_to_suffix_dict. Will return a non-empty
                                    value iff name_to_suffix_dict[street_name]
                                    contains only one value.
        """
        if street_name in name_to_suffix_dict:
            if ( len(name_to_suffix_dict[street_name]) == 1 ):
                return list(name_to_suffix_dict[street_name])[0]
        else:
            return ""
