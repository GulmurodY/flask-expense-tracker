# Expense Tracker

Expense Tracker is a web application built with Flask that allows users to easily track their expenses and income, helping them stay on top of their finances.

## Features

- **User Authentication**: Secure sign-up, log-in, and log-out functionality.
- **Expense & Income Tracking**: Add and view your income and expense records.
- **Record Management**: Ability to delete any of your financial records.
## Demonstration
![Demo](https://github.com/GulmurodY/flask-expense-tracker/blob/main/expense-tracker-demo.gif)
## Installation

Follow these steps to get the application running locally:

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/GulmurodY/expense-tracker.git
    ```

2. **Navigate into the Project Directory**:

    ```bash
    cd expense-tracker
    ```

3. **Install Dependencies**:

    First, create and activate a virtual environment, then run the following command to install all required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. **Run the App**:

    Start the application using:

    ```bash
    python main.py
    ```

5. **Access the Application**:

    Open your web browser and visit [http://localhost:8000](http://localhost:8000) to access the Expense Tracker.

## Usage

- **Sign Up & Log In**: Create a new account or log in with your existing credentials.
- **Home Page**: Once logged in, you will be redirected to the home page where you can see all your tracked records.
- **Adding a Note**: To add a new note, enter the amount, select the type (income or expense), add a comment if desired, and click the **Add Note** button.
- **Deleting a Note**: To delete a note, simply click the delete button next to the transaction you want to remove.

## Technologies Used

- **Flask**: A lightweight Python web framework for backend development.
- **Flask-SQLAlchemy**: Flask extension to work with SQLAlchemy for database interactions.
- **Flask-Login**: Manages user sessions and authentication.
- **HTML/CSS/JavaScript**: For the frontend, providing a clean and responsive user interface.
