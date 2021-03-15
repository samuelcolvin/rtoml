# rtoml benchmarks

Versus [uiri/toml](https://github.com/uiri/toml) and [sdispater/tomlkit](https://github.com/sdispater/tomlkit).

Time taken to load [`data.toml`](https://github.com/samuelcolvin/rtoml/blob/main/benchmarks/data.toml):
```
rtoml     version: 0.2.0    0.221 ms/parse
uiri/toml version: 0.10.0   1.977 ms/parse (8.96 X slower)
tomlkit   version: 0.5.8    13.950 ms/parse (63.23 X slower)
```

See [`run.py`](https://github.com/samuelcolvin/rtoml/blob/main/benchmarks/run.py) for details on how
the benchmarks are run.
