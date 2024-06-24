use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::{create_exception, wrap_pyfunction};

use serde::de::DeserializeSeed;
use toml::{to_string as to_toml_string, to_string_pretty as to_toml_string_pretty, Deserializer};

use crate::ser::SerializePyObject;

mod datetime;
mod de;
mod py_type;
mod ser;

create_exception!(_rtoml, TomlParsingError, PyValueError);
create_exception!(_rtoml, TomlSerializationError, PyValueError);

#[pyfunction]
fn deserialize(py: Python, toml_data: String, none_value: Option<&str>) -> PyResult<PyObject> {
    let mut deserializer = Deserializer::new(&toml_data);
    let seed = de::PyDeserializer::new(py, none_value);
    seed.deserialize(&mut deserializer)
        .map_err(|e| TomlParsingError::new_err(e.to_string()))
}

#[pyfunction]
fn serialize(py: Python, obj: Bound<'_, PyAny>, none_value: Option<&str>) -> PyResult<String> {
    let s = SerializePyObject::new(py, obj, none_value);
    match to_toml_string(&s) {
        Ok(s) => Ok(s),
        Err(e) => Err(TomlSerializationError::new_err(e.to_string())),
    }
}

#[pyfunction]
fn serialize_pretty(py: Python, obj: Bound<'_, PyAny>, none_value: Option<&str>) -> PyResult<String> {
    let s = SerializePyObject::new(py, obj, none_value);
    match to_toml_string_pretty(&s) {
        Ok(s) => Ok(s),
        Err(e) => Err(TomlSerializationError::new_err(e.to_string())),
    }
}

pub fn get_version() -> String {
    let version = env!("CARGO_PKG_VERSION").to_string();
    // cargo uses "1.0-alpha1" etc. while python uses "1.0.0a1", this is not full compatibility,
    // but it's good enough for now
    // see https://docs.rs/semver/1.0.9/semver/struct.Version.html#method.parse for rust spec
    // see https://peps.python.org/pep-0440/ for python spec
    // it seems the dot after "alpha/beta" e.g. "-alpha.1" is not necessary, hence why this works
    version.replace("-alpha", "a").replace("-beta", "b")
}

#[pymodule]
fn _rtoml(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("TomlParsingError", py.get_type_bound::<TomlParsingError>())?;
    m.add("TomlSerializationError", py.get_type_bound::<TomlSerializationError>())?;
    let version = get_version();
    m.add("__version__", version.clone())?;
    // keep VERSION for compatibility
    m.add("VERSION", version)?;
    m.add_wrapped(wrap_pyfunction!(deserialize))?;
    m.add_wrapped(wrap_pyfunction!(serialize))?;
    m.add_wrapped(wrap_pyfunction!(serialize_pretty))?;
    Ok(())
}
