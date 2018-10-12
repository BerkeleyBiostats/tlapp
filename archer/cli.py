import getpass
import archer

if __name__ == "__main__":
	print("hello docker")

	from fabric import Connection

	password = getpass.getpass("Enter password for root@cluster: ")

	conn = Connection("root@cluster", connect_kwargs={"password": password})
	result = conn.run("echo 'hello docker docker'")
	print(result)
	print(result.command)
	print(result.stdout)
	print(result.stderr)
