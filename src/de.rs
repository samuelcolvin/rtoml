use std::collections::HashSet;
use std::fmt;
use std::hash::BuildHasherDefault;
use std::marker::PhantomData;
use std::str::FromStr;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use ahash::RandomState;
use nohash_hasher::NoHashHasher;
use serde::de::{self, DeserializeSeed, Deserializer, MapAccess, SeqAccess, Visitor};
use toml::value::Datetime as TomlDatetime;

use crate::datetime;

pub const DATETIME_MAPPING_KEY: &str = "$__toml_private_datetime";
type BuildNoHashHasher<T> = BuildHasherDefault<NoHashHasher<T>>;
pub type NoHashSet<T> = HashSet<T, BuildNoHashHasher<T>>;

pub struct PyDeserializer<'py> {
    py: Python<'py>,
    none_value: Option<&'py str>,
}

impl<'py> PyDeserializer<'py> {
    pub fn new(py: Python<'py>, none_value: Option<&'py str>) -> Self {
        Self { py, none_value }
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
        Ok(value.into_py(self.py))
    }

    fn visit_i64<E>(self, value: i64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Ok(value.into_py(self.py))
    }

    fn visit_u64<E>(self, value: u64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Ok(value.into_py(self.py))
    }

    fn visit_f64<E>(self, value: f64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Ok(value.into_py(self.py))
    }

    fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        match self.none_value {
            Some(none_value) if value == none_value => Ok(self.py.None()),
            _ => Ok(value.into_py(self.py)),
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

        Ok(elements.into_py(self.py))
    }

    fn visit_map<A>(self, mut map_access: A) -> Result<Self::Value, A::Error>
    where
        A: MapAccess<'de>,
    {
        match map_access.next_entry_seed(PhantomData::<String>, PyDeserializer::new(self.py, self.none_value))? {
            Some((first_key, first_value)) if first_key == DATETIME_MAPPING_KEY => {
                let py_string = first_value.extract::<&str>(self.py).map_err(de::Error::custom)?;
                let dt: TomlDatetime = TomlDatetime::from_str(py_string).map_err(de::Error::custom)?;
                Ok(datetime::parse(self.py, &dt).map_err(de::Error::custom)?)
            }
            Some((first_key, first_value)) => {
                // we use a hashset to check for duplicate keys, but to avoid cloning the keys, we hash manually
                // and store that in a no-hash hashset
                let hash_builder = RandomState::new();
                let mut key_set = NoHashSet::<u64>::with_hasher(BuildHasherDefault::default());
                key_set.insert(hash_builder.hash_one(&first_key));

                let dict = PyDict::new_bound(self.py);
                dict.set_item(first_key, first_value).map_err(de::Error::custom)?;

                while let Some((key, value)) =
                    map_access.next_entry_seed(PhantomData::<String>, PyDeserializer::new(self.py, self.none_value))?
                {
                    if key_set.insert(hash_builder.hash_one(&key)) {
                        dict.set_item(key, value).map_err(de::Error::custom)?;
                    } else {
                        return Err(de::Error::custom(format!("duplicate key: `{key}`")));
                    }
                }

                Ok(dict.into_py(self.py))
            }
            None => Ok(PyDict::new_bound(self.py).into_py(self.py)),
        }
    }
}
