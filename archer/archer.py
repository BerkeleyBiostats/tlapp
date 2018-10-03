from fabric import Connection

def validate_config(config):
	assert 'host' in config

def run(config):
	validate_config(config)

	conn = Connection(config['host'])

	result = conn.run("echo 'hello docker'")
	print(result)
	print(result.command)
	print(result.stdout)
	print(result.stderr)