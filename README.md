# Asset Management Project

## Overview

The Asset Management Project is a comprehensive solution designed to help organizations efficiently manage their assets. This project provides functionalities for asset information, maintenance, asset allocation to users under admin, and dashboard viewing. The system is built with a user-friendly interface.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Admin**: Maintain detailed records of all Assigned Users, Locations, Departments ,Product Types ,Product Categories ,Roles. 
- **Dashboard**: Displays information like Assets, Assigned/Unassigned Assets, Vendors ,Locations ,Products ,Users and Total Asset Cost in a tabular format along with      Upcoming Warranty Expiries and Recent Activities Performed in the dashboard.
- **Assets**:Assign people to assets by adding them and a list to display all the assigned peoples with their respective assets.
- **Upload**: To generate a sample file or upload them for all the displayed data of Vendors, Locations, Departments, Product Types, Product Categories.
- **Reporting and Analytics**: Generate reports on asset performance, utilization, and maintenance history.
- **User Management**: Role-based access control to secure sensitive asset information.
- **Integration**: API support for integrating with other enterprise systems.
- **Recycle Bin**:Contains all the previously deleted files by the admin and also has functionality to restore them.

## Installation

### Prerequisites

- [Python 3.9+](https://www.python.org/)
- [Mysql](https://www.mysql.com/) (Can be replaced by your preferred database)
- [Docker](https://www.docker.com/) (optional, for containerized deployment)

### Steps

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/assetmanagement.git
    cd asseto-asset-management
    ```

2. Create and activate a virtual environment:
    ```sh
    python -m venv env
    source env/bin/activate  # On Windows use `env\Scripts\activate`
    ```

3. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up environment variables:
    ```sh
    cp .env.example .env
    ```
    Edit the `.env` file with your preferred settings.

5. Apply migrations:
    ```sh
    python manage.py migrate
    ```

6. Start the development server:
    ```sh
    python manage.py runserver
    ```

7. Open your browser and navigate to `http://localhost:8000`.

8. Create a superuser if necessary:
    ``` sh
    python manage.py createsuperuser
    ```


## Usage

#### Try This Project with a Demo Account
You can use this project before downloading.
The project is hosted [here](https://asset-management-hg2x.onrender.com/login?next=/).\
\
Credentials:\
&nbsp;&nbsp;&nbsp;&nbsp; email: asset-management@demo.com \
&nbsp;&nbsp;&nbsp;&nbsp; password: DM4g476ZmQ$U

Log in with this credential and use the below features

### Admin

1. Navigate to the "Admin" section.
2. Admin Consists of Five Sections Locations,Departments, Product Types, Product Categories and Roles.
3. Each section have their own functionalities where you may perform according to our needs.(Add/Edit/Delete/View) 

### Vendors

1. Navigate to the "Vendors" section.
2. Click on the buttons as per your need. (Add/Edit/Delete/View venders).
3. Fill in the vendors detail and click save.
4. Searching of the vendors and downloading of details are also available. 

### Products

1. Navigate to the "Products" section.
2. Click on the buttons as per your need. (Add/Edit/Delete/View venders).
3. Fill in the Products detail and click save.
4. Searching of the Products and downloading of details are also available. 

### Users

1. Navigate to the "Users" section.
2. Click on the buttons as per your need. (Add/Edit/Delete/View venders).
3. Fill in the users detail and click save.
4. Searching of the Users and downloading of details are also available. 


### Assets

1. Navigate to the "Assets" section.
2. Click on the buttons as per your need. (Add/Edit/Delete/View assets).
3. Fill in the assets detail and click save.
4. Assigned Assets also contains a list of all the assets assigned to different individuals with search functionalities and Reassign/Unassign features.

### Upload

1. Navigate to the "Upload" section.
2. Upload Consists of Five Sections Locations,Departments, Product Types, Product Categories and Vendors.
3. Each section have their own functionalities where you may either upload the data or get to download a sample.


### Recycle Bin

1. Contains all the previously deleted files by the admin and also has functionality to restore them divided in each category

## Configuration

Configuration options are managed via the `.env` file. Key settings include:

Copy the settings from .env.example file



## Contributing

We welcome contributions! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a pull request.

Please ensure your code follows our [coding standards](CONTRIBUTING.md).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For any inquiries or support, please contact:

- Email: info@vyrazu.com
- Project Maintainer: [Vyrazu Labs Ltd](https://vyrazu.com/)
