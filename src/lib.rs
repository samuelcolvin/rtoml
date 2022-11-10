use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::{create_exception, wrap_pyfunction};
use serde::de::DeserializeSeed;

use toml::{to_string as to_toml_string, to_string_pretty as to_toml_string_pretty, Deserializer};

use crate::ser::SerializePyObject;

#[cfg(not(target_env = "musl"))]
#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

mod datetime;
mod de;
mod py_type;
mod ser;

const VERSION: &str = env!("CARGO_PKG_VERSION");
create_exception!(_rtoml, TomlParsingError, PyValueError);
create_exception!(_rtoml, TomlSerializationError, PyValueError);

#[pyfunction]
fn deserialize(py: Python, toml_data: String) -> PyResult<PyObject> {
    let mut deserializer = Deserializer::new(&toml_data);
    let seed = de::PyDeserializer::new(py);
    seed.deserialize(&mut deserializer)
        .map_err(|e| TomlParsingError::new_err(e.to_string()))
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
