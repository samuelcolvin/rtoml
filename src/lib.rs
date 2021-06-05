extern crate pyo3;

use chrono::{DateTime as ChronoDatetime, Datelike, ParseError, Timelike};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDateTime, PyDelta, PyDict, PyFloat, PyList, PyTuple, PyTzInfo};
use pyo3::{create_exception, wrap_pyfunction};
use serde::ser::{self, Serialize, SerializeMap, SerializeSeq, Serializer};
use std::str::FromStr;
use toml::Value::{Array, Boolean, Datetime, Float, Integer, String as TomlString, Table};
use toml::{to_string as to_toml_string, to_string_pretty as to_toml_string_pretty, Value};

const VERSION: &str = env!("CARGO_PKG_VERSION");
create_exception!(_rtoml, TomlParsingError, PyValueError);
create_exception!(_rtoml, TomlSerializationError, PyValueError);

fn chrono_py_err(e: ParseError) -> PyErr {
    let s = format!("invalid toml date: {}", e.to_string());
    PyErr::new::<PyValueError, _>(PyValueError::new_err(s))
}

#[pyclass(extends=PyTzInfo)]
struct TzClass {
    seconds: i32,
}

#[pymethods]
impl TzClass {
    #[new]
    fn new(seconds: i32) -> Self {
        TzClass { seconds }
    }

    fn utcoffset<'p>(&self, py: Python<'p>, _dt: &PyDateTime) -> PyResult<&'p PyDelta> {
        PyDelta::new(py, 0, self.seconds, 0, true)
    }

    fn tzname(&self, _py: Python<'_>, _dt: &PyDateTime) -> String {
        String::from("+01:00") // TODO
    }

    fn dst(&self, _py: Python<'_>, _dt: &PyDateTime) -> Option<&PyDelta> {
        None
    }
}

fn convert_value(t: &Value, py: Python) -> PyResult<PyObject> {
    match t {
        Table(table) => {
            let d = PyDict::new(py);
            for (key, value) in table.iter() {
                d.set_item(key.to_string(), convert_value(value, py)?)?;
            }
            Ok(d.to_object(py))
        }

        Array(array) => {
            let mut list: Vec<PyObject> = Vec::with_capacity(array.len());
            for value in array {
                list.push(convert_value(value, py)?)
            }
            Ok(list.to_object(py))
        }
        TomlString(v) => Ok(v.to_object(py)),
        Integer(v) => Ok(v.to_object(py)),
        Float(v) => Ok(v.to_object(py)),
        Boolean(v) => Ok(v.to_object(py)),
        // Datetime(v) => Ok(v.to_string().to_object(py)),
        Datetime(v) => {
            let mut date_string = v.to_string();
            // println!("date_string: {:?}", date_string);
            let date_ending = &date_string[date_string.len() - 3..];
            let tz_naive = date_ending.chars().nth(0) != Some(':') && date_ending.chars().nth(2) != Some('Z');
            if tz_naive{
                date_string.push('Z');
            }

            let dt = ChronoDatetime::parse_from_rfc3339(&date_string).map_err(chrono_py_err)?;
            let date = dt.date();
            let time = dt.time();
            let offset_seconds = dt.offset().local_minus_utc();
            let tz_info = TzClass::new(offset_seconds);

            // let tz_info: Option<&PyObject>;
            // let tz_pyobject: PyObject;
            // if tz_naive {
            //     tz_info = None;
            // } else {
            //     let locals = PyDict::new(py);
            //     locals.set_item("datetime", py.import("datetime")?)?;
            //     locals.set_item("seconds", offset_seconds.to_object(py))?;
            //     let code = "datetime.timezone(datetime.timedelta(seconds=seconds))";
            //     tz_pyobject = py.eval(code, None, Some(&locals))?.into_py(py);
            //     tz_info = Some(&tz_pyobject);
            // }

            let dt = PyDateTime::new(
                py,
                date.year(),
                date.month() as u8,
                date.day() as u8,
                time.hour() as u8,
                time.minute() as u8,
                time.second() as u8,
                time.nanosecond() / 1000 as u32,
                Some(&Py::new(py, tz_info)?.to_object(py)),
            )?;
            Ok(dt.to_object(py))
        }
    }
}

#[pyfunction]
fn deserialize(py: Python, toml: String) -> PyResult<PyObject> {
    match toml.parse::<Value>() {
        Ok(v) => convert_value(&v, py),
        Err(e) => Err(TomlParsingError::new_err(e.to_string())),
    }
}

// taken from https://github.com/mre/hyperjson/blob/10d31608584ef4499d6b6b10b6dc9455b358fe3d/src/lib.rs#L287-L402
struct SerializePyObject<'p, 'a> {
    py: Python<'p>,
    obj: &'a PyAny,
}

impl<'p, 'a> Serialize for SerializePyObject<'p, 'a> {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        macro_rules! cast {
            ($f:expr) => {
                if let Ok(val) = PyTryFrom::try_from(self.obj) {
                    return $f(val);
                }
            };
        }

