from address_parser.address_parser import AddressParser
from address_parser.resource_manager import ResourceManager
import address_parser.address_methods_on_df as amod
import numpy as np
import pandas as pd
from parameterized import parameterized
import unittest


class TestResourceManager(unittest.TestCase):
    def test_load_sample(self):
        df = ResourceManager().load_sample()
        print("\n******** This is the top 5 rows of sample dataset: ********\
                \n\n",
                df.head(5))
        assert (isinstance(df,pd.DataFrame))

if __name__ == '__main__':
    unittest.main()
