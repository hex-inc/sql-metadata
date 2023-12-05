import pytest

from sqlparse import joins
from sql_metadata import Parser


def test_pivot_operator():
    source = """
SELECT *
  FROM monthly_sales
    PIVOT(SUM(amount) FOR MONTH IN ('JAN', 'FEB', 'MAR', 'APR'))
      AS p
  ORDER BY EMPID
    """
    parser = Parser(source)
    assert ["monthly_sales"] == parser.tables


def test_table_named_pivot():
    parser = Parser("from pivot")
    assert parser.tables == ["pivot"]
    assert parser.query_type == "SELECT"
    parser = Parser("select * from pivot join other using (id)")
    assert "pivot" in parser.tables and "other" in parser.tables
    assert parser.query_type == "SELECT"


def test_from_first():
    parser = Parser("from dataframe")
    assert parser.tables == ["dataframe"]
    assert parser.query_type == "SELECT"
    parser = Parser("from dataframe select *")
    assert parser.tables == ["dataframe"]
    assert parser.query_type == "SELECT"

    parser = Parser(
        "from dataframe_1 select * where id in (from dataframe_2 select id)"
    )
    assert set(parser.tables) == {"dataframe_1", "dataframe_2"}
    assert parser.query_type == "SELECT"


def test_pivot():
    parser = Parser(
        """
PIVOT
    vendor_offers_current
ON 'curr_' || curr
USING sum(offer_count)
GROUP BY vendor_id
"""
    )
    assert parser.tables == ["vendor_offers_current"]
    assert parser.query_type == "SELECT"

    parser = Parser(
        """
WITH pivot_alias AS (
    PIVOT Cities on Year USING SUM(Population) GROUP BY Country
)
SELECT * FROM pivot_alias;
"""
    )
    assert parser.tables == ["Cities"]
    assert parser.query_type == "SELECT"

    parser = Parser(
        """
SELECT
    *
FROM (
    PIVOT Cities on Year USING SUM(Population) GROUP BY Country
) pivot_alias;
"""
    )
    assert "Cities" in parser.tables
    assert "pivot_alias" not in parser.tables
    assert parser.query_type == "SELECT"


def test_unpivot():
    parser = Parser(
        """
UNPIVOT monthly_sales
    ON (jan, feb, mar) AS q1, (apr, may, jun) AS q2
    INTO
        NAME quarter
        VALUE month_1_sales, month_2_sales, month_3_sales;
"""
    )
    assert "monthly_sales" in parser.tables
    assert parser.query_type == "SELECT"

    parser = Parser(
        """
WITH unpivot_alias AS (
    UNPIVOT monthly_sales
    ON COLUMNS(* EXCLUDE (empid, dept))
    INTO
        NAME month
        VALUE sales
)
SELECT * FROM unpivot_alias;
"""
    )
    assert "monthly_sales" in parser.tables
    assert "unpivot_alias" not in parser.tables
    assert parser.query_type == "SELECT"

    parser = Parser(
        """
SELECT
    *
FROM (
    UNPIVOT monthly_sales
    ON COLUMNS(* EXCLUDE (empid, dept))
    INTO
        NAME month
        VALUE sales
) unpivot_alias;
"""
    )
    assert "monthly_sales" in parser.tables
    assert "unpivot_alias" not in parser.tables
    assert parser.query_type == "SELECT"


def test_natural_join():
    parser = Parser(
        """
select * from
    dataframe_1
natural join dataframe_2
"""
    )
    assert "dataframe_1" in parser.tables
    assert "dataframe_2" in parser.tables
    assert parser.query_type == "SELECT"


ALL_JOIN_TYPES = [" ".join(type).lower() for type in joins.enumerate_types()]


@pytest.mark.parametrize("join_type", ALL_JOIN_TYPES)
def test_all_join_types(join_type):
    parser = Parser(f"select * from dataframe_1 {join_type} dataframe_2")
    assert "dataframe_1" in parser.tables
    assert "dataframe_2" in parser.tables
    assert parser.query_type == "SELECT"


def test_mega_join():
    dataframes = [f"dataframe_{i}" for i in range(len(ALL_JOIN_TYPES) + 1)]
    query = "select * from dataframe_0\n"
    for join_type, dataframe in zip(ALL_JOIN_TYPES, dataframes[1:]):
        query += f"{join_type} {dataframe}\n"
    parser = Parser(query)
    for dataframe in dataframes:
        assert dataframe in parser.tables
    assert parser.query_type == "SELECT"
