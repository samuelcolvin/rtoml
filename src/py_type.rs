use pyo3::prelude::*;
use pyo3::sync::GILOnceCell;
use pyo3::types::{
    PyBool, PyByteArray, PyBytes, PyDate, PyDateTime, PyDict, PyFloat, PyInt, PyList, PyNone, PyString, PyTime, PyTuple,
};
use pyo3::PyTypeInfo;

#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
pub struct PyTypeLookup {
    pub none: usize,
    // numeric types
    pub int: usize,
    pub bool: usize,
    pub float: usize,
    // string types
    pub string: usize,
    pub bytes: usize,
    pub bytearray: usize,
    // sequence types
    pub list: usize,
    pub tuple: usize,
    // mapping types
    pub dict: usize,
    // datetime types
    pub datetime: usize,
    pub date: usize,
    pub time: usize,
}

static TYPE_LOOKUP: GILOnceCell<PyTypeLookup> = GILOnceCell::new();

impl PyTypeLookup {
    fn new(py: Python) -> Self {
        Self {
            none: PyNone::type_object_raw(py) as usize,
            // numeric types
            int: PyInt::type_object_raw(py) as usize,
            bool: PyBool::type_object_raw(py) as usize,
            float: PyFloat::type_object_raw(py) as usize,
            // string types
            string: PyString::type_object_raw(py) as usize,
            bytes: PyBytes::type_object_raw(py) as usize,
            bytearray: PyByteArray::type_object_raw(py) as usize,
            // sequence types
            list: PyList::type_object_raw(py) as usize,
            tuple: PyTuple::type_object_raw(py) as usize,
            // mapping types
            dict: PyDict::type_object_raw(py) as usize,
            // datetime types
            datetime: PyDateTime::type_object_raw(py) as usize,
            date: PyDate::type_object_raw(py) as usize,
            time: PyTime::type_object_raw(py) as usize,
        }
    }

    pub fn cached(py: Python<'_>) -> &PyTypeLookup {
        TYPE_LOOKUP.get_or_init(py, || PyTypeLookup::new(py))
    }
}
