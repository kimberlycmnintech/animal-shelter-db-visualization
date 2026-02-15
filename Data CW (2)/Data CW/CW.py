import mysql.connector
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import csv
from datetime import datetime

# Database connection configuration
config = {
    'user': 'root',  # Update with your MySQL username
    'password': '',  # Update with your MySQL password
    'host': 'localhost',
    'database': 'animal_shelter'  # Will be created if doesn't exist
}

# Establish connection
try:
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()
    print("Connected to MySQL server")
except mysql.connector.Error as err:
    # If database doesn't exist, connect without database first
    if err.errno == 1049:  # Unknown database
        config.pop('database')
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS animal_shelter")
        cursor.execute("USE animal_shelter")
        connection.commit()
        print("Created and connected to animal_shelter database")
    else:
        print(f"Error: {err}")
        exit(1)

# Drop existing tables if they exist (in reverse order of dependencies)
print("\nDropping existing tables...")
cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
tables = ['Adoption', 'HealthCheck', 'Animals', 'HousingUnit', 'Adopter']
for table in tables:
    cursor.execute(f"DROP TABLE IF EXISTS {table}")
cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
connection.commit()

# Create tables
print("\nCreating tables...")

# HousingUnit table
cursor.execute("""
    CREATE TABLE HousingUnit (
        residence_id INT PRIMARY KEY,
        residence_name VARCHAR(20) NOT NULL,
        capacity INT NOT NULL,
        current_occupancy INT NOT NULL,
        availability CHAR(1) NOT NULL,
        cleaning_status VARCHAR(14) NOT NULL
    )
""")

# Animals table
cursor.execute("""
    CREATE TABLE Animals (
        animal_id INT PRIMARY KEY,
        animal_name VARCHAR(20) NOT NULL,
        species VARCHAR(15) NOT NULL,
        breed VARCHAR(20) NOT NULL,
        gender VARCHAR(6) NOT NULL,
        age INT NOT NULL CHECK (age > 0),
        arrival_date DATE NOT NULL,
        status VARCHAR(20) NOT NULL,
        residence_id INT,
        FOREIGN KEY (residence_id) REFERENCES HousingUnit(residence_id)
    )
""")

# HealthCheck table
cursor.execute("""
    CREATE TABLE HealthCheck (
        check_id INT PRIMARY KEY,
        animal_id INT NOT NULL,
        check_date DATE NOT NULL,
        vet_name VARCHAR(30),
        diagnosis VARCHAR(30),
        treatment VARCHAR(40),
        health_rating INT CHECK (health_rating BETWEEN 1 AND 5),
        FOREIGN KEY (animal_id) REFERENCES Animals(animal_id)
    )
""")

# Adopter table
cursor.execute("""
    CREATE TABLE Adopter (
        adopter_id INT PRIMARY KEY,
        adopter_name VARCHAR(30) NOT NULL,
        phone VARCHAR(20) NOT NULL,
        email VARCHAR(30) NOT NULL,
        address VARCHAR(30) NOT NULL
    )
""")

# Adoption table
cursor.execute("""
    CREATE TABLE Adoption (
        adoption_id INT PRIMARY KEY,
        animal_id INT NOT NULL,
        adopter_id INT NOT NULL,
        adoption_date DATE NOT NULL,
        adoption_fee DECIMAL(5,2) NOT NULL,
        FOREIGN KEY (animal_id) REFERENCES Animals(animal_id),
        FOREIGN KEY (adopter_id) REFERENCES Adopter(adopter_id)
    )
""")

connection.commit()
print("Tables created successfully")

# Load data from CSV files
print("\nLoading data from CSV files...")

def load_csv_to_table(csv_file, table_name, cursor, connection):
    """Load data from CSV file to MySQL table"""
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            headers = next(csv_reader)  # Skip header row
            
            # Prepare column names and placeholders
            columns = ', '.join(headers)
            placeholders = ', '.join(['%s'] * len(headers))
            
            # Insert data
            row_count = 0
            for row in csv_reader:
                if row:  # Skip empty rows
                    # Convert empty strings to None for NULL values
                    values = [None if val == '' else val for val in row]
                    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                    cursor.execute(query, values)
                    row_count += 1
            
            connection.commit()
            print(f"  ✓ Loaded {row_count} rows into {table_name}")
            return True
    except Exception as e:
        print(f"  ✗ Error loading {csv_file}: {e}")
        return False

