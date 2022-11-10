use std::fmt;
use std::marker::PhantomData;
use std::str::FromStr;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use ahash::AHashSet;
use serde::de::{self, DeserializeSeed, Deserializer, MapAccess, SeqAccess, Visitor};
use toml::value::Datetime as TomlDatetime;

use crate::datetime;

pub const DATETIME_MAPPING_KEY: &str = "$__toml_private_datetime";

pub struct PyDeserializer<'py> {
    py: Python<'py>,
}

impl<'py> PyDeserializer<'py> {
    pub fn new(py: Python<'py>) -> Self {
        Self { py }
    }
}

impl<'de, 'py> DeserializeSeed<'de> for PyDeserializer<'py> {
    type Value = PyObject;

    fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
    where
        D: Deserializer<'de>,
    {
        deserializer.deserialize_any(self)
    }
}

impl<'de, 'py> Visitor<'de> for PyDeserializer<'py> {
    type Value = PyObject;

    fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
        formatter.write_str("any valid JSON value")
    }

    fn visit_bool<E>(self, value: bool) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Ok(value.to_object(self.py))
    }

    fn visit_i64<E>(self, value: i64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Ok(value.to_object(self.py))
    }

    fn visit_u64<E>(self, value: u64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Ok(value.to_object(self.py))
    }

    fn visit_f64<E>(self, value: f64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Ok(value.to_object(self.py))
    }

    fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Ok(value.to_object(self.py))
    }

    fn visit_unit<E>(self) -> Result<Self::Value, E> {
        Ok(self.py.None())
    }

    fn visit_seq<A>(self, mut seq: A) -> Result<Self::Value, A::Error>
    where
        A: SeqAccess<'de>,
    {
        let mut elements = Vec::new();

        while let Some(elem) = seq.next_element_seed(PyDeserializer::new(self.py))? {
            elements.push(elem);
        }

        Ok(elements.to_object(self.py))
    }

    fn visit_map<A>(self, mut map_access: A) -> Result<Self::Value, A::Error>
    where
        A: MapAccess<'de>,
    {
        match map_access.next_entry_seed(PhantomData::<String>, PyDeserializer::new(self.py))? {
            Some((first_key, first_value)) if first_key == DATETIME_MAPPING_KEY => {
                let py_string = first_value.extract::<&str>(self.py).map_err(de::Error::custom)?;
                let dt: TomlDatetime = TomlDatetime::from_str(py_string).map_err(de::Error::custom)?;
                Ok(datetime::parse(self.py, &dt).map_err(de::Error::custom)?)
            }
            Some((first_key, first_value)) => {
                let dict = PyDict::new(self.py);
                let mut keys: AHashSet<String> = AHashSet::new();
                keys.insert(first_key.clone());
                dict.set_item(first_key, first_value).map_err(de::Error::custom)?;

                while let Some((key, value)) =
                    map_access.next_entry_seed(PhantomData::<String>, PyDeserializer::new(self.py))?
                {
                    if keys.insert(key.clone()) {
                        dict.set_item(key, value).map_err(de::Error::custom)?;
                    } else {
                        return Err(de::Error::custom(format!("duplicate key: `{key}`")));
                    }
                }

                Ok(dict.to_object(self.py))
            }
            None => Ok(PyDict::new(self.py).to_object(self.py)),
        }
    }
}
