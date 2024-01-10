from collections import OrderedDict
from ruamel.yaml import YAML
import argparse
import os

TOPLEVEL_ORDER = ['version', 'services', 'volumes', 'networks', 'secrets']
SERVICE_ORDER = [
    'image', 'command', 'entrypoint', 'container_name',
    'links', 'volumes_from', 'volumes', 'volume_driver', 'tmpfs',
    'build',
    'expose', 'ports',
    'net', 'network_mode', 'networks',
    'deploy',
    'labels',
    'devices',
    'read_only',
    'healthcheck',
    'env_file', 'environment',
    'secrets',
    'cpu_shares', 'cpu_quota', 'cpuset', 'domainname', 'hostname', 'ipc',
    'mac_address', 'mem_limit', 'memswap_limit', 'privileged', 'shm_size',
    'depends_on', 'extends', 'external_links',
    'stdin_open', 'user', 'working_dir',
    'extra_hosts', 'restart', 'ulimits', 'tty', 'dns', 'dns_search', 'pid',
    'security_opt', 'cap_add', 'cap_drop', 'cgroup_parent', 'logging', 'log_driver', 'log_opt',
    'stopsignal', 'stop_signal', 'stop_grace_period',
    'sysctls', 'userns_mode',
    'autodestroy', 'autoredeploy',
    'deployment_strategy', 'sequential_deployment', 'tags', 'target_num_containers',
    'roles']


def sort_yaml_file(file_path, result_file_path):
    yaml = YAML(typ='rt')  # Use RoundTrip
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.preserve_quotes = True

    # Load the YAML file into a Python dictionary
    with open(file_path, 'r') as file:
        lines = file.readlines()
        lines = [line for line in lines if line.strip()]
        data = yaml.load(''.join(lines))

    # Create a new OrderedDict where the keys are sorted according to TOPLEVEL_ORDER
    # Check if data is a dictionary
    if isinstance(data, dict):
        # Create a new OrderedDict where the keys are sorted according to TOPLEVEL_ORDER
        sorted_data = OrderedDict((key, data[key]) for key in TOPLEVEL_ORDER if key in data)
        remaining_keys = set(data.keys()) - set(TOPLEVEL_ORDER)
        sorted_data.update((key, data[key]) for key in remaining_keys)
        # If 'services' is one of the keys, sort its sub-keys according to SERVICE_ORDER
        if 'services' in sorted_data:
            for service_name, service_data in sorted_data['services'].items():
                sorted_service_data = OrderedDict(
                    (key, service_data[key]) for key in SERVICE_ORDER if key in service_data)
                remaining_keys = set(service_data.keys()) - set(SERVICE_ORDER)
                sorted_service_data.update((key, service_data[key]) for key in remaining_keys)

                # Sort the elements under 'depends_on', 'environment', 'labels', 'ports', 'volumes' alphabetically
                for key in ['depends_on', 'ports', 'volumes']:
                    if key in sorted_service_data and isinstance(sorted_service_data[key], list):
                        sorted_service_data[key] = sorted(sorted_service_data[key])

                sorted_data['services'][service_name] = dict(sorted_service_data)  # Convert to regular dict
        # Write the modified YAML string back to the new YAML file
        with open(result_file_path, 'w') as file:
            for key, value in dict(sorted_data).items():
                yaml.dump({key: value}, file)
                file.write('\n')  # Add a newline after each top-level element
    else:
        print("The YAML file does not contain a dictionary at the top level.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sort a docker-compose.yml file.')
    parser.add_argument('input', help='Path to YAML or directory to sort.')
    parser.add_argument('-o', '--output', help='Output file to write sorted YAML, if empty will be overwritten.')
    parser.add_argument('-n', '--name', help='add to name of output file')
    args = parser.parse_args()

    if args.output is None:
        args.output = args.input

    nameSuffix = ''
    if args.name is not None:
        nameSuffix = args.name

    files_changed = 0

    if os.path.isdir(args.input):
        for dirpath, dirnames, filenames in os.walk(args.input):
            for filename in filenames:
                if filename.startswith('docker-compose') and (filename.endswith('.yml') or filename.endswith('.yaml')):
                    input_file_path = os.path.join(dirpath, filename)
                    output_file_path = os.path.join(dirpath, filename + nameSuffix)
                    sort_yaml_file(input_file_path, output_file_path)
                    print(f"{input_file_path} changed.")
                    files_changed += 1
    elif os.path.isfile(args.input):
        sort_yaml_file(args.input, args.output)
        files_changed = 1
    else:
        print(f"Error: {args.input} is not a valid file or directory.")

    print(f"Number of files changed: {files_changed}")
