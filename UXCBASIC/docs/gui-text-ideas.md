# UXC GUI FORMS v1 Design Notes

*Inspired by dBASE II / III business applications*

## Philosophy

The goal is **not** a modern widget toolkit.

The goal is a **dBASE-style business forms system** where the programmer spends time defining data and workflow rather than screen coordinates.

These should solve 90% of real-world business applications.

---

# Object Model

A **Form** contains one or more **Sections**.

A **Section** contains **Controls**.

Forms handle:

- Layout
- Navigation
- Validation
- Saving
- Loading

Controls remain simple.

---

# Form Verbs

## Create / Destroy

```basic
GUI.CreateForm()
GUI.DestroyForm()
```

## Display

```basic
GUI.Show()
GUI.Hide()
```

## Persistence

```basic
GUI.Save()
GUI.Load()
```

## Data

```basic
GUI.LoadData()
GUI.SaveData()
```

## Runtime

```basic
GUI.Run()