from max import MaxClient

cli = MaxClient()

cli.auth(input("Number: "))
print(cli.auth_token)