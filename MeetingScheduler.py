import psycopg2
import re
from datetime import datetime
from icalendar import Calendar, Event

# Connecting to the database using psycopg2
conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="2002", port=5432)
cur = conn.cursor()

def initialize_database():
    """
    Initialize the database by creating 'Persons' and 'Meetings' tables if they don't exist
    """
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Persons (
                person_id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS Meetings (
                meeting_id SERIAL PRIMARY KEY,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                participants VARCHAR(1000)[] NOT NULL
            )
        """)

        conn.commit()
        print("Database initialized successfully!")
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        
def validate_name(name):
    """
    The function checks if the provided name contains at least two parts (first name and last name) 
    and if all characters in the name are within the allowed set of characters, which includes 
    letters (uppercase and lowercase), spaces, and hyphens.
    :param name: the name to be validated
    :return: True if the name meets the criteria, False otherwise
    """
    if len(name.split()) < 2:
        return False
    
    allowed_characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ -"
    if not all(char in allowed_characters for char in name):
        return False
    
    return True

def extract_person_name(command):
    """
    Extracts the name of the person entered in the command line.
    :param command: the command given as input
    :return: the name extracted from the input command or None if the name extracted is not in a valid form
    """
    parts = command.split(' ')
    name = ' '.join(parts[2:])
    
    if validate_name(name):
        return name
    else:
        return None 
    
def normalize_name(name):
    """
    The function performs the following operations on the provided name:
    1. Removes leading and trailing whitespaces
    2. Converts the name to lowercase
    3. Replaces hyphens with spaces
    4. Consolidates multiple consecutive spaces into a single space
    :param name: the name to be normalized
    :return: the normalized name
    """
    name = name.strip()
    name = name.lower()
    name = name.replace("-", " ")
    name = " ".join(name.split())
    
    return name

def are_names_equivalent(name1, name2):
    """
    Check if two names are equivalent after normalization.
    :param name1: the first name for comparison
    :param name2: the second name for comparison
    :return: True if the normalized tokens of the names are equivalent, False otherwise
    """
    name1_tokens = normalize_name(name1).split()
    name2_tokens = normalize_name(name2).split()

    return set(name1_tokens) == set(name2_tokens) 
    
def add_person(name): 
    """
    Adds a person's name to the database if the name does not already exist.
    :param name: the name of the person to be added 
    """
    try:
        cur.execute("SELECT name FROM Persons")
        existing_names = cur.fetchall()

        for existing_name in existing_names:
            existing_name = existing_name[0]
            if are_names_equivalent(name, existing_name):
                print(f"{name} is equivalent to an existing name in the database: {existing_name}. Not added")
                return

        cur.execute("INSERT INTO Persons (name) VALUES (%s)", (name,))
        conn.commit()
        print(f"Added {name} to the database")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Database error: {e}")
        
def identify_datetime(text):
    """
    Identifies the start and end date-time values from a given text.
    :param text: the input text containing date-time information
    :return: if both of them are found, returns a tuple containing start and end date-time values in the format (start_date_time, end_date_time), otherwise returns a tuple of None
    """
    date_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}'
    dates = re.findall(date_pattern, text)
    
    if len(dates) >= 2:
        return dates[0], dates[1]
    else:
        print("Not enough start and end dates were found")
        return None, None

def identify_participants(text):
    """
    Identifies participants' names from the given text.
    :param text: the input text containing information about participants
    :return: a string containing the identified participants' names, separated by commas
    """
    name_pattern = r'\b(?:[A-Z][a-z]* ){1,3}[A-Z][a-z]*\b'
    potential_names = re.findall(name_pattern, text)
    participants = ', '.join(potential_names)
    
    return participants
        
def identify_datetime_and_participants(text):
    """
    Identifies start date-time, end date-time, and participants's names from the given text.
    :param text: the input text containing information about date-time and participants
    :return: If valid date-time information and participants are identified, returns a tuple in the format (start_date_time, end_date_time, [participants_list]). If insufficient or invalid information is found, it returns None for all values.
    """
    start_time, end_time = identify_datetime(text)
    
    if start_time and end_time:
        participants_text = text.split(end_time)[1].strip()
        participants = identify_participants(participants_text)
        
        if ',' in participants: 
            return start_time, end_time, participants.split(', ')
        else: # a single person's name
            extracted_name = extract_person_name(text)
            if extracted_name:
                return start_time, end_time, [extracted_name]
            else:
                print("Names of participants are invalid")
                return None, None, None
    else:
        return None, None, None
    
def validate_date(date_text):
    """
    Checks if the input text conforms to a valid date-time format.
    :param date_text: the input text representing a date-time string
    :return: True if the input string matches the specified date-time format, False otherwise
    """
    try:
        datetime.strptime(date_text, "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False
    
def schedule_meeting(start_time, end_time, participants):
    """
    Schedule a meeting in the database, if not already exists, given start and end times along with participants.
    :param start_time: the starting time of the meeting 
    :param end_time: the ending time of the meeting
    :param participants: a comma-separated string of participant names
    """
    try:
        if start_time >= end_time:
            print("Start time should be before end time.")
            return

        cur.execute("SELECT * FROM Meetings WHERE start_time = %s AND end_time = %s", (start_time, end_time))
        existing_meeting = cur.fetchone()

        if existing_meeting:
            print("Meeting already exists with the same start and end time.")
        else:
            cur.execute("INSERT INTO Meetings (start_time, end_time, participants) VALUES (%s, %s, %s)", (start_time, end_time, participants))
            conn.commit()
            print("Meeting scheduled successfully")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Database error: {e}")

def schedule_meeting_from_input(command):
    """
    Parse user input command to schedule a meeting.
    :param command: the input command that contains meeting details
    """
    try:
        start_time, end_time, participants = identify_datetime_and_participants(command)
        
        if not (validate_date(start_time) and validate_date(end_time)):
            print("The date format entered is invalid. Please use the format YYYY-MM-DD HH:MM")
            return
        
        schedule_meeting(start_time, end_time, participants)
    except Exception as e:
        print(f"An error occurred: {e}")
        
def get_meetings_in_interval(start_time, end_time):
    """
    Retrieving meetings from the database within a specified timeframe (start_time, end_time) and displaying them.
    :param start_time: the start time of the interval
    :param end_time: the end time of the interval
    """
    try:
        cur.execute("SELECT * FROM Meetings WHERE start_time >= %s AND end_time <= %s", (start_time, end_time))
        meetings = cur.fetchall()

        if meetings:
            print("Meetings:")
            for meeting in meetings:
                print(f"Start Time: {meeting[1]}, End Time: {meeting[2]}, Participants: {meeting[3]}")
        else:
            print("No meetings found in the specified interval")
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        
def display_meetings_from_input(command):
    """
    Display meetings based on the time interval specified in the input command.
    :param command: the user command containing information about the time interval
    """
    try:
        start_time, end_time = identify_datetime(command)
        
        if not (validate_date(start_time) and validate_date(end_time)):
            print("The date format entered is invalid. Please use the format YYYY-MM-DD HH:MM")
            return
        
        get_meetings_in_interval(start_time, end_time)
    except Exception as e:
        print(f"An error occurred: {e}")
        
def export_to_ical():
    """
    Export meetings from the database to an iCalendar file.
    """
    try:
        cur.execute("SELECT * FROM Meetings")
        meetings = cur.fetchall()

        cal = Calendar()

        for meeting in meetings:
            event = Event()
            event.add('summary', 'Meeting')
            event.add('dtstart', meeting[1])
            event.add('dtend', meeting[2])
            event.add('description', meeting[3])
            cal.add_component(event)

        with open('meetings.ics', 'wb') as f:
            f.write(cal.to_ical())

        print("Meetings exported to meetings.ics")
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error exporting to iCalendar: {e}")
        
def import_from_ical(file_path):
    """
    Import meetings from an iCalendar file into the database.
    :param file_path: the path to the iCalendar file to be imported
    """
    try:
        if not file_path.endswith('.ics'):
            print("Invalid file format. Please provide a file with the .ics extension")
            return
        
        with open(file_path, 'rb') as f:
            cal = Calendar.from_ical(f.read())

        for component in cal.walk():
            if component.name == 'VEVENT':
                start_time = component.get('dtstart').dt
                end_time = component.get('dtend').dt
                description = component.get('description')
                
                cur.execute("SELECT * FROM Meetings WHERE start_time = %s AND end_time = %s", (start_time, end_time))
                existing_meeting = cur.fetchone()

                if existing_meeting:
                    print(f"Meeting {start_time} to {end_time} already exists")
                else:
                    cur.execute("INSERT INTO Meetings (start_time, end_time, participants) VALUES (%s, %s, %s)", (start_time, end_time, description))
                    conn.commit()
                    print(f"Meeting {start_time} to {end_time} imported from iCalendar")
                
    except FileNotFoundError:
        print("File not found")
    except Exception as e:
        print(f"Error importing from iCalendar: {e}")           

def process_command(command):
    """
    Process the given command to perform specific actions.
    :param command: the input command to be processed

    Example Commands:
    - 'adauga persoana Popescu Ion'
    - 'adauga sedinta care va incepe la 2020-11-20 14:00, se va termina la 2020-11-20 14:30 si la care vor participa Ion Popescu, Ana Maria'
    - 'adauga sedinta din intervalul 2020-11-20 14:00 si 2020-11-20 14:30, la care participa urmatoarele persoane Ion Popescu, Ana Maria'
    - 'adauga sedinta 2020-11-20 17:00 2020-11-20 18:00, cu participantii Ion Popescu, Ana Maria'
    - 'afiseaza sedintele din intervalul 2020-11-20 08:00, 2020-11-20 23:59'
    - 'exporta sedintele'
    - 'importa sedintele din meetings.ics'
    """
    try:
        if command.lower().startswith('adauga persoana'):
            person_name = extract_person_name(command)
            if person_name is not None:
                add_person(person_name)
            else:
                print("Invalid name")
                
        elif command.lower().startswith('adauga sedinta'):
            schedule_meeting_from_input(command)
            
        elif command.lower().startswith('afiseaza sedintele'):
            display_meetings_from_input(command)
            
        elif command.lower().startswith('exporta sedintele'):
            export_to_ical()
            
        elif command.lower().startswith('importa sedintele'):
            file_path = command.split('importa sedintele din ')[1]
            import_from_ical(file_path)
            
        else:
            print("Invalid command")
    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    """
    Main function to manage user input and command processing for database operations.
    """
    initialize_database()    
    
    while True:
        command = input("Input: ")
        
        if command.lower().startswith('exit'):
            break
        
        process_command(command)


if __name__ == "__main__":
    main()
    
# Close the cursor and the database connection.
cur.close()
conn.close()