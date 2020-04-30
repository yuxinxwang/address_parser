from address_parser.address_parser import AddressParser
from address_parser.resource_manager import ResourceManager
import address_parser.address_methods_on_df as amod
import numpy as np
import pandas as pd
from parameterized import parameterized
import unittest

class TestAddressParser(unittest.TestCase):

    def test_init(self):
        a = AddressParser()
        assert (isinstance(a,AddressParser))

    def test_to_first_upper(self):
        a = "ROAD"
        assert (AddressParser().to_first_upper(a)=='Road')

    @parameterized.expand([
    ["Regular",
        "1000 Michigan Avenue",
        ("1000", "Michigan", "", 'Avenue', "") ],
    ["Multiple suffix",
        "1000 Michigan Avenue Road",
        ("1000", "Michigan Avenue", "","Road", "") ],
    ["Empty string 0",
        "",
        ("","","","","")],
    ["Empty string 1",
        " ",
        ("","","","","")],
    ["Extra numerical values and dots",
        "56 Test Dr. unit 571",
        ("56", "Test", "", "Dr", "unit 571")],
    ["With prefix",
        "32 East-Stone Trail.#9",
        ("32", "Stone", "E", "Trail", '9')],
    ["No street number",
        "Best of America 1000 Dr cat 506",
        ("", "Best of America", "", "Dr", "1000 cat 506") ]
    ])

    def test_split(self, name_of_test, input, output):
        ans = AddressParser().parse_street(input)
        self.assertEqual(ans, output)


    def test_amod(self, name_of_test, input, output):
        input = pd.read_csv()


if __name__ == '__main__':
    unittest.main()
