# rtoml benchmarks

Versus
[bobfang1992/pytomlpp](https://github.com/bobfang1992/pytomlpp),
[hukkinj1/tomli](https://github.com/hukkinj1/tomli),
[uiri/toml](https://github.com/uiri/toml),
and
[sdispater/tomlkit](https://github.com/sdispater/tomlkit).

Time taken to load [`data.toml`](https://github.com/samuelcolvin/rtoml/blob/main/benchmarks/data.toml):
```
rtoml     version: 0.6.1    0.272 ms/parse
pytomlpp  version: 2.4.0    0.249 ms/parse (1.09 X faster)
tomli     version: 0.2.7    1.799 ms/parse (6.62 X slower)
uiri/toml version: 0.10.2   2.675 ms/parse (9.84 X slower)
tomlkit   version: 0.7.2    15.726 ms/parse (57.88 X slower)
```

See [`run.py`](https://github.com/samuelcolvin/rtoml/blob/main/benchmarks/run.py) for details on how
the benchmarks are run.