# Load all CSV files
load_csv_to_table('housing_units.csv', 'HousingUnit', cursor, connection)
load_csv_to_table('animals.csv', 'Animals', cursor, connection)
load_csv_to_table('health_checks.csv', 'HealthCheck', cursor, connection)
load_csv_to_table('adopters.csv', 'Adopter', cursor, connection)
load_csv_to_table('adoptions.csv', 'Adoption', cursor, connection)

print("\nData loading completed!")

# =============================================================================
# QUERIES AND VISUALIZATIONS
# =============================================================================

print("\n" + "="*70)
print("EXECUTING QUERIES AND GENERATING VISUALIZATIONS")
print("="*70)

# Query 1: Show all animals with their adoption information (LEFT JOIN)
# English: List all animals with their adoption details, showing animals that have been adopted and those that haven't
print("\nQuery 1: List all animals with their adoption information")
query1 = """
    SELECT 
        a.animal_id,
        a.animal_name,
        a.species,
        a.breed,
        a.status,
        ad.adoption_date,
        adopter.adopter_name,
        ad.adoption_fee
    FROM Animals a
    LEFT OUTER JOIN Adoption ad ON a.animal_id = ad.animal_id
    LEFT OUTER JOIN Adopter adopter ON ad.adopter_id = adopter.adopter_id
    ORDER BY a.animal_id
"""
cursor.execute(query1)
results1 = cursor.fetchall()
columns1 = [desc[0] for desc in cursor.description]
print(f"\nFound {len(results1)} records")

# Prepare data for visualization
status_counts = {}
for row in results1:
    status = row[4]  # status column
    status_counts[status] = status_counts.get(status, 0) + 1

# Visualization 1: Adoption status distribution
fig1 = go.Figure(data=[
    go.Bar(
        x=list(status_counts.keys()),
        y=list(status_counts.values()),
        marker_color=['#2ecc71', '#3498db', '#e74c3c'],
        text=list(status_counts.values()),
        textposition='outside'
    )
])
fig1.update_layout(
    title=dict(text='Adoption Status Distribution', font=dict(size=16, family='Arial Black')),
    xaxis_title='Status',
    yaxis_title='Number of Animals',
    template='plotly_white',
    showlegend=False,
    height=500
)
fig1.write_html('query1_adoption_status.html')
print("✓ Visualization saved: query1_adoption_status.html")

# Query 2: GROUP BY - Count animals by species and calculate average adoption fee
# English: For each species, count the number of animals and calculate the average adoption fee for adopted animals
print("\n\nQuery 2: Count animals by species with average adoption fees (GROUP BY)")
query2 = """
    SELECT 
        a.species,
        COUNT(a.animal_id) as total_animals,
        COUNT(ad.adoption_id) as adopted_count,
        COALESCE(AVG(ad.adoption_fee), 0) as avg_adoption_fee
    FROM Animals a
    LEFT JOIN Adoption ad ON a.animal_id = ad.animal_id
    GROUP BY a.species
    ORDER BY total_animals DESC
"""
cursor.execute(query2)
results2 = cursor.fetchall()
columns2 = [desc[0] for desc in cursor.description]

species_list = []
total_animals_list = []
adopted_count_list = []
avg_fee_list = []

for row in results2:
    species_list.append(row[0])
    total_animals_list.append(row[1])
    adopted_count_list.append(row[2])
    avg_fee_list.append(float(row[3]) if row[3] else 0)

print(f"\nResults:")
for i, species in enumerate(species_list):
    print(f"  {species}: {total_animals_list[i]} total animals, {adopted_count_list[i]} adopted, Avg fee: ${avg_fee_list[i]:.2f}")

# Visualization 2: Animals by species (bar chart)
fig2 = go.Figure(data=[
    go.Bar(
        x=species_list,
        y=total_animals_list,
        marker_color='steelblue',
        text=total_animals_list,
        textposition='outside'
    )
])
fig2.update_layout(
    title=dict(text='Number of Animals by Species', font=dict(size=16, family='Arial Black')),
    xaxis_title='Species',
    yaxis_title='Number of Animals',
    template='plotly_white',
    showlegend=False,
    height=500
)
fig2.write_html('query2_animals_by_species.html')
print("\n✓ Visualization saved: query2_animals_by_species.html")

