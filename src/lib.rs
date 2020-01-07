use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use pyo3::types::{PyDict, PyList, PyTuple, PyDateTime};
use toml::Value;
use toml::Value::{String, Integer, Float, Boolean, Datetime, Array, Table};
use chrono::{DateTime};

fn convert_value(py: Python, t: &Value) -> PyObject {
    match *t {
        Table(ref table) => {
            let d = PyDict::new(py);
            for (key, value) in table.iter() {
                d.set_item(key.to_string(), convert_value(py,value)).unwrap();
            }
            d.to_object(py)
        },

        Array(ref array) => {
            let l = PyList::empty(py);
            for value in array.iter() {
                l.append(convert_value(py, value)).unwrap();
            }
            l.to_object(py)
        },
        String(ref v) => v.to_object(py),
        Integer(ref v) => v.to_object(py),
        Float(ref v) => v.to_object(py),
        Boolean(ref v) => v.to_object(py),
        Datetime(ref v) => {

            let parse_dt = py.import("parse_dt").unwrap();
            let parse_datetime = parse_dt.get("parse_datetime").unwrap().to_object(py);
            let args = PyTuple::new(py, &[v.to_string().to_object(py)]);
            println!("{:?}", parse_datetime.call1(py, args));

            // really ugly, but only option since toml datetime keeps .date and .time private
//            let datetime = py.import("datetime").unwrap();
//            let timezone = datetime.get("timezone").unwrap();
//            datetime.timezone(

            let dt = DateTime::parse_from_rfc3339(&v.to_string()).unwrap();
//            println!("{:?}", dt);
////            if let Some(date) = dt.date {
////                if let Some(time) = dt.time {
////                    println!("{} {}", date, time)
////                }
////            }
            PyDateTime::from_timestamp(py, dt.timestamp() as f64, None).unwrap().to_object(py)
        }
    }
}


#[pyfunction]
fn load(py: Python, toml: std::string::String) -> PyResult<PyObject> {
    let value = toml.parse::<Value>().unwrap();
    let obj = convert_value(py,&value);
    Ok(obj)
}

#[pymodule]
fn rtoml(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_wrapped(wrap_pyfunction!(load))?;

    Ok(())
}
