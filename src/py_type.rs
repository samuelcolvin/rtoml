use pyo3::prelude::*;
use pyo3::sync::GILOnceCell;
use pyo3::types::{PyByteArray, PyBytes, PyDate, PyDateTime, PyDict, PyList, PyString, PyTime, PyTuple};

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
            none: py.None().bind(py).get_type_ptr() as usize,
            // numeric types
            int: 0i32.into_py(py).bind(py).get_type_ptr() as usize,
            bool: true.into_py(py).bind(py).get_type_ptr() as usize,
            float: 0f32.into_py(py).bind(py).get_type_ptr() as usize,
            // string types
            string: PyString::new_bound(py, "s").get_type_ptr() as usize,
            bytes: PyBytes::new_bound(py, b"s").get_type_ptr() as usize,
            bytearray: PyByteArray::new_bound(py, b"s").get_type_ptr() as usize,
            // sequence types
            list: PyList::empty_bound(py).get_type_ptr() as usize,
            tuple: PyTuple::empty_bound(py).get_type_ptr() as usize,
            // mapping types
            dict: PyDict::new_bound(py).get_type_ptr() as usize,
            // datetime types
            datetime: PyDateTime::new_bound(py, 2000, 1, 1, 0, 0, 0, 0, None)
                .unwrap()
                .get_type_ptr() as usize,
            date: PyDate::new_bound(py, 2000, 1, 1).unwrap().get_type_ptr() as usize,
            time: PyTime::new_bound(py, 0, 0, 0, 0, None).unwrap().get_type_ptr() as usize,
        }
    }

    pub fn cached(py: Python<'_>) -> &PyTypeLookup {
        TYPE_LOOKUP.get_or_init(py, || PyTypeLookup::new(py))
    }
}
