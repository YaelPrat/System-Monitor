# System Monitor
## System Monitor is a web application built using Flask, SQLAlchemy, and SocketIO for real-time monitoring of system metrics such as CPU usage, memory usage, and disk usage.

### Features
Real-time System Metrics: View real-time CPU usage, memory usage, and disk usage metrics in the form of charts.
Averages Dashboard: Check the average CPU, memory, and disk usage for a selected date.
Abnormal Results Dashboard: Monitor abnormal system metrics such as CPU, memory, and disk usage exceeding predefined thresholds.
Interactive Interface: Select a specific date to view historical system metrics.
Responsive Design: The application interface is designed to be responsive and accessible from various devices.


### Usage
- Home Page: Enter the IP address of the target system and click "Start Monitoring" to begin monitoring system metrics.
- Charts Dashboard: View real-time CPU usage, memory usage, and disk usage metrics in the form of interactive charts.
- Averages Dashboard: Select a specific date using the date picker to view average CPU, memory, and disk usage for that date.
- Abnormal Results Dashboard: Monitor abnormal system metrics such as CPU, memory, and disk usage exceeding predefined thresholds.

### Configuration
Database: The application uses SQLite as the default database. 

### Dependencies
- Flask
- Flask-Migrate
- Flask-SocketIO
- Flask-SQLAlchemy
- Paramiko
- Chart.js
- jQuery

### Instructions
1. Clone the repository to your local machine.
2. Install the required dependencies using pip:
    ```
    pip install -r requirements.txt
    ```
3. Ensure you have access to a virtual machine running Kali Linux.
4. Set up the virtual machine's IP address, username, and password in the application. By default, the username and password are set to "kali" for authentication. The IP address should be provided as input when running the application.
5. Run the Flask application using the following command:
    ```
    python app.py
    ```
6. Access the application in your web browser at http://localhost:5006.

### Notes
- The application expects input in the form of the virtual machine's IP address. Ensure that the IP address is correctly configured to establish an SSH connection.
- The default username and password for authentication are set to "kali". Modify these credentials as needed based on your virtual machine setup.


### Author
Barak, Dor, Raziel, Yael Prat.