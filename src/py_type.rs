use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::{PyByteArray, PyBytes, PyDate, PyDateTime, PyDelta, PyDict, PyList, PyString, PyTime, PyTuple};

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
    pub timedelta: usize,
}

static TYPE_LOOKUP: GILOnceCell<PyTypeLookup> = GILOnceCell::new();

impl PyTypeLookup {
    fn new(py: Python) -> Self {
        Self {
            none: py.None().as_ref(py).get_type_ptr() as usize,
            // numeric types
            int: 0i32.into_py(py).as_ref(py).get_type_ptr() as usize,
            bool: true.into_py(py).as_ref(py).get_type_ptr() as usize,
            float: 0f32.into_py(py).as_ref(py).get_type_ptr() as usize,
            // string types
            string: PyString::new(py, "s").get_type_ptr() as usize,
            bytes: PyBytes::new(py, b"s").get_type_ptr() as usize,
            bytearray: PyByteArray::new(py, b"s").get_type_ptr() as usize,
            // sequence types
            list: PyList::empty(py).get_type_ptr() as usize,
            tuple: PyTuple::empty(py).get_type_ptr() as usize,
            // mapping types
            dict: PyDict::new(py).get_type_ptr() as usize,
            // datetime types
            datetime: PyDateTime::new(py, 2000, 1, 1, 0, 0, 0, 0, None)
                .unwrap()
                .get_type_ptr() as usize,
            date: PyDate::new(py, 2000, 1, 1).unwrap().get_type_ptr() as usize,
            time: PyTime::new(py, 0, 0, 0, 0, None).unwrap().get_type_ptr() as usize,
            timedelta: PyDelta::new(py, 0, 0, 0, false).unwrap().get_type_ptr() as usize,
        }
    }

    pub fn cached(py: Python<'_>) -> &PyTypeLookup {
        TYPE_LOOKUP.get_or_init(py, || PyTypeLookup::new(py))
    }
}
