from address_parser.address_parser import AddressParser
from address_parser.resource_manager import ResourceManager
import address_parser.address_methods_on_df as amod
import numpy as np
import pandas as pd
from parameterized import parameterized
import unittest


class TestAmod(unittest.TestCase):

    def test_load_sample(self, print_ans=False):
        df = amod.load_sample()
        if print_ans:
            print("\n******** This is the top 5 rows of sample dataset:\
            ********\n\n", df.head(5))
        assert (isinstance(df,pd.DataFrame))

    def test_parse_address(self):
        df = amod.load_sample()
        a,b,c,d,e = amod.parse_street_series(df['Address_x'])
        self.assertEqual(list(b),
                df['Street Name'].astype(str).tolist())

    def test_combination_as_df(self):
        df = pd.DataFrame(data={'0': [1,1,2], '1': [3,3,5]})
        ans = amod.get_combinations_as_df(df, ['0', '1'])
        assert( (ans.to_numpy() == \
                        np.array([[1,3,2],[2,5,1]])).all() )


    def test_combination_as_dict(self):
        df = pd.DataFrame(data={'0': [1,1,2], '1': [3,4,5]})
        ans = amod.get_combinations_as_df(df, ['0', '1'])
        assert( (ans.to_numpy() == \
                np.array([[1,3,1],[1,4,1],[2,5,1]])).all() )



if __name__ == '__main__':
    unittest.main()
