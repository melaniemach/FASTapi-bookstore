# FASTapi-bookstore

CPSC 449 Final Project

#### Link to Demo: https://www.dropbox.com/s/iw4d2mih709uwjd/FASTapi-bookstore-demo.mp4?dl=0

## By

Melanie Mach #888079639
melaniemach@csu.fullerton.edu

Michael Martinez #886914472
michael.mar413@csu.fullerton.edu

## Steps to run (based on MacOS):

### Step 1

- Clone the repository and navigate to the root directory of your project
  ``` sh
   cd '<repository location>'
   cd 'FASTapi-bookstore'
  ```

### Step 2

- Create a virtual environment (assuming user has most recent Python version)
  ```sh
  python3 -m pip install virtualenv
  python3 -m venv myenv
  source myenv/bin/activate
  ```
- When done working with virtual environment, run ``deactivate`` to restore default Python environment: 

### Step 3

- Install the dependencies from `requierments.txt` 
  ```sh
  pip install -r .\requirements.txt
  ```
  OR
- Install the dependencies using this command:
  ```sh
  pip install pymongo fastapi motor pydantic
  ```
  
### Step 4 

- Run the following command to start the API
  ```sh
  uvicorn main:app
  ```
- Use this if you're making edits while running the code to keep it up to date
  ```sh
  uvicorn main:app --reload
  ```
 - Uvicorn will start and display the URL where your application is running. `ex.: 'http://127.0.0.1:8000'`

### Step 5

- Open a web browser and navigate to `http://127.0.0.1:8000/docs#/`
- Use Swagger UI to help run endpoints and you should be set to run each route!
  - Video will demonstrate how to use Swagger UI




