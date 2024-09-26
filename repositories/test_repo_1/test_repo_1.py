from dagster import job, op

@op
def add_numbers():
    return 1 + 2

@job
def addition_job():
    add_numbers()
