from sql_metadata import Parser
from sql_metadata.keywords_lists import TokenType


def test_simple_table():
    source = """
        SELECT column_1
        FROM table_1
    """

    parser = Parser(source)
    assert ["table_1"] == parser.tables
    (table_token,) = [
        token for token in parser.tokens if token.token_type == TokenType.TABLE
    ]
    assert len(table_token.source_locations) == 1
    assert (
        source[table_token.source_locations[0][0] : table_token.source_locations[0][1]]
        == "table_1"
    )


def test_complex_identifier():
    source = """
        SELECT *
        FROM "DB".schema."table"
    """

    parser = Parser(source)
    assert ["DB.schema.table"] == parser.tables
    (table_token,) = [
        token for token in parser.tokens if token.token_type == TokenType.TABLE
    ]
    assert len(table_token.source_locations) == 1
    assert (
        source[table_token.source_locations[0][0] : table_token.source_locations[0][1]]
        == '"DB".schema."table"'
    )


def test_whitespace_between_identifiers():
    source = """
        SELECT *
        FROM demo_data
."demos" .
  flights
    """

    parser = Parser(source)
    assert ["demo_data.demos.flights"] == parser.tables
    (table_token,) = [
        token for token in parser.tokens if token.token_type == TokenType.TABLE
    ]
    assert len(table_token.source_locations) == 4
    assert [
        source[location[0] : location[1]] for location in table_token.source_locations
    ] == ["demo_data", '."demos"', ".", "flights"]


def test_comments_between_identifiers():
    source = """select from -- wrong
/* nope */my_db.
my_schema /* lol */
.my_table"""
    parser = Parser(source, filter_comments=True)
    assert ["my_db.my_schema.my_table"] == parser.tables
    (table_token,) = [
        token for token in parser.tokens if token.token_type == TokenType.TABLE
    ]
    assert len(table_token.source_locations) == 3
    assert [
        source[location[0] : location[1]] for location in table_token.source_locations
    ] == ["my_db.", "my_schema", ".my_table"]
