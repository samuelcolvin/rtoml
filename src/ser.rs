//! Writes Python objects out as TOML directly, without going through serde.
//!
//! The `toml` crate's serializer walks every value twice, once to decide whether it's a plain value, a table
//! or an array of tables and once to write it, and buffers each table separately. Doing the walk ourselves
//! is cheaper, we know the strategy for a Python object from its type alone. The actual formatting of keys,
//! strings, numbers and datetimes is delegated to `toml_writer`, the same crate `toml` uses, so the output is
//! identical.
use std::fmt::Write as _;

use pyo3::prelude::*;
use pyo3::types::{PyAny, PyByteArray, PyBytes, PyDateTime, PyDict, PyList, PyString, PyTuple};
use toml_writer::TomlWrite;

use crate::datetime;
use crate::py_type::PyTypeLookup;

type Result<T> = std::result::Result<T, String>;

/// Deepest nesting of tables, inline tables and arrays we'll write. Deeper structures, including ones that
/// contain themselves, would otherwise overflow the stack and take the process down. The toml crate's parser
/// refuses to read anything nested more than 80 deep, so this is already generous.
const MAX_DEPTH: usize = 128;

/// Serialize `obj` to a TOML string.
///
/// A dict becomes a TOML document, anything else is written as a bare TOML value, `pretty` only affects
/// documents.
pub fn to_toml(py: Python<'_>, obj: &Bound<'_, PyAny>, none_value: Option<&str>, pretty: bool) -> Result<String> {
    let lookup = PyTypeLookup::cached(py);
    let mut writer = Writer {
        none_value,
        pretty: false,
        lookup,
        out: String::with_capacity(256),
        depth: 0,
    };
    if obj.get_type_ptr() as usize == lookup.dict {
        writer.pretty = pretty;
        let dict = obj.cast::<PyDict>().map_err(|e| e.to_string())?;
        writer.write_table(dict, &mut Vec::new(), TableKind::Root)?;
    } else {
        writer.write_value(obj)?;
    }
    Ok(writer.out)
}

struct Writer<'py> {
    none_value: Option<&'py str>,
    /// write arrays with two or more elements one element per line
    pretty: bool,
    lookup: &'py PyTypeLookup,
    out: String,
    /// how many tables, inline tables and arrays we're currently inside
    depth: usize,
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum TableKind {
    /// the top level dict, never has a header
    Root,
    /// `[a.b]`, the header is omitted if the table has no values of its own but does have sub-tables
    Table,
    /// `[[a.b]]`, always has a header, even if empty
    ArrayElement,
}

/// An entry of a dict, with its value already classified.
struct Entry<'py> {
    key: Bound<'py, PyAny>,
    value: Bound<'py, PyAny>,
}

macro_rules! err {
    ($($arg:tt)*) => { Err(format!($($arg)*)) };
}

impl<'py> Writer<'py> {
    /// Call on entering a table, inline table or array, must be paired with `leave` on the success path;
    /// on error the writer is abandoned so there's nothing to restore.
    fn enter(&mut self) -> Result<()> {
        self.depth += 1;
        if self.depth > MAX_DEPTH {
            err!("TOML nesting too deep, the limit is {MAX_DEPTH} levels, does the object contain itself?")
        } else {
            Ok(())
        }
    }

    fn leave(&mut self) {
        self.depth -= 1;
    }

    /// Split a dict into plain values, arrays and sub-dicts, in that order, dropping `None` entries when
    /// `none_value` is `None`. This order is what rtoml has always produced: values first, then arrays, then
    /// tables.
    fn partition(&self, dict: &Bound<'py, PyDict>) -> (Vec<Entry<'py>>, Vec<Entry<'py>>, Vec<Entry<'py>>) {
        let lookup = self.lookup;
        let mut simple = Vec::new();
        let mut arrays = Vec::new();
        let mut dicts = Vec::new();
        for (key, value) in dict {
            let value_type = value.get_type_ptr() as usize;
            if self.none_value.is_none() && (value_type == lookup.none || key.is_none()) {
                continue;
            }
            let entry = Entry { key, value };
            if value_type == lookup.dict {
                dicts.push(entry);
            } else if value_type == lookup.list || value_type == lookup.tuple {
                arrays.push(entry);
            } else {
                simple.push(entry);
            }
        }
        (simple, arrays, dicts)
    }

    /// Whether a list or tuple should be written as an array of tables (`[[a]]`), which is the case when it
    /// has at least one element and every element is a dict.
    fn is_array_of_tables(&self, array: &Bound<'py, PyAny>) -> bool {
        let mut any = false;
        for element in self.array_elements(array) {
            let element_type = element.get_type_ptr() as usize;
            if element_type == self.lookup.dict {
                any = true;
            } else if self.none_value.is_none() && element_type == self.lookup.none {
                // skipped when written, so doesn't count
            } else {
                return false;
            }
        }
        any
    }

