# AirportFactsAlexaSkill

Simple skill for answer factual questions about airports.

## Airport Data

Converting from airport ICAO code to friendly name is done using data from [openflights.org](https://openflights.org/data.html). Specifically, the [Airports.dat](https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat) dataset.

## Architecture

1) Alexa Skill Definition
2) AWS Lambda Function
3) S3 Bucket containing external data

A copy of the Airports.dat file is stored in the S3 bucket. The Skill's Lambda function, upon activiation, downloads this file to the Lambda host server if it isn't found locally, and loads an in-memory dictionary with the data. Using the intent's data (an ICAO code such as KBOS, KLAX, etc), a response is provided.