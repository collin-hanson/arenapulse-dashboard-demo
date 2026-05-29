from dataclasses import dataclass

from src.services.demo_data import get_governance_feeds


@dataclass(frozen=True)
class DataQualityStatus:
    feed_name: str
    status: str
    message: str


def get_demo_data_quality_statuses() -> list[DataQualityStatus]:
    feeds = get_governance_feeds()
    return [
        DataQualityStatus(str(row.feed_name), str(row.status), str(row.message))
        for row in feeds.itertuples(index=False)
    ]
