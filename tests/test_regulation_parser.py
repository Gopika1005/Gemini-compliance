import asyncio

from src.regulation_parser import RegulationParser


def test_parse_regulation_fallback():
    parser = RegulationParser()
    result = asyncio.run(parser.parse_regulation_from_text("", "GDPR"))

    assert isinstance(result, dict)
    assert result.get("regulation_name") == "GDPR"
    assert isinstance(result.get("key_requirements"), list)


def test_parse_regulations_loads_file_and_caches():
    parser = RegulationParser()
    regs = asyncio.run(parser.parse_regulations(["GDPR", "CCPA"]))

    assert "GDPR" in regs
    assert "CCPA" in regs
    # Ensure key fields exist
    assert isinstance(regs["GDPR"].get("key_requirements"), list)

    # Subsequent call should use cache (no errors)
    regs2 = asyncio.run(parser.parse_regulations(["GDPR"]))
    assert "GDPR" in regs2
