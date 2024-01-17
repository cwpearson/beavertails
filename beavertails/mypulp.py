from tempfile import NamedTemporaryFile

from pulp.apis import PULP_CBC_CMD


def solve(prob):
    with NamedTemporaryFile() as log_file:
        status = prob.solve(PULP_CBC_CMD(msg=False, logPath=log_file.name))
        with open(log_file.name, "r") as f:
            log = f.read()
    return status, log
