from dagster import job, op

@op
def multiply_numbers():
    return 3 * 4

@job
def multiplication_job():
    multiply_numbers()

