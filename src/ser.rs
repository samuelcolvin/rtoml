use std::fmt;
use std::str::FromStr;

use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDate, PyDateTime, PyDict, PyList, PyString, PyTime, PyTuple};
use serde::ser::{Error as SerError, Serialize, SerializeMap, SerializeSeq, Serializer};
use toml::value::Datetime;

use crate::py_type::PyTypeLookup;

pub struct SerializePyObject<'py> {
    obj: &'py PyAny,
    py: Python<'py>,
    none_value: Option<&'py str>,
    ob_type_lookup: &'py PyTypeLookup,
}

impl<'py> SerializePyObject<'py> {
    pub fn new(py: Python<'py>, obj: &'py PyAny, none_value: Option<&'py str>) -> Self {
        Self {
            obj,
            py,
            none_value,
            ob_type_lookup: PyTypeLookup::cached(py),
        }
    }

    fn with_obj(&self, obj: &'py PyAny) -> Self {
        Self {
            obj,
            py: self.py,
            none_value: self.none_value,
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
            serializer.serialize_str(self.none_value.unwrap())
        } else if ob_type == lookup.int {
            serialize!(i64)
        } else if ob_type == lookup.bool {
            serialize!(bool)
        } else if ob_type == lookup.float {
            serialize!(f64)
        } else if ob_type == lookup.string {
            let py_str: &PyString = self.obj.downcast().map_err(map_py_err)?;
            let s = py_str.to_str().map_err(map_py_err)?;
            serializer.serialize_str(s)
        } else if ob_type == lookup.dict {
            let py_dict: &PyDict = self.obj.downcast().map_err(map_py_err)?;

            let len = py_dict.len();
            let mut simple_items: Vec<(&PyAny, &PyAny)> = Vec::with_capacity(len);
            let mut array_items: Vec<(&PyAny, &PyAny)> = Vec::with_capacity(len);
            let mut dict_items: Vec<(&PyAny, &PyAny)> = Vec::with_capacity(len);

            for (k, v) in py_dict {
                let v_ob_type = v.get_type_ptr() as usize;
                if self.none_value.is_none() && (v_ob_type == lookup.none || k.is_none()) {
                    continue;
                } else if v_ob_type == lookup.dict {
                    dict_items.push((k, v));
                } else if v_ob_type == lookup.list || v_ob_type == lookup.tuple {
                    array_items.push((k, v));
                } else {
                    simple_items.push((k, v));
                }
            }
            let mut map = serializer.serialize_map(Some(len))?;
            for (k, v) in simple_items {
                let key = table_key(k, self.none_value)?;
                let value = self.with_obj(v);
                map.serialize_entry(key, &value)?;
            }
            for (k, v) in array_items {
                let key = table_key(k, self.none_value)?;
                let value = self.with_obj(v);
                map.serialize_entry(key, &value)?;
            }
            for (k, v) in dict_items {
                let key = table_key(k, self.none_value)?;
                let value = self.with_obj(v);
                map.serialize_entry(key, &value)?;
            }
            map.end()
        } else if ob_type == lookup.list {
            let py_list: &PyList = self.obj.downcast().map_err(map_py_err)?;
            let mut seq = serializer.serialize_seq(Some(py_list.len()))?;
            for element in py_list {
                if self.none_value.is_none() && element.is_none() {
                    continue;
                }
                seq.serialize_element(&self.with_obj(element))?
            }
            seq.end()
        } else if ob_type == lookup.tuple {
            let py_tuple: &PyTuple = self.obj.downcast().map_err(map_py_err)?;
            let mut seq = serializer.serialize_seq(Some(py_tuple.len()))?;
            for element in py_tuple {
                if self.none_value.is_none() && element.is_none() {
                    continue;
                }
                seq.serialize_element(&self.with_obj(element))?
            }
            seq.end()
        } else if ob_type == lookup.datetime {
            let py_dt: &PyDateTime = self.obj.downcast().map_err(map_py_err)?;
            let dt_str = py_dt.str().map_err(map_py_err)?.to_str().map_err(map_py_err)?;
            let iso_str = dt_str.replacen("+00:00", "Z", 1);
            match Datetime::from_str(&iso_str) {
                Ok(dt) => dt.serialize(serializer),
                Err(e) => serde_err!("unable to convert datetime string to TOML datetime object {:?}", e),
            }
        } else if ob_type == lookup.date {
            let py_date: &PyDate = self.obj.downcast().map_err(map_py_err)?;
            let date_str = py_date.str().map_err(map_py_err)?.to_str().map_err(map_py_err)?;
            match Datetime::from_str(date_str) {
                Ok(dt) => dt.serialize(serializer),
                Err(e) => serde_err!("unable to convert date string to TOML date object {:?}", e),
            }
        } else if ob_type == lookup.time {
            let py_time: &PyTime = self.obj.downcast().map_err(map_py_err)?;
            let time_str = py_time.str().map_err(map_py_err)?.to_str().map_err(map_py_err)?;
            match Datetime::from_str(time_str) {
                Ok(dt) => dt.serialize(serializer),
                Err(e) => serde_err!("unable to convert time string to TOML time object {:?}", e),
            }
        } else if ob_type == lookup.bytes || ob_type == lookup.bytearray {
            serialize!(&[u8])
        } else {
            serde_err!("{} is not serializable to TOML", any_repr(self.obj))
        }
    }
}

fn map_py_err<I: fmt::Display, O: SerError>(err: I) -> O {
    O::custom(err.to_string())
}

fn table_key<'a, E: SerError>(key: &'a PyAny, none_value: Option<&'a str>) -> Result<&'a str, E> {
    if let Ok(py_string) = key.downcast::<PyString>() {
        py_string.to_str().map_err(map_py_err)
    } else if key.is_none() {
        Ok(none_value.unwrap())
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
