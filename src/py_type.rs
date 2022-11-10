use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::{
    PyByteArray, PyBytes, PyDate, PyDateTime, PyDelta, PyDict, PyFrozenSet, PyList, PySet, PyString, PyTime, PyTuple,
};

pub struct FindPyType<'py> {
    ob_type_lookup: &'py ObTypeLookup,
}

impl<'py> FindPyType<'py> {
    pub fn new(py: Python) -> Self {
        let ob_type_lookup = TYPE_LOOKUP.get_or_init(py, || ObTypeLookup::new(py));
        Self { ob_type_lookup }
    }

    pub fn find(&self, obj: &PyAny) -> PyObType {
        let lookup = self.ob_type_lookup;

        let ob_type = obj.get_type_ptr() as usize;
        // ugly but this seems to be just marginally faster than a guarded match, also allows for custom cases
        // if we wanted to add them
        if ob_type == lookup.none {
            PyObType::None
        } else if ob_type == lookup.int {
            PyObType::Int
        } else if ob_type == lookup.bool {
            PyObType::Bool
        } else if ob_type == lookup.float {
            PyObType::Float
        } else if ob_type == lookup.string {
            PyObType::String
        } else if ob_type == lookup.bytes {
            PyObType::Bytes
        } else if ob_type == lookup.bytearray {
            PyObType::ByteArray
        } else if ob_type == lookup.list {
            PyObType::List
        } else if ob_type == lookup.tuple {
            PyObType::Tuple
        } else if ob_type == lookup.set {
            PyObType::Set
        } else if ob_type == lookup.frozenset {
            PyObType::FrozenSet
        } else if ob_type == lookup.dict {
            PyObType::Dict
        } else if ob_type == lookup.datetime {
            PyObType::Datetime
        } else if ob_type == lookup.date {
            PyObType::Date
        } else if ob_type == lookup.time {
            PyObType::Time
        } else if ob_type == lookup.timedelta {
            PyObType::TimeDelta
        } else {
            PyObType::Unknown
        }
    }
}

#[derive(Debug)]
pub enum PyObType {
    None,
    // numeric types
    Int,
    Bool,
    Float,
    // string types
    String,
    Bytes,
    ByteArray,
    // sequence types
    List,
    Tuple,
    Set,
    FrozenSet,
    // mapping types
    Dict,
    // date and time types
    Datetime,
    Date,
    Time,
    TimeDelta,
    // don't know what this is
    Unknown,
}

static TYPE_LOOKUP: GILOnceCell<ObTypeLookup> = GILOnceCell::new();

#[derive(Clone)]
#[cfg_attr(debug_assertions, derive(Debug))]
struct ObTypeLookup {
    none: usize,
    // numeric types
    int: usize,
    bool: usize,
    float: usize,
    // string types
    string: usize,
    bytes: usize,
    bytearray: usize,
    // sequence types
    list: usize,
    set: usize,
    frozenset: usize,
    tuple: usize,
    // mapping types
    dict: usize,
    // datetime types
    datetime: usize,
    date: usize,
    time: usize,
    timedelta: usize,
}

impl ObTypeLookup {
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
            set: PySet::empty(py).unwrap().get_type_ptr() as usize,
            frozenset: PyFrozenSet::empty(py).unwrap().get_type_ptr() as usize,
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
}
