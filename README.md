# ngs_orders

This is a Django App for collection and storage of sequenicing orders for the sequencing facility. After registration/login the user can define orders, associate samples to a order and associate samples to  MIxS Sample Checklists.

## About The Project

This project, "Establishing data broker functionalities at HZI for optimizing omics data submissions to public repositories," is funded by HZI through the NFDI4Microbiota Strategy Funds in 2023. The initiative aims to enhance the submission process of omics data to public repositories, making it more efficient and streamlined.

![NFDI4Microbiota Logo](https://avatars.githubusercontent.com/u/97964957?s=200&v=4)

## Funding

This project is supported by the NFDI4Microbiota Strategy Funds, granted by the Helmholtz Centre for Infection Research (HZI) to facilitate the development of data broker functionalities for optimizing omics data submissions to public repositories.


## Installation

This project is developed with Django. To set up and run the project locally, follow these steps:

### Prerequisites

- Python (3.8 or newer)
- pip (Python package installer)

### Setting Up a Virtual Environment

It's recommended to use a virtual environment for Python projects. This keeps dependencies required by different projects separate. To create a virtual environment, run:


```bash
python3 -m venv myenv
source myenv/bin/activate
```

### Installing Dependencies

```bash
pip install Django
```

### Running the Project

Navigate to the project directory and run:


```bash
python manage.py runserver
```

This will start the Django development server, and you should be able to access the project at `http://127.0.0.1:8000/`.


## Configuration 

## Changes on the Order form

The Order form can be changed by modifying the class OrderForm in `myapp/forms.py` and the `models.py`file that defines the SQL fields. Updates on the SQL tables requires migration of the table layout.

```
python manage.py makemigrations
python manage.py migrate
```

### Configuration of MIxS Sample Checklists

The application comes with 14 MIxS Sample Checklists that are downloaded from https://www.ebi.ac.uk/ena/browser/checklists. These are stored and can be changed and updated under `staticfiles/xml/EnviornmentID.xml`. These IDs should match `MIXS_METADATA_STANDARDS` defined in `mixs_metadata_standards.py`. After the .xml files are changed, run `python manage.py collectstatic` to update the static files. 

## Application Screenshots

Below are some screenshots that display the key functionalities of the application, including user registration/login, order creation, associating samples to an order, and associating samples to MIxS standards.

### User Registration/Login

![User Registration/Login](screenshots/image1.png)

This screenshot shows the user registration and login page, allowing users to access the application.

### Order Creation

![Order Creation](screenshots/image2.png)

Here, you can see the interface for creating a new sequencing order.

### Sample Association

![Sample Association](screenshots/image3.png)

This screenshot displays how a user can associate samples with a specific order.

### Associating MIxS Standards

![Associating MIxS Standards](screenshots/image3.png)

This image shows the functionality for associating samples with specific MIxS standards.