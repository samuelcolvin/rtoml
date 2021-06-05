extern crate pyo3;

use chrono::{DateTime, Datelike, NaiveDate, NaiveTime, Timelike};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDate, PyDateTime, PyDelta, PyTime, PyTzInfo};
use regex::Regex;

pub fn parse(py: Python, date_string: String) -> PyResult<PyObject> {
    let option_dt = match DateTime::parse_from_rfc3339(&date_string) {
        Ok(d) => Some(d),
        Err(_) => None,
    };
    if let Some(dt) = option_dt {
        let date = dt.date();
        let time = dt.time();
        let offset_seconds = dt.offset().local_minus_utc();
        let tz_info = TzClass::new(offset_seconds);

        let dt = PyDateTime::new(
            py,
            date.year(),
            date.month() as u8,
            date.day() as u8,
            time.hour() as u8,
            time.minute() as u8,
            time.second() as u8,
            time.nanosecond() / 1000_u32,
            Some(&Py::new(py, tz_info)?.to_object(py)),
        )?;
        return Ok(dt.to_object(py));
    }

    lazy_static! {
        static ref DATETIME_RE: Regex = Regex::new(
            r"(?x)
(?P<year>\d{4})
-
(?P<month>\d{2})
-
(?P<day>\d{2})
(?:T| )
(?P<hour>\d{2})
:
(?P<minute>\d{2})
:
(?P<second>\d{2})
(?:\.(?P<micro>\d{1,6}))?
"
        )
        .unwrap();
    }

    if let Some(cap) = DATETIME_RE.captures(&date_string) {
        let microseconds: u32 = match cap.name("micro") {
            Some(m) => format!("{:0<6}", m.as_str()).parse::<u32>().unwrap(),
            None => 0,
        };
        let dt = PyDateTime::new(
            py,
            cap["year"].parse::<i32>().unwrap(),
            cap["month"].parse::<u8>().unwrap(),
            cap["day"].parse::<u8>().unwrap(),
            cap["hour"].parse::<u8>().unwrap(),
            cap["minute"].parse::<u8>().unwrap(),
            cap["second"].parse::<u8>().unwrap(),
            microseconds,
            None,
        )?;
        return Ok(dt.to_object(py));
    }

    let option_date = match NaiveDate::parse_from_str(&date_string, "%F") {
        Ok(d) => Some(d),
        Err(_) => None,
    };
    if let Some(date) = option_date {
        let py_date = PyDate::new(py, date.year(), date.month() as u8, date.day() as u8)?;
        return Ok(py_date.to_object(py));
    }

    let option_time = match NaiveTime::parse_from_str(&date_string, "%T") {
        Ok(d) => Some(d),
        Err(_) => None,
    };
    if let Some(time) = option_time {
        let py_time = PyTime::new(
            py,
            time.hour() as u8,
            time.minute() as u8,
            time.second() as u8,
            time.nanosecond() / 1000_u32,
            None,
        )?;
        return Ok(py_time.to_object(py));
    }

    Err(PyErr::new::<PyValueError, _>(PyValueError::new_err(format!(
        "invalid date/time format \"{}\"",
        date_string
    ))))
}

#[pyclass(extends=PyTzInfo)]
struct TzClass {
    seconds: i32,
}

#[pymethods]
impl TzClass {
    #[new]
    fn new(seconds: i32) -> Self {
        TzClass { seconds }
    }

    fn utcoffset<'p>(&self, py: Python<'p>, _dt: &PyDateTime) -> PyResult<&'p PyDelta> {
        PyDelta::new(py, 0, self.seconds, 0, true)
    }

    fn tzname(&self, _py: Python<'_>, _dt: &PyDateTime) -> String {
        let minutes = self.seconds / 60;
        format!("UTC{:+03}:{:02}", minutes / 60, minutes % 60)
    }

    fn dst(&self, _py: Python<'_>, _dt: &PyDateTime) -> Option<&PyDelta> {
        None
    }
}
