extern crate pyo3;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDate, PyDateTime, PyDelta, PyTime, PyTzInfo};
use toml::value::{Datetime as TomlDatetime, Offset as TomlOffset};

pub fn parse(py: Python, datetime: &TomlDatetime) -> PyResult<PyObject> {
    let py_dt: PyObject = match &datetime.date {
        Some(date) => match &datetime.time {
            Some(t) => {
                let tzinfo: Option<Bound<'_, PyTzInfo>> = match &datetime.offset {
                    Some(offset) => {
                        let tz_info = match offset {
                            TomlOffset::Z => TzInfo::new(0, 0),
                            TomlOffset::Custom { hours, minutes } => TzInfo::new(*hours, *minutes),
                        };
                        Some(Bound::new(py, tz_info)?.into_any().downcast_into()?)
                    }
                    None => None,
                };

                PyDateTime::new_bound(
                    py,
                    date.year as i32,
                    date.month,
                    date.day,
                    t.hour,
                    t.minute,
                    t.second,
                    t.nanosecond / 1000,
                    tzinfo.as_ref(),
                )?
                .to_object(py)
            }
            None => PyDate::new_bound(py, date.year as i32, date.month, date.day)?.to_object(py),
        },
        None => match &datetime.time {
            Some(t) => PyTime::new_bound(py, t.hour, t.minute, t.second, t.nanosecond / 1000, None)?.to_object(py),
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

    fn utcoffset<'py>(&self, py: Python<'py>, _dt: &Bound<'py, PyDateTime>) -> PyResult<Bound<'py, PyDelta>> {
        PyDelta::new_bound(py, 0, self.seconds(), 0, true)
    }

    fn tzname(&self, _dt: &Bound<'_, PyDateTime>) -> String {
        self.__str__()
    }

    fn dst(&self, _dt: &Bound<'_, PyDateTime>) -> Option<&PyDelta> {
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
