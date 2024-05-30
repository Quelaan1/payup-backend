import os
import subprocess
import platform
import sys

# Construct an absolute path to the docker-compose file
script_dir = os.path.dirname(os.path.abspath(__file__))
docker_compose_file = os.path.join(script_dir, "docker-compose.yaml")


def print_container_logs(container_name):
    """Prints the logs of the specified Docker container."""
    print(f"Logs for container {container_name}:")
    command = ["docker", "logs", container_name]
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Failed to get logs for {container_name}", e.output)


def run_command(command):
    """Runs a command and returns a tuple of success status and output."""
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return (True, result.stdout)
    except subprocess.CalledProcessError as e:
        return (False, e.stderr)


def is_docker_running():
    """Checks if Docker daemon is running."""
    return run_command(["docker", "info"])


def start_docker_linux():
    """Attempts to start Docker on Linux."""
    print("Attempting to start Docker on Linux...")
    return run_command(["sudo", "systemctl", "start", "docker"])


def start_docker_macos():
    """Instructs the user to start Docker on macOS."""
    print("Please ensure Docker Desktop is running on your macOS system.")
    return False


def start_docker_windows():
    """Instructs the user to start Docker on Windows."""
    print("Please ensure Docker Desktop is running on your Windows system.")
    return False


def start_docker():
    """Attempts to start Docker based on the operating system."""
    os_system = platform.system()
    if os_system == "Linux":
        return start_docker_linux()
    elif os_system == "Darwin":
        return start_docker_macos()
    elif os_system == "Windows":
        return start_docker_windows()
    else:
        print(f"Unsupported operating system: {os_system}")
        return False


def docker_compose_up():
    """Attempts to run docker-compose up and returns success status and output."""
    return run_command(["docker", "compose", "-f", docker_compose_file, "up"])


def docker_compose_down():
    """Runs docker-compose down to tear down containers."""
    _, output = run_command(["docker", "compose", "-f", docker_compose_file, "down"])
    return output


def main():
    try:
        docker_running, _ = run_command(["docker", "info"])
        if not docker_running:
            print("Docker is not running. Attempting to start Docker...")
            # Include your Docker starting logic here based on the platform

        print("Docker is running. Proceeding with Docker Compose...")
        success, output = docker_compose_up()
        if success:
            print("Docker Compose executed successfully.")
            print_container_logs("flyway")
        else:
            print("Docker Compose failed to execute.")
            print("Error:", output)
    finally:
        # Whether successful or not, tear down the containers
        print("Tearing down Docker containers...")
        # teardown_output = docker_compose_down()
        # print(teardown_output)


if __name__ == "__main__":
    main()
