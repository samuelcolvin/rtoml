extern crate pyo3;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDate, PyDateTime, PyDelta, PyTime, PyTzInfo};
use toml::value::{Datetime as TomlDatetime, Offset as TomlOffset};

pub fn parse(py: Python, datetime: &TomlDatetime) -> PyResult<PyObject> {
    let py_dt: PyObject = match &datetime.date {
        Some(date) => match &datetime.time {
            Some(t) => {
                let py_tz: PyObject;
                let tzinfo = match &datetime.offset {
                    Some(offset) => {
                        let tz_info = match offset {
                            TomlOffset::Z => TzInfo::new(0, 0),
                            TomlOffset::Custom { hours, minutes } => TzInfo::new(*hours, *minutes),
                        };
                        py_tz = Py::new(py, tz_info)?.to_object(py);
                        Some(py_tz.extract(py)?)
                    }
                    None => None,
                };

                PyDateTime::new(
                    py,
                    date.year as i32,
                    date.month,
                    date.day,
                    t.hour,
                    t.minute,
                    t.second,
                    t.nanosecond / 1000,
                    tzinfo,
                )?
                .to_object(py)
            }
            None => PyDate::new(py, date.year as i32, date.month, date.day)?.to_object(py),
        },
        None => match &datetime.time {
            Some(t) => PyTime::new(py, t.hour, t.minute, t.second, t.nanosecond / 1000, None)?.to_object(py),
            None => {
                // AFAIK this can't actually happen
                let msg = "either time or date (or both) are required)".to_string();
                return Err(PyErr::new::<PyValueError, _>(PyValueError::new_err(msg)));
            }
        },
    };
    Ok(py_dt)
}

#[pyclass(module = "rtoml._rtoml", extends = PyTzInfo)]
struct TzInfo {
    hours: i8,
    minutes: u8,
}

#[pymethods]
impl TzInfo {
    #[new]
    fn new(hours: i8, minutes: u8) -> Self {
        Self { hours, minutes }
    }

    fn seconds(&self) -> i32 {
        (self.hours as i32) * 3600 + (self.minutes as i32) * 60
    }

    fn utcoffset<'p>(&self, py: Python<'p>, _dt: &PyDateTime) -> PyResult<&'p PyDelta> {
        PyDelta::new(py, 0, self.seconds(), 0, true)
    }

    fn tzname(&self, _dt: &PyDateTime) -> String {
        self.__str__()
    }

    fn dst(&self, _dt: &PyDateTime) -> Option<&PyDelta> {
        None
    }

    fn __repr__(&self) -> String {
        format!("TzInfo({})", self.__str__())
    }

    fn __str__(&self) -> String {
        if self.hours == 0 && self.minutes == 0 {
            "UTC".to_string()
        } else {
            format!("UTC{:+03}:{:02}", self.hours, self.minutes)
        }
    }
}