        macro_rules! extract {
            ($t:ty) => {
                if let Ok(val) = <$t as FromPyObject>::extract(self.obj) {
                    return val.serialize(serializer);
                }
            };
        }

        macro_rules! isa {
            ($v:ident, $t:ty) => {
                $v.is_instance::<$t>().map_err(debug_py_err)?
            };
        }

        macro_rules! add_to_map {
            ($map:ident, $key:ident, $value:ident) => {
                if $key.is_none() {
                    $map.serialize_key("null")?;
                } else if let Ok(key) = $key.extract::<bool>() {
                    $map.serialize_key(if key { "true" } else { "false" })?;
                } else if let Ok(key) = $key.str() {
                    let key = key.to_string();
                    $map.serialize_key(&key)?;
                } else {
                    return Err(ser::Error::custom(format_args!(
                        "Dictionary key is not a string: {:?}",
                        $key
                    )));
                }
                $map.serialize_value(&SerializePyObject {
                    py: self.py,
                    obj: $value,
                })?;
            };
        }

        fn debug_py_err<E: ser::Error>(err: PyErr) -> E {
            E::custom(format_args!("{:?}", err))
        }

        cast!(|x: &PyDict| {
            let mut map = serializer.serialize_map(Some(x.len()))?;

            // https://github.com/alexcrichton/toml-rs/issues/142#issuecomment-278970591
            // taken from alexcrichton/toml-rs/blob/ec4e821f3bb081391801e4c00aa90bf66a53562c/src/value.rs#L364-L387
            for (k, v) in x {
                if !isa!(v, PyList) && !isa!(v, PyTuple) && !isa!(v, PyDict) {
                    add_to_map!(map, k, v);
                }
            }
            for (k, v) in x {
                if isa!(v, PyList) || isa!(v, PyTuple) {
                    add_to_map!(map, k, v);
                }
            }
            for (k, v) in x {
                if isa!(v, PyDict) {
                    add_to_map!(map, k, v);
                }
            }
            map.end()
        });

        macro_rules! to_seq {
            ($type:ty) => {
                cast!(|x: $type| {
                    let mut seq = serializer.serialize_seq(Some(x.len()))?;
                    for element in x {
                        seq.serialize_element(&SerializePyObject {
                            py: self.py,
                            obj: element,
                        })?
                    }
                    return seq.end();
                });
            };
        }

        to_seq!(&PyList);
        to_seq!(&PyTuple);

        cast!(|x: &PyDateTime| {
            let dt_str: &str = x.str().map_err(debug_py_err)?.extract().map_err(debug_py_err)?;
            let iso_str = dt_str.replacen("+00:00", "Z", 1);
            match toml::value::Datetime::from_str(&iso_str) {
                Ok(dt) => dt.serialize(serializer),
                Err(e) => Err(ser::Error::custom(format_args!(
                    "unable to convert datetime string to toml datetime object {:?}",
                    e
                ))),
            }
        });

        extract!(String);
        extract!(bool);

        cast!(|x: &PyFloat| x.value().serialize(serializer));
        extract!(u64);
        extract!(i64);

        if self.obj.is_none() {
            return serializer.serialize_str("null");
        }

        let name = self.obj.get_type().name().map_err(debug_py_err)?;
        match self.obj.repr() {
            Ok(repr) => Err(ser::Error::custom(format_args!(
                "{} is not serializable to TOML: {}",
                name, repr,
            ))),
            Err(_) => Err(ser::Error::custom(format_args!("{} is not serializable to TOML", name))),
        }
    }
}

#[pyfunction]
fn serialize(py: Python, obj: PyObject) -> PyResult<String> {
    let s = SerializePyObject {
        py,
        obj: obj.extract(py)?,
    };
    match to_toml_string(&s) {
        Ok(s) => Ok(s),
        Err(e) => Err(TomlSerializationError::new_err(e.to_string())),
    }
}

#[pyfunction]
fn serialize_pretty(py: Python, obj: PyObject) -> PyResult<String> {
    let s = SerializePyObject {
        py,
        obj: obj.extract(py)?,
    };
    match to_toml_string_pretty(&s) {
        Ok(s) => Ok(s),
        Err(e) => Err(TomlSerializationError::new_err(e.to_string())),
    }
}

#[pymodule]
fn _rtoml(py: Python, m: &PyModule) -> PyResult<()> {
    m.add("TomlParsingError", py.get_type::<TomlParsingError>())?;
    m.add("TomlSerializationError", py.get_type::<TomlSerializationError>())?;
    m.add("VERSION", VERSION)?;
    m.add_wrapped(wrap_pyfunction!(deserialize))?;
    m.add_wrapped(wrap_pyfunction!(serialize))?;
    m.add_wrapped(wrap_pyfunction!(serialize_pretty))?;
    Ok(())
}
