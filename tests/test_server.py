import sys,os
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

SRC="**free\ndcl-f CUSTFILE;\ndcl-ds order;\ndcl-proc calcTax;"
def test_parse():
    p=server.parse_rpg(SRC); assert "RPG" in p.dialect; assert "calcTax" in p.procedures
def test_govern():
    assert any("SOX" in f for f in server.govern_ibmi(SRC).frameworks)
