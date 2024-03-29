# Meeting Scheduler - "Programming in Python" course

Meeting Scheduler is a graphical application developed as part of the "Programming in Python" course. This application is designed to efficiently schedule meetings, manage attendees, and provide export functionality to a standard calendar format. 

## Features

1. PostgreSQL Database Integration:

+ Meeting Scheduler integrates with a PostgreSQL database to store and manage meeting-related information and attendee details.

2. Interactive Menu Interface:

+ The application interacts with users through an intuitive menu system, offering the following commands:
  + Add a person to the database.
  + Schedule a future meeting (start date, end date, list of participants).
  + Display meetings within a specific time interval.
  + Export/Import to/from a standard calendar format(iCal).
    
3. Data Validation and Error Handling:

+ The application ensures validation of user input and provides error handling.
+ Informative messages are displayed in case of exceptions, guiding users on correct input.
  
4. Export/Import Functionality:

+ Users can export and import meeting data to/from a chosen standard calendar format.
+ The export/import functionality is implemented exclusively for a single calendar format to maintain simplicity.

Example commands in the interactive menu:
```
adauga persoana Popescu Ion
adauga sedinta care va incepe la 2020-11-20 14:00, se va termina la 2020-11-20 14:30 si la care vor participa Ion Popescu, Ana Maria
adauga sedinta 2020-11-20 17:00 2020-11-20 18:00, cu participantii Ion Popescu, Ana Maria
afiseaza sedintele din intervalul 2020-11-20 08:00, 2020-11-20 23:59
exporta sedintele
importa sedintele din meetings.ics
```
