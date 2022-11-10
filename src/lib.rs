extern crate pyo3;

use crate::py_type::PyTypeLookup;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDate, PyDateTime, PyDict, PyList, PyString, PyTime, PyTuple};
use pyo3::{create_exception, wrap_pyfunction, PyErrArguments};
use serde::ser::{Error as SerError, Serialize, SerializeMap, SerializeSeq, Serializer};
use std::fmt;
use std::str::FromStr;
use toml::Value::{Array, Boolean, Datetime, Float, Integer, String as TomlString, Table};
use toml::{to_string as to_toml_string, to_string_pretty as to_toml_string_pretty, Value};

#[cfg(not(target_env = "musl"))]
#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

mod datetime;
mod py_type;

const VERSION: &str = env!("CARGO_PKG_VERSION");
create_exception!(_rtoml, TomlParsingError, PyValueError);
create_exception!(_rtoml, TomlSerializationError, PyValueError);

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
        Datetime(v) => datetime::parse(py, v),
    }
}

#[pyfunction]
fn deserialize(py: Python, toml: String) -> PyResult<PyObject> {
    match toml.parse::<Value>() {
        Ok(v) => convert_value(&v, py).map_err(|e| TomlParsingError::new_err(e.arguments(py))),
        Err(e) => Err(TomlParsingError::new_err(e.to_string())),
    }
}

struct SerializePyObject<'py> {
    obj: &'py PyAny,
    py: Python<'py>,
    ob_type_lookup: &'py PyTypeLookup,
}

impl<'py> SerializePyObject<'py> {
    fn new(py: Python<'py>, obj: &'py PyAny) -> Self {
        Self {
            obj,
            py,
            ob_type_lookup: PyTypeLookup::cached(py),
        }
    }

    fn with_obj(&self, obj: &'py PyAny) -> Self {
        Self {
            obj,
            py: self.py,
            ob_type_lookup: self.ob_type_lookup,
        }
    }
}

macro_rules! serde_err {
    ($msg:expr, $( $msg_args:expr ),+ ) => {
        Err(SerError::custom(format!($msg, $( $msg_args ),+ )))
    };
}

impl<'py> Serialize for SerializePyObject<'py> {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        macro_rules! serialize {
            ($t:ty) => {
                match self.obj.extract::<$t>() {
                    Ok(v) => v.serialize(serializer),
                    Err(e) => Err(map_py_err(e)),
                }
            };
        }

