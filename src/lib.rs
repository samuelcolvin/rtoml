use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::{create_exception, wrap_pyfunction};

use serde::de::DeserializeSeed;
use serde::Serialize;
use toml::{to_string as to_toml_string, to_string_pretty as to_toml_string_pretty, Deserializer};

use crate::py_type::PyTypeLookup;
use crate::ser::SerializePyObject;

mod datetime;
mod de;
mod py_type;
mod ser;

create_exception!(_rtoml, TomlParsingError, PyValueError);
create_exception!(_rtoml, TomlSerializationError, PyValueError);

#[pyfunction]
#[pyo3(signature = (toml_data, none_value=None))]
fn deserialize(py: Python, toml_data: &str, none_value: Option<&str>) -> PyResult<Py<PyAny>> {
    let deserializer = Deserializer::parse(toml_data).map_err(|e| parsing_error(e, toml_data))?;
    let seed = de::PyDeserializer::new(py, none_value);
    seed.deserialize(deserializer).map_err(|e| parsing_error(e, toml_data))
}

/// Build a `TomlParsingError` as `"<message> at line <l> column <c>"`, the toml crate's own `Display`
/// is a multi-line snippet which is too noisy for an exception message.
fn parsing_error(e: toml::de::Error, toml_data: &str) -> PyErr {
    let msg = match e.span() {
        Some(span) => {
            let before = &toml_data[..span.start.min(toml_data.len())];
            let line = before.matches('\n').count() + 1;
            let column = before.rsplit('\n').next().unwrap_or("").chars().count() + 1;
            format!("{} at line {line} column {column}", e.message())
        }
        None => e.message().to_string(),
    };
    TomlParsingError::new_err(msg)
}

/// Serialize `obj`, a top-level dict becomes a TOML document, anything else is written as a bare TOML value.
fn serialize_any(py: Python, obj: Bound<'_, PyAny>, none_value: Option<&str>, pretty: bool) -> PyResult<String> {
    let is_dict = obj.get_type_ptr() as usize == PyTypeLookup::cached(py).dict;
    let s = SerializePyObject::new(py, obj, none_value);
    let result = if !is_dict {
        let mut output = String::new();
        // the Ok value borrows `output`, drop it before handing `output` back
        let result = s.serialize(toml::ser::ValueSerializer::new(&mut output)).map(|_| ());
        result.map(|()| output)
    } else if pretty {
        to_toml_string_pretty(&s)
    } else {
        to_toml_string(&s)
    };
    result.map_err(|e| TomlSerializationError::new_err(e.to_string()))
}

#[pyfunction]
#[pyo3(signature = (obj, none_value=None))]
fn serialize(py: Python, obj: Bound<'_, PyAny>, none_value: Option<&str>) -> PyResult<String> {
    serialize_any(py, obj, none_value, false)
}

#[pyfunction]
#[pyo3(signature = (obj, none_value=None))]
fn serialize_pretty(py: Python, obj: Bound<'_, PyAny>, none_value: Option<&str>) -> PyResult<String> {
    serialize_any(py, obj, none_value, true)
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
    m.add("TomlParsingError", py.get_type::<TomlParsingError>())?;
    m.add("TomlSerializationError", py.get_type::<TomlSerializationError>())?;
    let version = get_version();
    m.add("__version__", version.clone())?;
    // keep VERSION for compatibility
    m.add("VERSION", version)?;
    m.add_wrapped(wrap_pyfunction!(deserialize))?;
    m.add_wrapped(wrap_pyfunction!(serialize))?;
    m.add_wrapped(wrap_pyfunction!(serialize_pretty))?;
    Ok(())
}
