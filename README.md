#TopoLock

### Secure CRM for safer relationships

To run an this app on localhost with specific environment variables, you can follow these steps:

Set up a Virtual Environment (Optional): It is recommended to set up a virtual environment to isolate the dependencies of your Flask app. Open your terminal or command prompt, navigate to the directory where your Flask app is located, and run the following commands:

python -m venv env       # Create a virtual environment
source env/bin/activate # Activate the virtual environment (for Unix/Linux)
env\Scripts\activate    # Activate the virtual environment (for Windows)
Set the FLASK_APP Variable: In your terminal or command prompt, navigate to the directory where your Flask app is located and run the following command to set the FLASK_APP environment variable to app.py (assuming your Flask app is in a file named app.py):

export FLASK_APP=app.py  # For Unix/Linux
set FLASK_APP=app.py     # For Windows (Command Prompt)
Set the Environment Variables: Set the required environment variables for your Flask app. Assuming you have the following environment variables to set: API_TOKEN, CONFIG_ID, LOG_API_TOKEN, MAIL_USERNAME, and MAIL_PASSWORD. In your terminal or command prompt, run the following commands to set the environment variables:

export API_TOKEN=your_api_token
export CONFIG_ID=your_config_id
export LOG_API_TOKEN=your_log_api_token
export MAIL_USERNAME=your_mail_username
export MAIL_PASSWORD=your_mail_password
Run the App: Start the Flask app by running the following command in your terminal or command prompt:

flask run
The Flask app will start running on port 5000 by default.

Access the App: Once the server is running, you can access your Flask app by opening a web browser and navigating to http://localhost:5000. You should be able to interact with your Flask app based on its functionality.
