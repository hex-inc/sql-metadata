from sql_metadata import Parser

def test_sup850():
    parser = Parser(
        """                
        select coalesce(test_col, "") from dataframe
        where test_col in ("a")
        """)
    assert ["dataframe"] == parser.tables