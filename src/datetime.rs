use pyo3::prelude::*;
use pyo3::types::{PyDate, PyDateTime, PyDelta, PyTime, PyTzInfo};

use toml::value::{Datetime as TomlDatetime, Offset as TomlOffset};

pub fn parse(py: Python, datetime: &TomlDatetime) -> PyResult<PyObject> {
    match (&datetime.date, &datetime.time) {
        (Some(date), Some(t)) => {
            let tz_info: Option<Bound<'_, PyTzInfo>> = match &datetime.offset {
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
                tz_info.as_ref(),
            )
            .map(|dt| dt.to_object(py))
        }
        (Some(date), None) => PyDate::new_bound(py, date.year as i32, date.month, date.day).map(|d| d.to_object(py)),
        (None, Some(t)) => {
            PyTime::new_bound(py, t.hour, t.minute, t.second, t.nanosecond / 1000, None).map(|t| t.to_object(py))
        }
        (None, None) => {
            // AFAIK this can't actually happen
            unreachable!("either time or date (or both) are required")
        }
    }
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

    fn utcoffset<'py>(&self, dt: &Bound<'py, PyDateTime>) -> PyResult<Bound<'py, PyDelta>> {
        PyDelta::new_bound(dt.py(), 0, self.seconds(), 0, true)
    }

    fn tzname(&self, _dt: &Bound<'_, PyAny>) -> String {
        self.__str__()
    }

    fn dst(&self, _dt: &Bound<'_, PyAny>) -> Option<&PyDelta> {
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