    fn array_elements(&self, array: &Bound<'py, PyAny>) -> Vec<Bound<'py, PyAny>> {
        if let Ok(list) = array.cast::<PyList>() {
            list.iter().collect()
        } else {
            // the caller has checked the type, so this is a tuple
            array.cast::<PyTuple>().map(|t| t.iter().collect()).unwrap_or_default()
        }
    }

    fn write_table(&mut self, dict: &Bound<'py, PyDict>, path: &mut Vec<String>, kind: TableKind) -> Result<()> {
        self.enter()?;
        let (simple, arrays, dicts) = self.partition(dict);
        let arrays: Vec<(Entry<'py>, bool)> = arrays
            .into_iter()
            .map(|entry| {
                let aot = self.is_array_of_tables(&entry.value);
                (entry, aot)
            })
            .collect();

        let has_body = !simple.is_empty() || arrays.iter().any(|(_, aot)| !aot);
        let has_children = !dicts.is_empty() || arrays.iter().any(|(_, aot)| *aot);
        match kind {
            TableKind::Root => {}
            TableKind::Table => {
                if has_body || !has_children {
                    self.write_header(path, false)?;
                }
            }
            TableKind::ArrayElement => self.write_header(path, true)?,
        }

        for entry in &simple {
            self.write_key_value(entry)?;
        }
        for (entry, aot) in &arrays {
            if !aot {
                self.write_key_value(entry)?;
            }
        }
        for (entry, aot) in &arrays {
            if *aot {
                path.push(self.encode_key(&entry.key)?);
                for element in self.array_elements(&entry.value) {
                    if element.is_none() {
                        continue;
                    }
                    let element = element.cast::<PyDict>().map_err(|e| e.to_string())?;
                    self.write_table(element, path, TableKind::ArrayElement)?;
                }
                path.pop();
            }
        }
        for entry in &dicts {
            path.push(self.encode_key(&entry.key)?);
            let dict = entry.value.cast::<PyDict>().map_err(|e| e.to_string())?;
            self.write_table(dict, path, TableKind::Table)?;
            path.pop();
        }
        self.leave();
        Ok(())
    }

    /// Write `[a.b]` or `[[a.b]]` on its own line, preceded by a blank line unless this is the start of the
    /// document.
    fn write_header(&mut self, path: &[String], array: bool) -> Result<()> {
        if !self.out.is_empty() {
            self.out.push('\n');
        }
        self.out.push_str(if array { "[[" } else { "[" });
        for (i, key) in path.iter().enumerate() {
            if i > 0 {
                self.out.push('.');
            }
            self.out.push_str(key);
        }
        self.out.push_str(if array { "]]\n" } else { "]\n" });
        Ok(())
    }

    fn write_key_value(&mut self, entry: &Entry<'py>) -> Result<()> {
        self.write_key(&entry.key)?;
        self.out.push_str(" = ");
        self.write_value(&entry.value)?;
        self.out.push('\n');
        Ok(())
    }

    /// Write a dict key, bare where TOML allows it and quoted otherwise.
    fn write_key(&mut self, key: &Bound<'py, PyAny>) -> Result<()> {
        if let Ok(py_string) = key.cast::<PyString>() {
            let s = py_string.to_str().map_err(|e| e.to_string())?;
            self.out.key(s).map_err(fmt_err)
        } else if key.is_none() {
            self.out.key(self.none_value.unwrap_or("null")).map_err(fmt_err)
        } else if let Ok(b) = key.extract::<bool>() {
            self.out.key(if b { "true" } else { "false" }).map_err(fmt_err)
        } else {
            err!("{} is not serializable as a TOML key", any_repr(key))
        }
    }

    /// The same as `write_key` but into a new string, for building table header paths.
    fn encode_key(&self, key: &Bound<'py, PyAny>) -> Result<String> {
        let mut out = String::new();
        if let Ok(py_string) = key.cast::<PyString>() {
            let s = py_string.to_str().map_err(|e| e.to_string())?;
            out.key(s).map_err(fmt_err)?;
        } else if key.is_none() {
            out.key(self.none_value.unwrap_or("null")).map_err(fmt_err)?;
        } else if let Ok(b) = key.extract::<bool>() {
            out.key(if b { "true" } else { "false" }).map_err(fmt_err)?;
        } else {
            return err!("{} is not serializable as a TOML key", any_repr(key));
        }
        Ok(out)
    }

    /// Write any value in its inline form, a dict becomes an inline table and a list an array.
    fn write_value(&mut self, obj: &Bound<'py, PyAny>) -> Result<()> {
        let lookup = self.lookup;
        let ob_type = obj.get_type_ptr() as usize;
        // a chain of comparisons on the type pointer is marginally faster than a match
        if ob_type == lookup.none {
            self.out.value(self.none_value.unwrap_or("null")).map_err(fmt_err)
        } else if ob_type == lookup.int {
            match obj.extract::<i64>() {
                Ok(v) => write!(self.out, "{v}").map_err(fmt_err),
                Err(_) => {
                    let v = obj.extract::<i128>().map_err(|e| e.to_string())?;
                    write!(self.out, "{v}").map_err(fmt_err)
                }
            }
        } else if ob_type == lookup.bool {
            let v = obj.extract::<bool>().map_err(|e| e.to_string())?;
            self.out.push_str(if v { "true" } else { "false" });
            Ok(())
        } else if ob_type == lookup.float {
            let mut v = obj.extract::<f64>().map_err(|e| e.to_string())?;
            if v.is_nan() {
                // the sign of nan is rarely meaningful, don't write `-nan`
                v = v.copysign(1.0);
            }
            self.out.value(v).map_err(fmt_err)
        } else if ob_type == lookup.string {
            let py_string = obj.cast::<PyString>().map_err(|e| e.to_string())?;
            let s = py_string.to_str().map_err(|e| e.to_string())?;
            self.out.value(s).map_err(fmt_err)
        } else if ob_type == lookup.dict {
            let dict = obj.cast::<PyDict>().map_err(|e| e.to_string())?;
            self.write_inline_table(dict)
        } else if ob_type == lookup.list || ob_type == lookup.tuple {
            let len = obj.len().map_err(|e| e.to_string())?;
            let elements = self.array_elements(obj);
            self.write_array(len, elements.iter(), |w, element| {
                if element.is_none() && w.none_value.is_none() {
                    Ok(false)
                } else {
                    w.write_value(element)?;
                    Ok(true)
                }
            })
        } else if ob_type == lookup.datetime {
            let py_dt = obj.cast::<PyDateTime>().map_err(|e| e.to_string())?;
            let dt = datetime::datetime_to_toml(py_dt).map_err(|e| e.to_string())?;
            write!(self.out, "{dt}").map_err(fmt_err)
        } else if ob_type == lookup.date {
            let dt = datetime::date_only_to_toml(obj.cast().map_err(|e| e.to_string())?);
            write!(self.out, "{dt}").map_err(fmt_err)
        } else if ob_type == lookup.time {
            let dt = datetime::time_only_to_toml(obj.cast().map_err(|e| e.to_string())?);
            write!(self.out, "{dt}").map_err(fmt_err)
        } else if ob_type == lookup.bytes {
            let bytes = obj.cast::<PyBytes>().map_err(|e| e.to_string())?.as_bytes();
            self.write_array(bytes.len(), bytes.iter(), |w, b| {
                write!(w.out, "{b}").map_err(fmt_err)?;
                Ok(true)
            })
        } else if ob_type == lookup.bytearray {
            let bytes = obj.cast::<PyByteArray>().map_err(|e| e.to_string())?.to_vec();
            self.write_array(bytes.len(), bytes.iter(), |w, b| {
                write!(w.out, "{b}").map_err(fmt_err)?;
                Ok(true)
            })
        } else {
            err!("{} is not serializable to TOML", any_repr(obj))
        }
    }

    /// `{ a = 1, b = 2 }`, entries in the same order as a table: values, arrays, then dicts.
    fn write_inline_table(&mut self, dict: &Bound<'py, PyDict>) -> Result<()> {
        self.enter()?;
        let (simple, arrays, dicts) = self.partition(dict);
        self.out.push('{');
        let mut seen = false;
        for entry in simple.iter().chain(&arrays).chain(&dicts) {
            if seen {
                self.out.push(',');
            }
            seen = true;
            self.out.push(' ');
            self.write_key(&entry.key)?;
            self.out.push_str(" = ");
            self.write_value(&entry.value)?;
        }
        if seen {
            self.out.push(' ');
        }
        self.out.push('}');
        self.leave();
        Ok(())
    }

    /// Write `[a, b]`, or one element per line in pretty mode when there are two or more elements.
    /// `write_element` returns whether it wrote anything, so `None` elements can be skipped.
    fn write_array<T>(
        &mut self,
        len: usize,
        elements: impl Iterator<Item = T>,
        mut write_element: impl FnMut(&mut Self, T) -> Result<bool>,
    ) -> Result<()> {
        self.enter()?;
        let multiline = self.pretty && len >= 2;
        self.out.push('[');
        let mut seen = false;
        for element in elements {
            let before = self.out.len();
            if multiline {
                self.out.push_str("\n    ");
            } else if seen {
                self.out.push_str(", ");
            }
            if write_element(self, element)? {
                seen = true;
                if multiline {
                    self.out.push(',');
                }
            } else {
                self.out.truncate(before);
            }
        }
        if multiline && seen {
            self.out.push('\n');
        }
        self.out.push(']');
        self.leave();
        Ok(())
    }
}

fn fmt_err(_: std::fmt::Error) -> String {
    "error writing TOML".to_string()
}

fn any_repr(obj: &Bound<'_, PyAny>) -> String {
    let typ = obj.get_type();
    let name = typ.name().unwrap_or_else(|_| PyString::new(obj.py(), "unknown"));
    match obj.repr() {
        Ok(repr) => format!("{repr} ({name})"),
        Err(_) => name.to_string(),
    }
}
