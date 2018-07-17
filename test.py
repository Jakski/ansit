import shlex
import subprocess
from pprint import pformat


def main():
    cmd = '/home/jakub/dev/ansit/test.sh'
    process = subprocess.Popen(
        shlex.split(cmd),
        bufsize=1,
        universal_newlines=True,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE)
    output = []
    for line in process.stdout:
        output.append(line)
    print(pformat(output))


if __name__ == '__main__':
    main()
