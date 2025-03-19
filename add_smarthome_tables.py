import sqlite3
import os
import datetime
import random

# Database file path
DB_PATH = r"C:\Users\Luiss\OneDrive - tgm - Die Schule der Technik\TGM\4BHWII\Hackathon\hzl-2025\hauszumleben.db"

def create_connection(db_path):
    """Create a database connection to the SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        print(f"Connected to database: {db_path}")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def get_existing_tables(conn):
    """Get list of existing tables in the database"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    print(f"Existing tables: {', '.join(tables)}")
    return tables

def create_smart_home_tables(conn):
    """Create smart home related tables if they don't exist"""
    cursor = conn.cursor()
    
    # Create smart_devices table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS smart_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        room TEXT,
        status INTEGER DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create rooms table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        floor INTEGER,
        size_sqm REAL
    )
    ''')
    
    # Create device_history table for tracking status changes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS device_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        status INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES smart_devices (id)
    )
    ''')
    
    conn.commit()
    print("Smart home tables created successfully")

def create_assisted_living_tables(conn):
    """Create tables for assisted living management"""
    cursor = conn.cursor()
    
    # Resident profile table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS residents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        room_number TEXT,
        date_of_birth DATE,
        age INTEGER,
        mobility_status TEXT,
        has_fall_history INTEGER DEFAULT 0,
        last_fall_date DATE,
        emergency_contact TEXT,
        emergency_phone TEXT
    )
    ''')
    
    # Health monitoring tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS health_vitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER,
        heart_rate INTEGER,
        blood_pressure_systolic INTEGER,
        blood_pressure_diastolic INTEGER,
        measurement_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (resident_id) REFERENCES residents (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctor_visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER,
        visit_date DATE,
        doctor_name TEXT,
        reason TEXT,
        notes TEXT,
        follow_up_date DATE,
        FOREIGN KEY (resident_id) REFERENCES residents (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS allergies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER,
        allergy_type TEXT,
        allergy_name TEXT,
        severity TEXT,
        notes TEXT,
        FOREIGN KEY (resident_id) REFERENCES residents (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sleep_quality (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER,
        date DATE,
        hours_slept REAL,
        quality_rating INTEGER CHECK(quality_rating BETWEEN 1 AND 5),
        notes TEXT,
        FOREIGN KEY (resident_id) REFERENCES residents (id)
    )
    ''')
    
    # Activities and schedules
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        location TEXT,
        scheduled_time TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS activity_participation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER,
        activity_id INTEGER,
        date DATE,
        attended INTEGER DEFAULT 0,
        notes TEXT,
        FOREIGN KEY (resident_id) REFERENCES residents (id),
        FOREIGN KEY (activity_id) REFERENCES activities (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS outings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER,
        departure_time TIMESTAMP,
        expected_return_time TIMESTAMP,
        actual_return_time TIMESTAMP,
        destination TEXT,
        accompanied_by TEXT,
        notes TEXT,
        FOREIGN KEY (resident_id) REFERENCES residents (id)
    )
    ''')
    
    # Dietary information
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dietary_requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER,
        requirement_type TEXT,
        description TEXT,
        is_allergy INTEGER DEFAULT 0,
        notes TEXT,
        FOREIGN KEY (resident_id) REFERENCES residents (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        meal_type TEXT,
        calories INTEGER,
        is_vegetarian INTEGER DEFAULT 0,
        is_vegan INTEGER DEFAULT 0,
        is_glutenfree INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS menu_selections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER,
        menu_item_id INTEGER,
        date DATE,
        meal_time TEXT,
        consumed_percent INTEGER DEFAULT 100,
        feedback TEXT,
        FOREIGN KEY (resident_id) REFERENCES residents (id),
        FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leftover_food (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        menu_selection_id INTEGER,
        amount_percent INTEGER,
        reason TEXT,
        FOREIGN KEY (menu_selection_id) REFERENCES menu_selections (id)
    )
    ''')
    
    # Financial tracking
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trust_account_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER,
        transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        amount REAL NOT NULL,
        transaction_type TEXT,
        description TEXT,
        balance_after REAL,
        processed_by TEXT,
        FOREIGN KEY (resident_id) REFERENCES residents (id)
    )
    ''')
    
    conn.commit()
    print("Assisted living tables created successfully")

def insert_sample_data(conn):
    """Insert sample data into the smart home tables"""
    cursor = conn.cursor()
    
    # Check if data already exists to avoid duplicates
    cursor.execute("SELECT COUNT(*) FROM rooms")
    room_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM smart_devices")
    device_count = cursor.fetchone()[0]
    
    # Insert room data if no rooms exist
    if room_count == 0:
        rooms = [
            ('Living Room', 1, 25.5),
            ('Kitchen', 1, 15.0),
            ('Master Bedroom', 2, 22.0),
            ('Bathroom', 2, 8.0),
            ('Guest Room', 2, 16.0),
            ('Basement', 0, 30.0)
        ]
        cursor.executemany('''
        INSERT INTO rooms (name, floor, size_sqm)
        VALUES (?, ?, ?)
        ''', rooms)
        print(f"Added {len(rooms)} rooms")
    
    # Insert device data if no devices exist
    if device_count == 0:
        devices = [
            ('Living Room Main Light', 'light', 'Living Room', 0, datetime.datetime.now()),
            ('Kitchen Light', 'light', 'Kitchen', 0, datetime.datetime.now()),
            ('Kitchen Smart Fridge', 'appliance', 'Kitchen', 1, datetime.datetime.now()),
            ('Master Bedroom Light', 'light', 'Master Bedroom', 0, datetime.datetime.now()),
            ('Bathroom Heater', 'heater', 'Bathroom', 0, datetime.datetime.now()),
            ('Smart TV', 'entertainment', 'Living Room', 0, datetime.datetime.now()),
            ('Air Conditioner', 'climate', 'Living Room', 0, datetime.datetime.now()),
            ('Basement Light', 'light', 'Basement', 0, datetime.datetime.now())
        ]
        cursor.executemany('''
        INSERT INTO smart_devices (name, type, room, status, last_updated)
        VALUES (?, ?, ?, ?, ?)
        ''', devices)
        print(f"Added {len(devices)} devices")
        
        # Add some history data
        for i in range(1, len(devices) + 1):
            # Create some random history entries for each device
            history_entries = [
                (i, 1, datetime.datetime.now() - datetime.timedelta(hours=6)),
                (i, 0, datetime.datetime.now() - datetime.timedelta(hours=4)),
                (i, 1, datetime.datetime.now() - datetime.timedelta(hours=2))
            ]
            cursor.executemany('''
            INSERT INTO device_history (device_id, status, timestamp)
            VALUES (?, ?, ?)
            ''', history_entries)
    
    conn.commit()
    print("Sample data added successfully")

def insert_assisted_living_sample_data(conn):
    """Insert sample data into the assisted living tables"""
    cursor = conn.cursor()
    
    # Check if residents data already exists to avoid duplicates
    cursor.execute("SELECT COUNT(*) FROM residents")
    resident_count = cursor.fetchone()[0]
    
    if resident_count == 0:
        # Insert sample residents
        residents = [
            ('Maria', 'Schmidt', '101', '1940-05-15', 83, 'Walker-assisted', 1, '2023-09-10', 'Hans Schmidt', '+43 664 1234567'),
            ('Johann', 'Müller', '102', '1935-11-22', 88, 'Fully mobile', 0, None, 'Anna Müller', '+43 676 2345678'),
            ('Helga', 'Bauer', '103', '1942-03-30', 81, 'Wheelchair', 1, '2023-12-05', 'Thomas Bauer', '+43 699 3456789'),
            ('Franz', 'Huber', '104', '1938-07-12', 85, 'Cane', 0, None, 'Elisabeth Huber', '+43 650 4567890'),
            ('Elisabeth', 'Wagner', '105', '1945-01-25', 78, 'Fully mobile', 0, None, 'Michael Wagner', '+43 660 5678901')
        ]
        
        cursor.executemany('''
        INSERT INTO residents (first_name, last_name, room_number, date_of_birth, age, 
                             mobility_status, has_fall_history, last_fall_date, 
                             emergency_contact, emergency_phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', residents)
        print(f"Added {len(residents)} residents")
        
        # Insert health vitals data
        vitals = []
        for resident_id in range(1, len(residents) + 1):
            # Generate several days of vitals for each resident
            for day_offset in range(5):
                measurement_time = datetime.datetime.now() - datetime.timedelta(days=day_offset)
                heart_rate = random.randint(60, 90)
                bp_systolic = random.randint(110, 150)
                bp_diastolic = random.randint(60, 90)
                vitals.append((resident_id, heart_rate, bp_systolic, bp_diastolic, measurement_time, "Regular checkup"))
        
        cursor.executemany('''
        INSERT INTO health_vitals (resident_id, heart_rate, blood_pressure_systolic,
                                blood_pressure_diastolic, measurement_time, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', vitals)
        print(f"Added {len(vitals)} health vital readings")
        
        # Insert doctor visits
        doctor_visits = [
            (1, '2023-12-15', 'Dr. Stefan Mayer', 'Annual checkup', 'All vitals normal', '2024-12-15'),
            (1, '2023-09-10', 'Dr. Stefan Mayer', 'Fall follow-up', 'Minor bruising, no fractures', '2023-09-24'),
            (2, '2024-01-10', 'Dr. Julia Weber', 'Respiratory infection', 'Prescribed antibiotics', '2024-01-24'),
            (3, '2023-11-05', 'Dr. Thomas Klein', 'Diabetes follow-up', 'Adjusted medication', '2024-02-05'),
            (4, '2023-12-20', 'Dr. Maria Schwarz', 'Blood pressure check', 'BP slightly elevated', '2024-03-20'),
            (5, '2024-01-15', 'Dr. Julia Weber', 'Annual checkup', 'All vitals normal', '2025-01-15')
        ]
        
        cursor.executemany('''
        INSERT INTO doctor_visits (resident_id, visit_date, doctor_name, reason, notes, follow_up_date)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', doctor_visits)
        print(f"Added {len(doctor_visits)} doctor visits")
        
        # Insert allergies
        allergies = [
            (1, 'Food', 'Lactose', 'Moderate', 'Avoid milk products'),
            (1, 'Medication', 'Penicillin', 'Severe', 'Rash and difficulty breathing'),
            (3, 'Food', 'Nuts', 'Severe', 'Anaphylaxis risk'),
            (4, 'Environmental', 'Pollen', 'Mild', 'Seasonal allergies in spring'),
            (5, 'Food', 'Shellfish', 'Moderate', 'Avoid all seafood')
        ]
        
        cursor.executemany('''
        INSERT INTO allergies (resident_id, allergy_type, allergy_name, severity, notes)
        VALUES (?, ?, ?, ?, ?)
        ''', allergies)
        print(f"Added {len(allergies)} allergies")
        
        # Insert sleep quality data
        sleep_data = []
        for resident_id in range(1, len(residents) + 1):
            for day_offset in range(7):
                date = datetime.date.today() - datetime.timedelta(days=day_offset)
                hours = round(random.uniform(5.0, 9.0), 1)
                quality = random.randint(2, 5)
                notes = "Normal night" if quality >= 4 else "Restless sleep"
                sleep_data.append((resident_id, date, hours, quality, notes))
                
        cursor.executemany('''
        INSERT INTO sleep_quality (resident_id, date, hours_slept, quality_rating, notes)
        VALUES (?, ?, ?, ?, ?)
        ''', sleep_data)
        print(f"Added {len(sleep_data)} sleep records")
        
        # Insert activities
        activities = [
            ('Morning Exercise', 'Gentle stretching and movement', 'Community Room', 
             datetime.datetime.now().replace(hour=9, minute=30, second=0, microsecond=0)),
            ('Bingo', 'Social game with prizes', 'Recreation Room', 
             datetime.datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)),
            ('Music Therapy', 'Singing and instrument playing', 'Community Room', 
             datetime.datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)),
            ('Art Class', 'Painting and crafts', 'Art Room', 
             datetime.datetime.now().replace(hour=10, minute=30, second=0, microsecond=0)),
            ('Garden Club', 'Plant care and gardening', 'Garden', 
             datetime.datetime.now().replace(hour=15, minute=30, second=0, microsecond=0))
        ]
        
        cursor.executemany('''
        INSERT INTO activities (name, description, location, scheduled_time)
        VALUES (?, ?, ?, ?)
        ''', activities)
        print(f"Added {len(activities)} activities")
        
        # Insert activity participation
        participations = []
        for resident_id in range(1, len(residents) + 1):
            for activity_id in range(1, len(activities) + 1):
                date = datetime.date.today() - datetime.timedelta(days=random.randint(0, 14))
                attended = random.choice([0, 1, 1, 1])  # 75% chance of attending
                notes = "Enjoyed the activity" if attended else "Did not feel well"
                participations.append((resident_id, activity_id, date, attended, notes))
                
        cursor.executemany('''
        INSERT INTO activity_participation (resident_id, activity_id, date, attended, notes)
        VALUES (?, ?, ?, ?, ?)
        ''', participations)
        print(f"Added {len(participations)} activity participations")
        
        # Insert outings data
        outings = [
            (1, datetime.datetime.now() - datetime.timedelta(days=5, hours=10), 
             datetime.datetime.now() - datetime.timedelta(days=5, hours=6),
             datetime.datetime.now() - datetime.timedelta(days=5, hours=6),
             'Family visit', 'Son Hans', 'Lunch with family'),
            (2, datetime.datetime.now() - datetime.timedelta(days=3, hours=14), 
             datetime.datetime.now() - datetime.timedelta(days=3, hours=11),
             datetime.datetime.now() - datetime.timedelta(days=3, hours=11.5),
             'Doctor appointment', 'Caregiver Lisa', 'Regular check-up'),
            (3, datetime.datetime.now() - datetime.timedelta(days=2, hours=9), 
             datetime.datetime.now() - datetime.timedelta(days=2, hours=5),
             datetime.datetime.now() - datetime.timedelta(days=2, hours=4.5),
             'Shopping', 'Daughter Maria', 'Grocery shopping'),
            (5, datetime.datetime.now() - datetime.timedelta(days=1, hours=13), 
             datetime.datetime.now() - datetime.timedelta(days=1, hours=10),
             datetime.datetime.now() - datetime.timedelta(days=1, hours=10),
             'Park walk', 'Caregiver Thomas', 'Afternoon walk')
        ]
        
        cursor.executemany('''
        INSERT INTO outings (resident_id, departure_time, expected_return_time, 
                           actual_return_time, destination, accompanied_by, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', outings)
        print(f"Added {len(outings)} outings")
        
        # Insert dietary requirements
        dietary_requirements = [
            (1, 'Restriction', 'Lactose-free', 1, 'Lactose intolerance'),
            (1, 'Preference', 'Soft food', 0, 'Dental issues'),
            (2, 'Restriction', 'Low sugar', 0, 'Diabetes management'),
            (3, 'Restriction', 'Nut-free', 1, 'Severe allergy'),
            (4, 'Restriction', 'Low sodium', 0, 'Blood pressure management'),
            (5, 'Restriction', 'Shellfish-free', 1, 'Seafood allergy'),
            (5, 'Preference', 'Vegetarian', 0, 'Personal choice')
        ]
        
        cursor.executemany('''
        INSERT INTO dietary_requirements (resident_id, requirement_type, description, is_allergy, notes)
        VALUES (?, ?, ?, ?, ?)
        ''', dietary_requirements)
        print(f"Added {len(dietary_requirements)} dietary requirements")
        
        # Insert menu items
        menu_items = [
            ('Wiener Schnitzel', 'Traditional veal schnitzel with potato salad', 'Lunch', 650, 0, 0, 0),
            ('Vegetable Soup', 'Clear vegetable soup with herbs', 'Starter', 120, 1, 1, 1),
            ('Grilled Fish', 'Fresh trout with lemon and herbs', 'Lunch', 450, 0, 0, 1),
            ('Fruit Salad', 'Mixed seasonal fruits', 'Dessert', 180, 1, 1, 1),
            ('Roast Chicken', 'Roasted chicken with vegetables', 'Dinner', 550, 0, 0, 1),
            ('Apple Strudel', 'Traditional apple strudel with vanilla sauce', 'Dessert', 320, 1, 0, 0),
            ('Vegetarian Goulash', 'Vegetable goulash with rice', 'Lunch', 380, 1, 1, 1),
            ('Omelette', 'Cheese and herb omelette', 'Breakfast', 320, 1, 0, 1)
        ]
        
        cursor.executemany('''
        INSERT INTO menu_items (name, description, meal_type, calories, 
                              is_vegetarian, is_vegan, is_glutenfree)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', menu_items)
        print(f"Added {len(menu_items)} menu items")
        
        # Insert menu selections
        menu_selections = []
        for resident_id in range(1, len(residents) + 1):
            for day in range(3):
                date = datetime.date.today() - datetime.timedelta(days=day)
                # Breakfast
                menu_item_id = random.choice([2, 8])
                consumed = random.randint(70, 100)
                feedback = "Good" if consumed >= 90 else "Adequate" if consumed >= 70 else "Poor"
                menu_selections.append((resident_id, menu_item_id, date, "Breakfast", consumed, feedback))
                
                # Lunch
                menu_item_id = random.choice([1, 3, 7])
                consumed = random.randint(50, 100)
                feedback = "Good" if consumed >= 90 else "Adequate" if consumed >= 70 else "Poor"
                menu_selections.append((resident_id, menu_item_id, date, "Lunch", consumed, feedback))
                
                # Dinner
                menu_item_id = random.choice([5, 7])
                consumed = random.randint(60, 100)
                feedback = "Good" if consumed >= 90 else "Adequate" if consumed >= 70 else "Poor"
                menu_selections.append((resident_id, menu_item_id, date, "Dinner", consumed, feedback))
                
                # Dessert
                menu_item_id = random.choice([4, 6])
                consumed = random.randint(80, 100)
                feedback = "Good" if consumed >= 90 else "Adequate" if consumed >= 70 else "Poor"
                menu_selections.append((resident_id, menu_item_id, date, "Dessert", consumed, feedback))
                
        cursor.executemany('''
        INSERT INTO menu_selections (resident_id, menu_item_id, date, meal_time, 
                                   consumed_percent, feedback)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', menu_selections)
        print(f"Added {len(menu_selections)} menu selections")
        
        # Insert leftover food records for meals that weren't fully consumed
        leftover_records = []
        cursor.execute("SELECT id, consumed_percent FROM menu_selections WHERE consumed_percent < 100")
        not_fully_consumed = cursor.fetchall()
        
        for menu_selection_id, consumed_percent in not_fully_consumed:
            leftover_percent = 100 - consumed_percent
            reason = random.choice(["Didn't like it", "Too much", "Not hungry", "Felt unwell", "Too spicy"])
            leftover_records.append((menu_selection_id, leftover_percent, reason))
        
        if leftover_records:
            cursor.executemany('''
            INSERT INTO leftover_food (menu_selection_id, amount_percent, reason)
            VALUES (?, ?, ?)
            ''', leftover_records)
            print(f"Added {len(leftover_records)} leftover food records")
        
        # Insert trust account transactions
        transactions = []
        for resident_id in range(1, len(residents) + 1):
            balance = 500  # Starting balance
            
            # Deposit
            amount = round(random.uniform(100, 300), 2)
            balance += amount
            transactions.append((resident_id, datetime.datetime.now() - datetime.timedelta(days=15), 
                               amount, 'Deposit', 'Family deposit', balance, 'Admin'))
            
            # Various transactions
            for i in range(4):
                day_offset = random.randint(1, 14)
                amount = round(random.uniform(10, 50), 2)
                transaction_type = random.choice(['Withdrawal', 'Purchase', 'Service fee'])
                description = random.choice(['Hairdresser', 'Café purchase', 'Newspaper', 'Gift shop', 'Outing expense'])
                balance -= amount
                transactions.append((resident_id, datetime.datetime.now() - datetime.timedelta(days=day_offset), 
                                   -amount, transaction_type, description, balance, 'Caregiver'))
                
        cursor.executemany('''
        INSERT INTO trust_account_transactions (resident_id, transaction_date, 
                                             amount, transaction_type, 
                                             description, balance_after, processed_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', transactions)
        print(f"Added {len(transactions)} trust account transactions")
    
    else:
        print("Resident data already exists, skipping sample data insertion")
    
    conn.commit()
    print("Assisted living sample data added successfully")

def display_tables_info(conn):
    """Display information about the tables in the database"""
    cursor = conn.cursor()
    
    # Get and display all tables
    tables = get_existing_tables(conn)
    
    # For each smart home table, display a sample of data
    smart_home_tables = ["smart_devices", "rooms", "device_history"]
    for table in smart_home_tables:
        if table in tables:
            print(f"\nData sample from {table}:")
            cursor.execute(f"SELECT * FROM {table} LIMIT 5")
            rows = cursor.fetchall()
            # Get column names
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            print("Columns:", columns)
            for row in rows:
                print(row)
    
    # For each assisted living table, display a sample of data
    assisted_living_tables = ["residents", "health_vitals", "doctor_visits", "allergies", "sleep_quality", "activities", "activity_participation", "outings", "dietary_requirements", "menu_items", "menu_selections", "leftover_food", "trust_account_transactions"]
    for table in assisted_living_tables:
        if table in tables:
            print(f"\nData sample from {table}:")
            cursor.execute(f"SELECT * FROM {table} LIMIT 5")
            rows = cursor.fetchall()
            # Get column names
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            print("Columns:", columns)
            for row in rows:
                print(row)

def main():
    """Main function"""
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file {DB_PATH} not found")
        return
    
    # Connect to the database
    conn = create_connection(DB_PATH)
    if conn is None:
        return
    
    # Get existing tables
    get_existing_tables(conn)
    
    # Create tables
    create_smart_home_tables(conn)
    create_assisted_living_tables(conn)
    
    # Insert sample data
    insert_sample_data(conn)
    insert_assisted_living_sample_data(conn)
    
    # Display information about the tables
    display_tables_info(conn)
    
    # Close the connection
    conn.close()
    print("\nDatabase update completed successfully.")

if __name__ == "__main__":
    main()
