# **Grapes of Weather**

A Business Intelligence dashboard that measures how the climate of the main French wine regions has changed since 1950, and what it means for each vintage.

## Table of contents

1. [Overview](#overview)
2. [Business context](#business-context)
3. [Data source](#data-source)
4. [Scope](#scope)
5. [Architecture](#architecture)
6. [Design choices](#design-choices)
7. [Indicators](#indicators)
8. [Getting started](#getting-started)
9. [Project status](#project-status)
10. [Author](#author)

## Overview

Grapes of Weather turns daily weather records from Météo-France into a small set of agro-climatic indicators per wine region and per vintage. A Streamlit application then presents these indicators as an interactive dashboard.

The main question is simple: is each French wine region still growing grapes in the climate it was known for, and how fast is it changing?

## Business context

Wine quality and style depend directly on the weather of the growing season. Warmer seasons bring earlier harvests, higher sugar levels and lower acidity. Spring frost and heat waves can destroy a large part of a harvest in a few days.

For producers, buyers and investors, these trends raise concrete questions:

- Which regions are warming the fastest?
- Are spring frosts becoming more or less frequent?
- How many heat wave days does a typical season now include?
- Is a given vintage exceptional, or part of a long-term trend?

The dashboard is built to answer these questions with transparent and reproducible indicators.

## Data source

- Provider: Météo-France, published on data.gouv.fr
- Dataset: [Données climatologiques de base quotidiennes](https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-quotidiennes)
- Files used: `RR-T-Vent` (precipitation, temperature and wind), one file per department and per period
- Periods: 1950 to 2024 (historical) and 2025 to 2026 (latest)
- License: Licence Ouverte 2.0 (Etalab)

Each row is one day at one weather station. Every measure comes with a quality code, which the pipeline uses to discard doubtful values.

## Scope

The first version covers six wine regions, each mapped to its main departments:

| Region | Departments |
| --- | --- |
| Bordeaux | 33 |
| Champagne | 51, 10 |
| Alsace | 67, 68 |
| Bourgogne | 21, 71 |
| Vallée du Rhône | 26, 84 |
| Languedoc | 34, 11 |

The analysis window runs from the 1950 vintage to the 2026 vintage. The growing season is defined as April to October, from bud break to the end of harvest.

Production volumes and wine prices are out of scope for this version and may be added later.

## Architecture

The project follows a two-stage design: an offline ETL pipeline that prepares compact CSV files, and a Streamlit application that only reads these files.

```
Grapes_of_Weather/
    data/
        raw/            downloaded Météo-France files (not versioned)
        processed/      station_year.csv and region_year.csv
    src/
        config.py       paths, regions, data source and analysis window
        etl.py          extraction, loading, cleaning, indicators, aggregation
    requirements.txt
    README.md
```

The ETL pipeline runs in five steps:

1. Extraction: download the raw files of each department into `data/raw/`, with a local cache.
2. Loading: read and concatenate the files of one department, keeping only the useful columns.
3. Cleaning: mask values with an invalid quality code and keep the growing season only.
4. Indicators: compute one row of indicators per station and per year.
5. Aggregation: average the stations of each region per vintage, then write the results to `data/processed/`.

## Design choices

- **Separate ETL and dashboard.** The raw data represents several million rows. Processing it once offline keeps the Streamlit application fast and simple.
- **Central configuration.** Regions, departments, paths and the analysis window live in `src/config.py`. Adding a region only requires editing this file.
- **Local download cache.** A file already present in `data/raw/` is not downloaded again, unless explicitly forced. The pipeline can be run several times at no cost.
- **Column selection at read time.** Only the needed columns are loaded from files that contain about sixty, which keeps memory usage low.
- **Quality codes respected.** Values flagged as doubtful are set to missing rather than removed, so that a doubtful rainfall value does not erase a valid temperature on the same day.
- **Minimum coverage per season.** A station and year pair is kept only if at least 90 percent of the season days have valid temperatures. This prevents incomplete records from biasing regional averages.
- **Equal weight per station.** Regional values are the mean of station values, and the number of stations is kept alongside each result.

## Indicators

All indicators are computed over the growing season, from April 1 to October 31.

| Indicator | Definition |
| --- | --- |
| `gdd` | Growing degree days (Winkler index), base 10 degrees Celsius |
| `frost_days` | Days in April and May with a minimum temperature below 0 degrees Celsius |
| `heat_days` | Days with a maximum temperature above 35 degrees Celsius |
| `tmean` | Mean daily temperature over the season |
| `rain_mm` | Total precipitation over the season, in millimetres |

## Getting started

Requirements: Python 3.11 or later.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run the ETL pipeline to download the data and build the processed files:

```bash
python -m src.etl
```

The Streamlit application will be documented here once it is available.

## Project status

- [x] Project configuration
- [x] Extraction with local cache
- [x] Loading and column selection
- [x] Cleaning and season filter
- [ ] Indicators (in progress)
- [ ] Regional aggregation and export (written, to be validated)
- [ ] Streamlit dashboard
- [ ] Demo video

## Author

Seyni Balde, EFREI, course BDML1 Data Visualization and Business Intelligence, supervised by Mano Mathew.