        let lookup = self.ob_type_lookup;
        let ob_type = self.obj.get_type_ptr() as usize;
        // ugly but this seems to be just marginally faster than a guarded match, also allows for custom cases
        // if we wanted to add them
        if ob_type == lookup.none {
            serializer.serialize_str("null")
        } else if ob_type == lookup.int {
            serialize!(i64)
        } else if ob_type == lookup.bool {
            serialize!(bool)
        } else if ob_type == lookup.float {
            serialize!(f64)
        } else if ob_type == lookup.string {
            serialize!(&str)
        } else if ob_type == lookup.bytes || ob_type == lookup.bytearray {
            serialize!(&[u8])
        } else if ob_type == lookup.dict {
            let py_dict: &PyDict = self.obj.cast_as().map_err(map_py_err)?;

            let len = py_dict.len();
            let mut simple_items: Vec<(&PyAny, &PyAny)> = Vec::with_capacity(len);
            let mut array_items: Vec<(&PyAny, &PyAny)> = Vec::with_capacity(len);
            let mut dict_items: Vec<(&PyAny, &PyAny)> = Vec::with_capacity(len);

            for (k, v) in py_dict {
                if v.cast_as::<PyDict>().is_ok() {
                    dict_items.push((k, v));
                } else if v.cast_as::<PyList>().is_ok() || v.cast_as::<PyTuple>().is_ok() {
                    array_items.push((k, v));
                } else {
                    simple_items.push((k, v));
                }
            }
            let mut map = serializer.serialize_map(Some(len))?;
            for (k, v) in simple_items {
                let key = table_key(k)?;
                let value = self.with_obj(v);
                map.serialize_entry(key, &value)?;
            }
            for (k, v) in array_items {
                let key = table_key(k)?;
                let value = self.with_obj(v);
                map.serialize_entry(key, &value)?;
            }
            for (k, v) in dict_items {
                let key = table_key(k)?;
                let value = self.with_obj(v);
                map.serialize_entry(key, &value)?;
            }
            map.end()
        } else if ob_type == lookup.list {
            let py_list: &PyList = self.obj.cast_as().map_err(map_py_err)?;
            let mut seq = serializer.serialize_seq(Some(py_list.len()))?;
            for element in py_list {
                seq.serialize_element(&self.with_obj(element))?
            }
            seq.end()
        } else if ob_type == lookup.tuple {
            let py_tuple: &PyTuple = self.obj.cast_as().map_err(map_py_err)?;
            let mut seq = serializer.serialize_seq(Some(py_tuple.len()))?;
            for element in py_tuple {
                seq.serialize_element(&self.with_obj(element))?
            }
            seq.end()
        } else if ob_type == lookup.datetime {
            let py_dt: &PyDateTime = self.obj.cast_as().map_err(map_py_err)?;
            let dt_str = py_dt.str().map_err(map_py_err)?.to_str().map_err(map_py_err)?;
            let iso_str = dt_str.replacen("+00:00", "Z", 1);
            match toml::value::Datetime::from_str(&iso_str) {
                Ok(dt) => dt.serialize(serializer),
                Err(e) => serde_err!("unable to convert datetime string to TOML datetime object {:?}", e),
            }
        } else if ob_type == lookup.date {
            let py_date: &PyDate = self.obj.cast_as().map_err(map_py_err)?;
            let date_str = py_date.str().map_err(map_py_err)?.to_str().map_err(map_py_err)?;
            match toml::value::Datetime::from_str(date_str) {
                Ok(dt) => dt.serialize(serializer),
                Err(e) => serde_err!("unable to convert date string to TOML date object {:?}", e),
            }
        } else if ob_type == lookup.time {
            let py_time: &PyTime = self.obj.cast_as().map_err(map_py_err)?;
            let time_str = py_time.str().map_err(map_py_err)?.to_str().map_err(map_py_err)?;
            match toml::value::Datetime::from_str(time_str) {
                Ok(dt) => dt.serialize(serializer),
                Err(e) => serde_err!("unable to convert time string to TOML time object {:?}", e),
            }
        } else {
            serde_err!("{} is not serializable to TOML", any_repr(self.obj))
        }
    }
}

fn map_py_err<I: fmt::Display, O: SerError>(err: I) -> O {
    O::custom(err.to_string())
}

fn table_key<E: SerError>(key: &PyAny) -> Result<&str, E> {
    if let Ok(py_string) = key.cast_as::<PyString>() {
        py_string.to_str().map_err(map_py_err)
    } else if key.is_none() {
        Ok("null")
    } else if let Ok(key) = key.extract::<bool>() {
        Ok(if key { "true" } else { "false" })
    } else {
        let key_repr = any_repr(key);
        serde_err!("{} is not serializable as a TOML key", key_repr)
    }
}

fn any_repr(obj: &PyAny) -> String {
    let name = obj.get_type().name().unwrap_or("unknown");
    match obj.repr() {
        Ok(repr) => format!("{repr} ({name})"),
        Err(_) => name.to_string(),
    }
}

#[pyfunction]
fn serialize(py: Python, obj: &PyAny) -> PyResult<String> {
    let s = SerializePyObject::new(py, obj);
    match to_toml_string(&s) {
        Ok(s) => Ok(s),
        Err(e) => Err(TomlSerializationError::new_err(e.to_string())),
    }
}

#[pyfunction]
fn serialize_pretty(py: Python, obj: &PyAny) -> PyResult<String> {
    let s = SerializePyObject::new(py, obj);
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
