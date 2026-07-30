# Home Service Marketplace Backend

## Tech Stack

* **Framework:** Flask & Flask-SQLAlchemy
* **Database:** SQLite (Development) / SQLAlchemy compatible
* **Authentication:** Flask-JWT-Extended (JSON Web Tokens)
* **Environment Management:** Pipenv, Python-Dotenv

## What It's About:

This is a RESTful API backend built to support the Home Service Marketplace platform.
Ensures secure user registration, token-based authentication, administrative controls, and service listing management.
Features custom administrative endpoints, ensuring authorized users can manage, oversee, and view platform user data securely.
Designed with clean code to seamlessly integrate with the frontend.

## How to Use It:

* Clone the repository and navigate into the backend directory.
* Create and activate a Python virtual environment using Pipenv: `pipenv install` followed by `pipenv shell`.
* Configure environment variables by creating a `.env` file in the root directory.
* Run database migrations and start the development server: `pipenv run python3 run.py`.

## API Architecture & Features:

* **User Authentication:** Endpoints for user signup, login, logout, and profile retrieval via JWT (`/api/auth`).
* **Administration:** Secure endpoints allowing authenticated admin users to view and manage user accounts (`/api/admin`).
* **Listing Management:** Modular routes for managing service listings and platform resources.

## Conclusion:

Home Service Marketplace Backend delivers a secure, highly scalable API foundation capable of managing core marketplace workflows.
With token-based security and clean modular structuring, it powers seamless integration across full-stack environments.

## Licenses:

This project is licensed under the MIT License.

## Authors

1. Prince Evanson
2. Marian Adisa
3. Safia Bulle
4. Mercy Cherop
