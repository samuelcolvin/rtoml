use std::fmt;
use std::str::FromStr;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use pyo3::IntoPyObjectExt;

use serde::de::{self, DeserializeSeed, Deserializer, MapAccess, SeqAccess, Visitor};
use toml::value::Datetime as TomlDatetime;

use crate::datetime;

pub const DATETIME_MAPPING_KEY: &str = "$__toml_private_datetime";

pub struct PyDeserializer<'py> {
    py: Python<'py>,
    none_value: Option<&'py str>,
}

impl<'py> PyDeserializer<'py> {
    pub fn new(py: Python<'py>, none_value: Option<&'py str>) -> Self {
        Self { py, none_value }
    }
}

impl<'de> DeserializeSeed<'de> for PyDeserializer<'_> {
    type Value = Py<PyAny>;

    fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
    where
        D: Deserializer<'de>,
    {
        deserializer.deserialize_any(self)
    }
}

impl<'de> Visitor<'de> for PyDeserializer<'_> {
    type Value = Py<PyAny>;

    fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
        formatter.write_str("any valid TOML value")
    }

    fn visit_bool<E>(self, value: bool) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        value.into_py_any(self.py).map_err(de::Error::custom)
    }

    fn visit_i64<E>(self, value: i64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        value.into_py_any(self.py).map_err(de::Error::custom)
    }

    fn visit_u64<E>(self, value: u64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        value.into_py_any(self.py).map_err(de::Error::custom)
    }

    fn visit_i128<E>(self, value: i128) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        value.into_py_any(self.py).map_err(de::Error::custom)
    }

    fn visit_u128<E>(self, value: u128) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        value.into_py_any(self.py).map_err(de::Error::custom)
    }

    fn visit_f64<E>(self, value: f64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        value.into_py_any(self.py).map_err(de::Error::custom)
    }

    fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        match self.none_value {
            Some(none_value) if value == none_value => Ok(self.py.None()),
            _ => value.into_py_any(self.py).map_err(de::Error::custom),
        }
    }

    fn visit_unit<E>(self) -> Result<Self::Value, E> {
        Ok(self.py.None())
    }

    fn visit_seq<A>(self, mut seq: A) -> Result<Self::Value, A::Error>
    where
        A: SeqAccess<'de>,
    {
        let mut elements = Vec::new();

        while let Some(elem) = seq.next_element_seed(PyDeserializer::new(self.py, self.none_value))? {
            elements.push(elem);
        }

        elements.into_py_any(self.py).map_err(de::Error::custom)
    }

    fn visit_map<A>(self, mut map_access: A) -> Result<Self::Value, A::Error>
    where
        A: MapAccess<'de>,
    {
        let value_seed = || PyDeserializer::new(self.py, self.none_value);
        match map_access.next_entry_seed(PyKeySeed(self.py), value_seed())? {
            Some((first_key, first_value)) if first_key.to_cow().ok().as_deref() == Some(DATETIME_MAPPING_KEY) => {
                let py_string = first_value.extract::<&str>(self.py).map_err(de::Error::custom)?;
                let dt: TomlDatetime = TomlDatetime::from_str(py_string).map_err(de::Error::custom)?;
                Ok(datetime::parse(self.py, &dt).map_err(de::Error::custom)?)
            }
            Some((first_key, first_value)) => {
                let dict = PyDict::new(self.py);
                dict.set_item(first_key, first_value).map_err(de::Error::custom)?;

                while let Some((key, value)) = map_access.next_entry_seed(PyKeySeed(self.py), value_seed())? {
                    // toml-rs doesn't check for duplicate keys on this code path, so we have to;
                    // if the dict didn't grow, the key was already there
                    let len = dict.len();
                    dict.set_item(&key, value).map_err(de::Error::custom)?;
                    if dict.len() == len {
                        return Err(de::Error::custom(format!("duplicate key: `{key}`")));
                    }
                }

                dict.into_py_any(self.py).map_err(de::Error::custom)
            }
            None => PyDict::new(self.py).into_py_any(self.py).map_err(de::Error::custom),
        }
    }
}

/// Deserializes a map key straight into a Python string, avoiding an intermediate Rust `String`.
struct PyKeySeed<'py>(Python<'py>);

impl<'de, 'py> DeserializeSeed<'de> for PyKeySeed<'py> {
    type Value = Bound<'py, PyString>;

    fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
    where
        D: Deserializer<'de>,
    {
        deserializer.deserialize_str(self)
    }
}

impl<'de, 'py> Visitor<'de> for PyKeySeed<'py> {
    type Value = Bound<'py, PyString>;

    fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
        formatter.write_str("a string key")
    }

    fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Ok(PyString::new(self.0, value))
    }
}
