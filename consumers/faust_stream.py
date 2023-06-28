"""Defines trends calculations for stations"""
import logging

import faust


logger = logging.getLogger(__name__)


# Faust will ingest records from Kafka in this format
class Station(faust.Record):
    stop_id: int
    direction_id: str
    stop_name: str
    station_name: str
    station_descriptive_name: str
    station_id: int
    order: int
    red: bool
    blue: bool
    green: bool


# Faust will produce records to Kafka in this format
class TransformedStation(faust.Record):
    station_id: int
    station_name: str
    order: int
    line: str


# Define a Faust Stream that ingests data from the Kafka Connect stations topic and
# places it into a new topic with only the necessary information.
app = faust.App("stations-stream",
                broker="kafka://localhost:9092", store="memory://")
topic = app.topic("stations", value_type=Station)
out_topic = app.topic("faust_transformed_stations", partitions=1)
table = app.Table(
    "faust_transformed_stations",
    default=TransformedStation,
    partitions=1,
    changelog_topic=out_topic,
)

#  Using Faust, transform input `Station` records into `TransformedStation` records.
#  E.g.: if the `Station` record has the field `red` set to true,
#  then you would set the `line` of the `TransformedStation` record to the string `"red"`.


@app.agent(topic)
async def ProcessStationInfo(stations):

    async for station in stations:

        transformed_line = ""
        if station.red is True:
            transformed_line = "red"
        elif station.green is True:
            transformed_line = "green"
        elif station.blue is True:
            transformed_line = "blue"
        else:
            transformed_line = "null"

        transformed_station = TransformedStation(
            station_id=station.station_id,
            station_name=station.station_name,
            order=station.order,
            line=transformed_line
        )

        await out_topic.send(value=transformed_station)


if __name__ == "__main__":
    app.main()
