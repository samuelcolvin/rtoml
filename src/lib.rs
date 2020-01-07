extern crate pyo3;

use pyo3::prelude::*;
use pyo3::{wrap_pyfunction, import_exception};
use pyo3::types::PyDict;
use toml::Value;
use toml::Value::{String, Integer, Float, Boolean, Datetime, Array, Table};

import_exception!(utils, TomlError);

fn convert_value(t: &Value, py: Python, parse_datetime: &PyObject) -> PyResult<PyObject> {
    match t {
        Table(table) => {
            let d = PyDict::new(py);
            for (key, value) in table.iter() {
                d.set_item(key.to_string(), convert_value(value, py, parse_datetime)?)?;
            }
            Ok(d.to_object(py))
        },

        Array(array) => {
            let mut list: Vec<PyObject> = Vec::with_capacity(array.len());
            for (i, value) in array.iter().enumerate() {
                list[i] = convert_value(value, py, parse_datetime)?;
            }
            Ok(list.to_object(py))
        },
        String(v) => Ok(v.to_object(py)),
        Integer(v) => Ok(v.to_object(py)),
        Float(v) => Ok(v.to_object(py)),
        Boolean(v) => Ok(v.to_object(py)),
        Datetime(v) => parse_datetime.call1(py, (v.to_string(),)),
    }
}

#[pyfunction]
fn parse(py: Python, toml: std::string::String, parse_datetime: PyObject) -> PyResult<PyObject> {
    match toml.parse::<Value>() {
        Ok(v) => convert_value(&v, py, &parse_datetime),
        Err(e) => Err(TomlError::py_err(e.to_string()))
    }
}

#[pymodule]
fn rtoml(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(parse))?;
    Ok(())
}
