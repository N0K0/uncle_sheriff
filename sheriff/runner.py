from sheriff import api


r1 = api.blocks(limit=10000)
r2 = api.blocks(limit=10000, before=12317065)

print()
