# Animal Shelter Database – Data Coursework

A Python project that builds an **animal shelter** MySQL database from CSV data, runs analytical queries, and generates interactive Plotly visualizations.

## Overview

This project:

- Connects to MySQL and creates the `animal_shelter` database (if it doesn’t exist).
- Defines and creates five tables: **HousingUnit**, **Animals**, **HealthCheck**, **Adopter**, and **Adoption**.
- Loads sample data from CSV files into those tables.
- Runs four SQL queries (including LEFT JOIN and GROUP BY) and saves the results as HTML charts.

## Prerequisites

- **Python 3** with:
  - `mysql-connector-python` – MySQL connection
  - `plotly` – interactive visualizations
- **MySQL Server** installed and running (e.g. localhost).

### Install dependencies

```bash
pip install mysql-connector-python plotly
```

## Configuration

Edit the database config at the top of `CW.py` if needed:

```python
config = {
    'user': 'root',        # Your MySQL username
    'password': '',        # Your MySQL password
    'host': 'localhost',
    'database': 'animal_shelter'
}
```

## Data Files

Place these CSV files in the **same folder as `CW.py`**:

| File               | Table       | Description                          |
|--------------------|------------|--------------------------------------|
| `housing_units.csv`| HousingUnit| Kennels, rooms, capacity, occupancy  |
| `animals.csv`      | Animals    | Animals (species, breed, status)    |
| `health_checks.csv`| HealthCheck| Vet checks and health ratings        |
| `adopters.csv`     | Adopter    | Adopter contact details              |
| `adoptions.csv`    | Adoption   | Adoption records and fees            |

## How to Run

1. Start MySQL.
2. Open a terminal in the folder that contains `CW.py` and the CSV files.
3. Run:

```bash
python CW.py
```

The script will:

- Create or connect to the `animal_shelter` database.
- Drop and recreate the tables, then load the CSV data.
- Run the four queries and print results to the console.
- Write four HTML visualization files in the same folder.

## Generated Visualizations

| File                           | Description                                      |
|--------------------------------|--------------------------------------------------|
| `query1_adoption_status.html`  | Bar chart of adoption status (e.g. Adopted, Available, Medical Hold) |
| `query2_animals_by_species.html` | Bar chart of animal counts by species         |
| `query3_housing_occupancy.html`  | Grouped bar chart: capacity vs current occupancy per housing unit |
| `query4_health_ratings.html`     | Bar chart of health check ratings (1–5) distribution |

Open any `.html` file in a browser to view the interactive chart.

## Queries Summary

1. **Query 1** – All animals with adoption info (LEFT JOIN on Adoption and Adopter).
2. **Query 2** – Animals per species with adopted count and average adoption fee (GROUP BY species).
3. **Query 3** – Housing units with capacity, occupancy, and animal count (GROUP BY housing unit).
4. **Query 4** – Health check ratings distribution (GROUP BY health_rating).

## Project Structure

```
Data CW (2)/
├── README.md           (this file)
└── Data CW/            (or project root)
    ├── CW.py           (main script)
    ├── housing_units.csv
    ├── animals.csv
    ├── health_checks.csv
    ├── adopters.csv
    ├── adoptions.csv
    └── query1_adoption_status.html   (generated)
        query2_animals_by_species.html
        query3_housing_occupancy.html
        query4_health_ratings.html
```

## Notes

- The script turns off foreign key checks, drops the five tables, then recreates them and reloads data. Any existing `animal_shelter` data will be replaced.
- CSV files must use UTF-8 encoding and match the column names expected by the script.
