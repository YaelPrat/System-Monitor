from flask import Flask, render_template, jsonify, request
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
import paramiko

app = Flask(__name__)
socketio = SocketIO(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///site.db"
app.config['SECRET_KEY'] = 'secret_key_'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float)
    type = db.Column(db.String(50))  # Type of the sample ( CPU, memory, RAM)
    date = db.Column(db.DateTime, default=db.func.current_date())

    def serialize(self):
        return {
            'id': self.id,
            'value': self.value,
            'type': self.type,
            'date': self.date
        }


# Create a sample
def add_sample(value, type_):
    new_sample = Sample(value=value, type=type_)
    db.session.add(new_sample)
    db.session.commit()


def get_samples_by_date_and_type(target_date, sample_type):
    # Query the Sample table for samples with the specified date and type
    with app.app_context():
        samples = Sample.query.filter_by(date=target_date[:10], type=sample_type).all()
        return samples


def get_abnormal_samples(type_):
    with app.app_context():
        if type_ == 'CPU':
            samples_cpu = Sample.query.filter(Sample.value > 50, Sample.type == 'CPU').all()
            return samples_cpu
        if type_ == 'RAM':
            samples_ram = Sample.query.filter(Sample.value > 70, Sample.type == 'RAM').all()
            return samples_ram
        if type_ == 'DISK':
            samples_disk = Sample.query.filter(Sample.value > 90, Sample.type == 'DISK').all()
            return samples_disk


@app.route('/getAvgs', methods=['GET'])
def getAvgs():
    # Get the date parameter from the request query string
    selected_date = request.args.get('date', default=None)

    if selected_date:
        cpu_samples = get_samples_by_date_and_type(selected_date, "CPU")
        ram_samples = get_samples_by_date_and_type(selected_date, "RAM")
        disk_samples = get_samples_by_date_and_type(selected_date, "DISK")

        # Calculate averages
        cpu_avg = round(sum(x.value for x in cpu_samples) / len(cpu_samples), 2) if cpu_samples else 0
        ram_avg = round(sum(x.value for x in ram_samples) / len(ram_samples), 2) if ram_samples else 0
        disk_avg = round(sum(x.value for x in disk_samples) / len(disk_samples), 2) if disk_samples else 0

        # Prepare data for JSON response
        data = {
            'cpu': cpu_avg,
            'ram': ram_avg,
            'disk': disk_avg,
        }

        return jsonify(data)
    else:
        # Handle case where no date is provided
        return jsonify({'error': 'Date parameter is missing'}), 400


# Define a global variable for storing historical data
cpu_history = []
memory_history = []
disk_history = []
db_counter = 0
ssh_client = paramiko.SSHClient()



@app.route('/', methods=['GET', 'POST'])
def index():
    global ssh_client
    # if ssh_client.get_transport().isAlive():
    #     ssh_client.close()
    if request.method == 'POST':
        global ip
        ip = request.form.get("ip")
        host = ip
        username = 'kali'
        password = 'kali'
        # Connect to the VM
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh_client.connect(hostname=host, username=username, password=password, timeout=2)
        except Exception as e:
            return render_template("homepage.html", error="The IP invalid")

        return render_template("charts.html")
    ssh_client.close()
    return render_template("homepage.html")


@app.route('/charts')
def charts():
    return render_template("charts.html")


@app.route('/averages')
def averages():
    return render_template("averages.html")


@app.route('/system_metrics')
def system_metrics():
    global cpu_history, memory_history, disk_history
    global db_counter

    # Get current system metrics
    cpu_percent, disk_usage, memory = get_data(ip)

    # Append current metrics to history
    cpu_history.append(cpu_percent)
    memory_history.append(memory)
    disk_history.append(disk_usage)

    # Keep history length limited to last 50 data points
    cpu_history = cpu_history[-50:]
    memory_history = memory_history[-50:]

    # Prepare data for JSON response
    data = {
        'cpu_percent': cpu_percent,
        'memory_percent': memory,
        'disk_percent': disk_usage,
        'cpu_history': cpu_history,
        'memory_history': memory_history
    }

    db_counter = db_counter + 1
    if db_counter % 10 == 0:
        add_sample(float(cpu_percent), "CPU")
        add_sample(float(memory), "RAM")
        add_sample(float(disk_usage), "DISK")
    return jsonify(data)


@app.route('/abnormal')
def abnormal():
    arg = request.args.get('arg')  # Retrieve the argument from the query parameters
    samples = get_abnormal_samples(arg)
    data = {
        'samples': [sample.serialize() for sample in samples]
    }
    return jsonify(data)


def get_data(ip):
    # Define SSH connection parameters
    # Execute commands on the VM
    cpu_stdin, cpu_stdout, cpu_stderr = ssh_client.exec_command(
        "top -bn1 | grep '^%Cpu' |  awk '{print $2 + $4 + $6 + $9 + $11 + $13 + $15}'")
    mem_stdin, mem_stdout, mem_stderr = ssh_client.exec_command(''' df -h | awk '$NF=="/"{print ($3/$2)*100}' ''')
    ram_stdin, ram_stdout, ram_stderr = ssh_client.exec_command("free | awk '/^Mem:/{print ($3/$2)*100}'")

    cpu_output, mem_output, ram_output = cpu_stdout.read().decode('utf-8'), mem_stdout.read().decode(
        'utf-8'), ram_stdout.read().decode('utf-8')
    # Close the standard input, output, and error streams
    if cpu_stdin and mem_stdin and ram_stdin:
        cpu_stdin.close()
        mem_stdin.close()
        ram_stdin.close()
    if cpu_stdout and mem_stdout and ram_stdout:
        cpu_stdout.close()
        mem_stdout.close()
        ram_stdout.close()
    if cpu_stderr and mem_stderr and ram_stderr:
        cpu_stderr.close()
        mem_stderr.close()
        ram_stderr.close()
    # Close the SSH connection
    return cpu_output.strip(), mem_output.strip(), ram_output.strip()


def get_active_processes():
    try:
        # Execute command to get active processes
        stdin, stdout, stderr = ssh_client.exec_command('ps aux')
        output = stdout.read().decode('utf-8')

        # Process the output to extract relevant information
        active_processes = [line.split() for line in output.splitlines()]
        usernames = set(process[0] for process in active_processes)

        return active_processes, usernames
    except Exception as e:
        return []


@app.route('/active_processes')
def active_processes():
    processes, usernames = get_active_processes()
    return render_template('active_processes.html', processes=processes, usernames=usernames)


@app.route('/filtered_processes', methods=['GET'])
def filtered_processes():
    # Get the selected username from the request query string
    selected_username = request.args.get('username')
    print(selected_username)
    try:
        # Execute command to get active processes
        stdin, stdout, stderr = ssh_client.exec_command('ps aux')
        output = stdout.read().decode('utf-8')

        # Process the output to extract relevant information
        active_processes = [line.split() for line in output.splitlines()]
    except Exception as e:
        # Handle exceptions gracefully
        app.logger.error(f"Failed to fetch active processes: {str(e)}")
        return jsonify({'error': 'Failed to fetch active processes'}), 500

    if selected_username:
        # Filter active processes based on the selected username
        filtered_processes = [process for process in active_processes if process[0] == selected_username]
        print(filtered_processes)
    else:
        # If no username is selected, return all active processes
        filtered_processes = active_processes

    # Return the filtered processes as JSON
    return jsonify(filtered_processes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006, debug=True)
