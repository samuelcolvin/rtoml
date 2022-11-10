use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::{create_exception, wrap_pyfunction, PyErrArguments};

use toml::Value::{Array, Boolean, Datetime, Float, Integer, String as TomlString, Table};
use toml::{to_string as to_toml_string, to_string_pretty as to_toml_string_pretty, Value};

use crate::ser::SerializePyObject;

#[cfg(not(target_env = "musl"))]
#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

mod datetime;
mod py_type;
mod ser;

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
