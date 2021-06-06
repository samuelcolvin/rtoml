extern crate pyo3;

use chrono::{Datelike, NaiveDate};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDate, PyDateTime, PyDelta, PyTime, PyTzInfo};
use regex::Regex;

lazy_static! {
    static ref DATETIME_RE: Regex = Regex::new(
        r"(?x)
(?:
    (?P<year>\d{4})
    -
    (?P<month>\d{2})
    -
    (?P<day>\d{2})
    (?:T| )
)?
(?P<hour>\d{2})
:
(?P<minute>\d{2})
:
(?P<second>\d{2})
(?:\.(?P<microseconds>\d{1,6}))?
(?P<tz>
    Z
    |
    (?P<tz_sign>\+|\-)
    (?P<tz_hour>\d{2})
    :
    (?P<tz_minute>\d{2})
)?
"
    )
    .unwrap();
}

pub fn parse(py: Python, date_string: String) -> PyResult<PyObject> {
    if let Some(cap) = DATETIME_RE.captures(&date_string) {
        let hour = cap["hour"].parse::<u8>().unwrap();
        let minute = cap["minute"].parse::<u8>().unwrap();
        let second = cap["second"].parse::<u8>().unwrap();
        let microseconds: u32 = match cap.name("microseconds") {
            // We pad the result with zeros so 1.123 is 123000 microseconds
            Some(m) => format!("{:0<6}", m.as_str()).parse::<u32>().unwrap(),
            None => 0,
        };

        return match cap.name("year") {
            Some(y) => {
                let year = y.as_str().parse::<i32>().unwrap();
                let py_tz: PyObject;
                let tzinfo = match cap.name("tz") {
                    Some(_) => {
                        let offset_seconds: i32 = match cap.name("tz_hour") {
                            Some(tz_hour) => {
                                let tz_hour = tz_hour.as_str().parse::<i32>().unwrap();
                                let tz_minute = cap["tz_minute"].parse::<i32>().unwrap();
                                let s = tz_hour * 3600 + tz_minute * 60;
                                if cap["tz_sign"] == *"-" {
                                    -s
                                } else {
                                    s
                                }
                            }
                            None => 0,
                        };
                        let tz_info = TzClass::new(offset_seconds);
                        py_tz = Py::new(py, tz_info)?.to_object(py);
                        Some(&py_tz)
                    }
                    None => None,
                };
                let dt = PyDateTime::new(
                    py,
                    year,
                    cap["month"].parse::<u8>().unwrap(),
                    cap["day"].parse::<u8>().unwrap(),
                    hour,
                    minute,
                    second,
                    microseconds,
                    tzinfo,
                )?;
                Ok(dt.to_object(py))
            }
            None => {
                if cap.name("tz").is_some() {
                    let msg = format!("tz not allowed with times \"{}\"", date_string);
                    Err(PyErr::new::<PyValueError, _>(PyValueError::new_err(msg)))
                } else {
                    let py_time = PyTime::new(py, hour, minute, second, microseconds, None)?;
                    Ok(py_time.to_object(py))
                }
            }
        };
    }

    if let Ok(date) = NaiveDate::parse_from_str(&date_string, "%F") {
        let py_date = PyDate::new(py, date.year(), date.month() as u8, date.day() as u8)?;
        return Ok(py_date.to_object(py));
    }

    let msg = format!("invalid date/time format \"{}\"", date_string);
    Err(PyErr::new::<PyValueError, _>(PyValueError::new_err(msg)))
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
        if self.seconds == 0 {
            "UTC".to_string()
        } else {
            let minutes = self.seconds / 60;
            format!("UTC{:+03}:{:02}", minutes / 60, minutes % 60)
        }
    }

    fn dst(&self, _py: Python<'_>, _dt: &PyDateTime) -> Option<&PyDelta> {
        None
    }
}
