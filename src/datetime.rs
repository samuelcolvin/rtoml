use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{
    PyDate, PyDateAccess, PyDateTime, PyDelta, PyDeltaAccess, PyTime, PyTimeAccess, PyTzInfo, PyTzInfoAccess,
};
use pyo3::{intern, IntoPyObjectExt};

use toml::value::{Date as TomlDate, Datetime as TomlDatetime, Offset as TomlOffset, Time as TomlTime};

pub fn parse(py: Python, datetime: &TomlDatetime) -> PyResult<Py<PyAny>> {
    match (&datetime.date, &datetime.time) {
        (Some(date), Some(t)) => {
            let tz_info: Option<Bound<'_, PyTzInfo>> = match &datetime.offset {
                Some(offset) => {
                    let tz_info = match offset {
                        TomlOffset::Z => TzInfo::new(0),
                        TomlOffset::Custom { minutes } => TzInfo::new(*minutes),
                    };
                    Some(Bound::new(py, tz_info)?.into_any().cast_into()?)
                }
                None => None,
            };

            let dt = PyDateTime::new(
                py,
                date.year as i32,
                date.month,
                date.day,
                t.hour,
                t.minute,
                t.second.unwrap_or(0),
                t.nanosecond.unwrap_or(0) / 1000,
                tz_info.as_ref(),
            )?;
            Ok(dt.into_py_any(py)?)
        }
        (Some(date), None) => Ok(PyDate::new(py, date.year as i32, date.month, date.day)?.into_py_any(py)?),
        (None, Some(t)) => Ok(PyTime::new(
            py,
            t.hour,
            t.minute,
            t.second.unwrap_or(0),
            t.nanosecond.unwrap_or(0) / 1000,
            None,
        )?
        .into_py_any(py)?),
        (None, None) => {
            // AFAIK this can't actually happen
            unreachable!("either time or date (or both) are required")
        }
    }
}

/// Convert a Python `datetime.datetime` to a TOML datetime without going via its string form.
pub fn datetime_to_toml(dt: &Bound<'_, PyDateTime>) -> PyResult<TomlDatetime> {
    let offset = match dt.get_tzinfo() {
        Some(tz_info) => offset_to_toml(dt, &tz_info)?,
        None => None,
    };
    Ok(TomlDatetime {
        date: Some(date_to_toml(dt)),
        time: Some(time_to_toml(dt)),
        offset,
    })
}

/// Convert a Python `datetime.date` to a TOML local date.
pub fn date_only_to_toml(date: &Bound<'_, PyDate>) -> TomlDatetime {
    TomlDatetime {
        date: Some(date_to_toml(date)),
        time: None,
        offset: None,
    }
}

/// Convert a Python `datetime.time` to a TOML local time, any tzinfo on the time is ignored as TOML has no
/// equivalent, which matches the previous behaviour of serializing `str(time)`.
pub fn time_only_to_toml(time: &Bound<'_, PyTime>) -> TomlDatetime {
    TomlDatetime {
        date: None,
        time: Some(time_to_toml(time)),
        offset: None,
    }
}

fn date_to_toml(d: &impl PyDateAccess) -> TomlDate {
    TomlDate {
        year: d.get_year() as u16,
        month: d.get_month(),
        day: d.get_day(),
    }
}

fn time_to_toml(t: &impl PyTimeAccess) -> TomlTime {
    let microsecond = t.get_microsecond();
    TomlTime {
        hour: t.get_hour(),
        minute: t.get_minute(),
        second: Some(t.get_second()),
        // omit the fraction entirely when it's zero, as `datetime.isoformat()` does
        nanosecond: (microsecond != 0).then_some(microsecond * 1000),
    }
}

/// `None` means the datetime is naive, which Python also uses for a tzinfo whose `utcoffset()` returns `None`.
fn offset_to_toml(dt: &Bound<'_, PyDateTime>, tz_info: &Bound<'_, PyTzInfo>) -> PyResult<Option<TomlOffset>> {
    let minutes = if let Ok(tz_info) = tz_info.cast::<TzInfo>() {
        // fast path for datetimes rtoml parsed itself
        tz_info.get().minutes
    } else {
        // go via the datetime rather than calling the tzinfo directly, so Python checks the offset is a
        // timedelta strictly within +/-24 hours
        let delta = dt.call_method0(intern!(dt.py(), "utcoffset"))?;
        if delta.is_none() {
            return Ok(None);
        }
        let delta = delta.cast::<PyDelta>()?;
        let seconds = delta.get_days() as i64 * 86_400 + delta.get_seconds() as i64;
        if delta.get_microseconds() != 0 || seconds % 60 != 0 {
            return Err(PyValueError::new_err(format!(
                "TOML offsets must be a whole number of minutes, got {delta}"
            )));
        }
        // |seconds| < 86_400 after Python's check, so this fits comfortably
        (seconds / 60) as i16
    };
    Ok(Some(if minutes == 0 {
        TomlOffset::Z
    } else {
        TomlOffset::Custom { minutes }
    }))
}

#[pyclass(module = "rtoml._rtoml", extends = PyTzInfo, frozen)]
struct TzInfo {
    /// offset from UTC in minutes, may be negative
    minutes: i16,
}

#[pymethods]
impl TzInfo {
    #[new]
    fn new(minutes: i16) -> Self {
        Self { minutes }
    }

    fn seconds(&self) -> i32 {
        (self.minutes as i32) * 60
    }

    fn utcoffset<'py>(&self, dt: &Bound<'py, PyDateTime>) -> PyResult<Bound<'py, PyDelta>> {
        PyDelta::new(dt.py(), 0, self.seconds(), 0, true)
    }

    fn tzname(&self, _dt: &Bound<'_, PyAny>) -> String {
        self.__str__()
    }

    fn dst<'py>(&self, _dt: &Bound<'py, PyAny>) -> Option<Bound<'py, PyDelta>> {
        None
    }

    fn __repr__(&self) -> String {
        format!("TzInfo({})", self.__str__())
    }

    fn __str__(&self) -> String {
        if self.minutes == 0 {
            "UTC".to_string()
        } else {
            let sign = if self.minutes < 0 { '-' } else { '+' };
            let abs = self.minutes.unsigned_abs();
            format!("UTC{sign}{:02}:{:02}", abs / 60, abs % 60)
        }
    }
}
