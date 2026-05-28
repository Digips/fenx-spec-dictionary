from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpecSource:
    source_id: str
    api_name: str
    api_mode: str
    api_version: str
    source_url: str

    @property
    def raw_filename(self) -> str:
        return f"{self.source_id}.swagger.json"


SPEC_SOURCES: list[SpecSource] = [
    SpecSource(
        source_id="policycommand_v1",
        api_name="policy",
        api_mode="command",
        api_version="1.0",
        source_url="https://api.fenergox.com/policycommand/swagger/1.0/swagger.json",
    ),
    SpecSource(
        source_id="policyquery_v2",
        api_name="policy",
        api_mode="query",
        api_version="2.0",
        source_url="https://api.fenergox.com/policyquery/swagger/2.0/swagger.json",
    ),
    SpecSource(
        source_id="productpolicycommand_v1",
        api_name="productpolicy",
        api_mode="command",
        api_version="1.0",
        source_url="https://api.fenergox.com/productpolicycommand/swagger/1.0/swagger.json",
    ),
    SpecSource(
        source_id="productpolicyquery_v1",
        api_name="productpolicy",
        api_mode="query",
        api_version="1.0",
        source_url="https://api.fenergox.com/productpolicyquery/swagger/1.0/swagger.json",
    ),
    SpecSource(
        source_id="lookupcommand_v1",
        api_name="lookup",
        api_mode="command",
        api_version="1.0",
        source_url="https://api.fenergox.com/lookupcommand/swagger/1.0/swagger.json",
    ),
    SpecSource(
        source_id="lookupquery_v1",
        api_name="lookup",
        api_mode="query",
        api_version="1.0",
        source_url="https://api.fenergox.com/lookupquery/swagger/1.0/swagger.json",
    ),
    SpecSource(
        source_id="journeycommand_v1",
        api_name="journey",
        api_mode="command",
        api_version="1.0",
        source_url="https://api.fenergox.com/journeycommand/swagger/1.0/swagger.json",
    ),
    SpecSource(
        source_id="journeyquery_v1",
        api_name="journey",
        api_mode="query",
        api_version="1.0",
        source_url="https://api.fenergox.com/journeyquery/swagger/1.0/swagger.json",
    ),
    SpecSource(
        source_id="riskcommand_v1",
        api_name="risk",
        api_mode="command",
        api_version="1.0",
        source_url="https://api.fenergox.com/riskcommand/swagger/1.0/swagger.json",
    ),
    SpecSource(
        source_id="riskquery_v1",
        api_name="risk",
        api_mode="query",
        api_version="1.0",
        source_url="https://api.fenergox.com/riskquery/swagger/1.0/swagger.json",
    ),
    SpecSource(
        source_id="documentmanagementcommand_v1",
        api_name="documentmanagement",
        api_mode="command",
        api_version="1.0",
        source_url="https://api.fenergox.com/documentmanagementcommand/swagger/1.0/swagger.json",
    ),
    SpecSource(
        source_id="documentmanagementcommand_v2",
        api_name="documentmanagement",
        api_mode="command",
        api_version="2.0",
        source_url="https://api.fenergox.com/documentmanagementcommand/swagger/2.0/swagger.json",
    ),
    SpecSource(
        source_id="documentmanagementquery_v1",
        api_name="documentmanagement",
        api_mode="query",
        api_version="1.0",
        source_url="https://api.fenergox.com/documentmanagementquery/swagger/1.0/swagger.json",
    ),
]


def get_spec_sources(source_ids: set[str] | None = None) -> list[SpecSource]:
    if not source_ids:
        return SPEC_SOURCES

    selected = [source for source in SPEC_SOURCES if source.source_id in source_ids]
    return selected
