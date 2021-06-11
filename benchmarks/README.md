# rtoml benchmarks

Versus
[bobfang1992/pytomlpp](https://github.com/bobfang1992/pytomlpp),
[hukkinj1/tomli](https://github.com/hukkinj1/tomli),
[uiri/toml](https://github.com/uiri/toml),
and
[sdispater/tomlkit](https://github.com/sdispater/tomlkit).

Time taken to load [`data.toml`](https://github.com/samuelcolvin/rtoml/blob/main/benchmarks/data.toml):
```
rtoml     version: 0.7.0    0.176 ms/parse
pytomlpp  version: 2.4.0    0.194 ms/parse (1.11 X slower)
tomli     version: 0.2.9    1.244 ms/parse (7.08 X slower)
uiri/toml version: 0.10.2   2.045 ms/parse (11.64 X slower)
tomlkit   version: 0.7.2    12.203 ms/parse (69.46 X slower)
```

Run with Python: `3.9.5`, OS: `Ubuntu 21.04`, CPU: `Intel(R) Core(TM) i7-8700K CPU @ 3.70GHz`.

See [`run.py`](https://github.com/samuelcolvin/rtoml/blob/main/benchmarks/run.py) for details on how
the benchmarks are run.
