# FASTapi-bookstore

CPSC 449 Final Project

## By

Melanie Mach #888079639

Michael Martinez #

## Steps to run:

### Step 1

- Clone the repository and navigate to the root directory of your project
  ``` sh
   cd '<repository location>'
   cd 'FASTapi-bookstore'
   cd 'bookstore'
  ```

### Step 2

- Install the dependencies from `requierments.txt` 
  ```sh
  pip install -r .\requirements.txt
  ```

### Step 3 

- Run the following command to start the API
  ```sh
  uvicorn main:app
  ```
- Use this if you're making edits while running the code to keep it up to date
  ```sh
  uvicorn main:app --reload
  ```
 - Uvicorn will start and display the URL where your application is running. `ex.: 'http://127.0.0.1:8000'`

### Step 4 

- Open a web browser and navigate to `http://127.0.0.1:8000/docs#/`
- Use each Dev Helper to help run endpoints and you should be set to run each route!

