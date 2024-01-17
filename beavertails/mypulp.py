from tempfile import NamedTemporaryFile

from pulp.apis import PULP_CBC_CMD


def solve(prob):
    with NamedTemporaryFile(delete_on_close=False) as log_file:
        status = prob.solve(PULP_CBC_CMD(msg=False, logPath=log_file.name))
        log_file.seek(0)
        log = log_file.read().decode("utf-8")
    return status, log
