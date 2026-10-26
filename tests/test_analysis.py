import sys
import unittest
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from analyze import funnel,summarize

class TestFunnel(unittest.TestCase):
    def test_chronological_and_distinct_visitors(self):
        events=pd.DataFrame([
            (100,1,'view'),(120,1,'view'),(140,1,'addtocart'),(160,1,'transaction'),
            (100,2,'transaction'),(130,2,'view'),(150,2,'addtocart'),
            (100,3,'view'),(140,3,'transaction')],columns=['timestamp','visitorid','event'])
        m=summarize(funnel(events))
        self.assertEqual((m['viewers'],m['added_to_cart'],m['purchasers']),(3,2,1))
    def test_unknown_action_excluded(self):
        events=pd.DataFrame([(100,1,'view'),(200,1,'unknown'),(300,1,'transaction')],columns=['timestamp','visitorid','event'])
        self.assertEqual(summarize(funnel(events))['purchasers'],0)
    def test_missing_columns_rejected(self):
        with self.assertRaises(ValueError):funnel(pd.DataFrame({'foo':[1]}))

if __name__=='__main__':unittest.main()
