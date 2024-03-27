# Expense Tracker

Expense Tracker is a web application built with Flask that allows users to track their expenses and income.

## Features

- User authentication: Users can sign up, log in, and log out securely.
- Adding notes: Users can add expenses and income with details like amount, type, and comments.
- Deleting notes: Users can delete their own notes.

## Installation

1. Clone the repository:

    ```
    git clone https://github.com/GulmurodY/expense-tracker.git
    ```

2. Navigate into the project directory:

    ```
    cd expense-tracker
    ```

3. Install dependencies:

    ```
    pip install -r requirements.txt
    ```

4. Set up the database:

    ```
    flask db init
    flask db migrate
    flask db upgrade
    ```

5. Run the application:

    ```
    flask run
    ```

6. Open a web browser and go to http://localhost:8000 to access the application.

## Usage

- Sign up for a new account or log in with an existing account.
- Once logged in, you'll be taken to the home page where you can view your records and add new ones.
- To add a new note, fill in the amount, select the type (income or expense), add a comment if desired, and click the "Add Note" button.
- To delete a note, click the delete button next to the note you want to delete.

## Technologies Used

- Flask: Python web framework for building the backend.
- Flask-SQLAlchemy: Flask extension for working with SQLAlchemy, an ORM for database interactions.
- Flask-Login: Flask extension for handling user authentication.
- HTML/CSS/JavaScript: Frontend technologies for building the user interface and interactivity.
