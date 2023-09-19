# TopoLock

Open Source Project under MIT License https://opensource.org/license/mit/

<h2>How to Run this App on Localhost</h2>
<p>To run TopoLock app on localhost with specific environment variables, you can follow these steps:</p>
<h3>Set up a Virtual Environment (Optional)</h3>
<p>It is recommended to set up a virtual environment to isolate the dependencies of the app. Open your terminal or command prompt, navigate to the directory where your app is located, and run the following commands:</p>
<pre><code>python -m venv env       # Create a virtual environment
source env/bin/activate # Activate the virtual environment (for Unix/Linux)
env\Scripts\activate    # Activate the virtual environment (for Windows)
</code></pre>
<h3>Set the FLASK_APP Variable</h3>
<p>In your terminal or command prompt, navigate to the directory where the app is located and run the following command to set the FLASK_APP environment variable to app.py:</p>
<pre><code>export FLASK_APP=app.py  # For Unix/Linux
set FLASK_APP=app.py     # For Windows (Command Prompt)
</code></pre>
<h3>Set the Environment Variables</h3>
<p>Set the required environment variables for the app. Assuming you have the following environment variables to set: API_TOKEN, CONFIG_ID, LOG_API_TOKEN, MAIL_USERNAME, and MAIL_PASSWORD. In your terminal or command prompt, run the following commands to set the environment variables:</p>
<pre><code>export API_TOKEN=your_api_token
export CONFIG_ID=your_config_id
export LOG_API_TOKEN=your_log_api_token
export MAIL_USERNAME=your_mail_username
export MAIL_PASSWORD=your_mail_password
</code></pre>
<h3>Run the App</h3>
<p>Start the app by running the following command in your terminal or command prompt:</p>
<pre><code>flask run
</code></pre>
<p>The app will start running on port 5000 by default.</p>
<h3>Access the App</h3>
<p>Once the server is running, you can access the app by opening a web browser and navigating to <a href="http://localhost:5000">http://localhost:5000</a>. You should be able to interact with the app based on its functionality.</p>