# Query 3: Animals by housing unit with capacity information
# English: List all housing units with their current animals, showing capacity and occupancy
print("\n\nQuery 3: Animals by housing unit with capacity information")
query3 = """
    SELECT 
        h.residence_name,
        h.capacity,
        h.current_occupancy,
        h.availability,
        h.cleaning_status,
        COUNT(a.animal_id) as animals_count
    FROM HousingUnit h
    LEFT JOIN Animals a ON h.residence_id = a.residence_id
    GROUP BY h.residence_id, h.residence_name, h.capacity, h.current_occupancy, h.availability, h.cleaning_status
    ORDER BY h.residence_id
"""
cursor.execute(query3)
results3 = cursor.fetchall()
columns3 = [desc[0] for desc in cursor.description]

residence_names = []
capacity_list = []
occupancy_list = []

for row in results3:
    residence_names.append(row[0])
    capacity_list.append(row[1])
    occupancy_list.append(row[2])

print(f"\nResults:")
for i, name in enumerate(residence_names):
    print(f"  {name}: Capacity={capacity_list[i]}, Occupancy={occupancy_list[i]}")

# Visualization 3: Housing unit occupancy vs capacity
fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=residence_names,
    y=capacity_list,
    name='Capacity',
    marker_color='lightcoral'
))
fig3.add_trace(go.Bar(
    x=residence_names,
    y=occupancy_list,
    name='Current Occupancy',
    marker_color='lightgreen'
))
fig3.update_layout(
    title=dict(text='Housing Unit Capacity vs Occupancy', font=dict(size=16, family='Arial Black')),
    xaxis_title='Housing Unit',
    yaxis_title='Number of Animals',
    barmode='group',
    template='plotly_white',
    height=500,
    xaxis=dict(tickangle=-45)
)
fig3.write_html('query3_housing_occupancy.html')
print("\n✓ Visualization saved: query3_housing_occupancy.html")

# Query 4: Health check ratings distribution
# English: Show the distribution of health ratings for all health checks performed
print("\n\nQuery 4: Health check ratings distribution")
query4 = """
    SELECT 
        hc.health_rating,
        COUNT(*) as check_count,
        COUNT(DISTINCT hc.animal_id) as animals_checked
    FROM HealthCheck hc
    GROUP BY hc.health_rating
    ORDER BY hc.health_rating DESC
"""
cursor.execute(query4)
results4 = cursor.fetchall()
columns4 = [desc[0] for desc in cursor.description]

ratings = []
check_counts = []
animals_checked = []

for row in results4:
    ratings.append(str(row[0]))
    check_counts.append(row[1])
    animals_checked.append(row[2])

print(f"\nResults:")
for i, rating in enumerate(ratings):
    print(f"  Rating {rating}: {check_counts[i]} checks, {animals_checked[i]} animals")

# Visualization 4: Health rating distribution
colors = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#27ae60']
fig4 = go.Figure(data=[
    go.Bar(
        x=ratings,
        y=check_counts,
        marker_color=colors[:len(ratings)],
        text=check_counts,
        textposition='outside'
    )
])
fig4.update_layout(
    title=dict(text='Health Check Ratings Distribution', font=dict(size=16, family='Arial Black')),
    xaxis_title='Health Rating',
    yaxis_title='Number of Health Checks',
    template='plotly_white',
    showlegend=False,
    height=500
)
fig4.write_html('query4_health_ratings.html')
print("\n✓ Visualization saved: query4_health_ratings.html")

print("\n" + "="*70)
print("ALL QUERIES EXECUTED AND VISUALIZATIONS GENERATED SUCCESSFULLY!")
print("="*70)
print("\nGenerated visualization files:")
print("  - query1_adoption_status.html")
print("  - query2_animals_by_species.html")
print("  - query3_housing_occupancy.html")
print("  - query4_health_ratings.html")

# Close connection
cursor.close()
connection.close()
print("\nDatabase connection closed.")

