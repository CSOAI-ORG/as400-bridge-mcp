#!/usr/bin/env python3
"""
IBM AS/400 (IBM i / RPG / DB2) Bridge MCP — CSOAI Layer-0 legacy-bridge family.
Parse RPG, map to modern, and govern. Sibling of cobol-bridge-mcp.
Tools: parse_rpg · identify_files · map_to_modern · govern_ibmi
"""
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import re

mcp = FastMCP("AS/400 Bridge", instructions="Bridge IBM i / RPG / DB2 legacy to ONE OS — parse, map, govern.")


class RPGParsed(BaseModel):
    dialect: str
    files: List[str] = Field(default_factory=list)
    data_structures: List[str] = Field(default_factory=list)
    procedures: List[str] = Field(default_factory=list)
    line_count: int = 0


class Governance(BaseModel):
    risk_flags: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    attestable: bool = True
    note: str = ""


def _dialect(src: str) -> str:
    if re.search(r"\bdcl-(proc|pi|ds|s)\b", src, re.I) or "**free" in src.lower():
        return "RPG IV free-format (RPGLE)"
    if re.search(r"^\s*[FDC]\s", src, re.M):
        return "RPG III/IV fixed-format"
    return "RPG (dialect unknown)"


@mcp.tool()
def parse_rpg(source_code: str) -> RPGParsed:
    """Parse RPG source: dialect, file declarations (F-specs/dcl-f), data structures, procedures."""
    s = source_code
    files = re.findall(r"(?:^\s*F(\w+)|dcl-f\s+(\w+))", s, re.I | re.M)
    files = [a or b for a, b in files]
    ds = re.findall(r"(?:^\s*D\s*(\w+)\s+DS|dcl-ds\s+(\w+))", s, re.I | re.M)
    ds = [a or b for a, b in ds]
    procs = re.findall(r"dcl-proc\s+(\w+)", s, re.I)
    return RPGParsed(
        dialect=_dialect(s), files=[f for f in files if f][:30],
        data_structures=[d for d in ds if d][:30], procedures=procs[:30],
        line_count=len(s.splitlines()),
    )


@mcp.tool()
def identify_files(source_code: str) -> Dict[str, Any]:
    """List the DB2/physical/logical files the program touches (migration scope)."""
    p = parse_rpg(source_code)
    return {"files": p.files, "count": len(p.files),
            "note": "Each file → a DB2 table; map to modern ORM / API during migration."}


@mcp.tool()
def map_to_modern(source_code: str) -> Dict[str, Any]:
    """Map the RPG program shape to a modern service skeleton (files->repos, procs->endpoints)."""
    p = parse_rpg(source_code)
    return {"source": "IBM i / RPG", "target": "modern service",
            "repositories": p.files, "endpoints": p.procedures or ["main"],
            "data_models": p.data_structures}


@mcp.tool()
def govern_ibmi(source_code: str) -> Governance:
    """Governance: IBM i security + data-governance surface (attestable for CSOAI)."""
    flags = []
    if re.search(r"\bEXEC\s+SQL\b", source_code, re.I) and not re.search(r":\w+", source_code):
        flags.append("Embedded SQL without host variables — review for injection on migration")
    if not parse_rpg(source_code).procedures:
        flags.append("Monolithic calc-specs — no procedures; decompose during modernisation")
    return Governance(risk_flags=flags,
                      frameworks=["IBM i security (object authority)", "DB2 for i", "SOX", "GDPR", "DORA"],
                      note="CSOAI governs the bridge: parsed program + data lineage attestable on the ledger.")


def main():
    mcp.run()


if __name__ == "__main__":
    main()
