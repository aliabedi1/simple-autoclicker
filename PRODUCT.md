# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Product Purpose

Simple Autoclicker is a local desktop utility for scheduling left/right/middle mouse clicks, keyboard keys and shortcuts, and ordered patterns mixing those actions. The web interface controls the Python desktop process on the same computer.

## Capabilities and Constraints

Preserve Windows and Linux X11 support, exact point selection, per-step actions and waits, keyboard shortcuts sent to the focused application, pattern editing and JSON files, start delays and dates, stopping by count or end date, progress, cancellation, and sleep prevention on Windows. Linux users disable sleep manually. No Wayland support. The desktop process must run on the computer being clicked. No cloud service or remote control is required.

## Brand Commitments

Preserve the name and pointer-and-clock icon in assets/. The user requested shadcn/ui and confirmed following the system theme. Existing blue identity carries into the primary action and focus treatment.

## Evidence on Hand

The Python implementation, schedule.py, README.md, assets/icon.png, and existing tests establish the product behavior. Specific user occupations and use cases remain unspecified.

## Product Principles

- Make the next click and the stopping condition clear before starting.
- Keep Stop available during a run.
- Run locally on both supported operating systems.
- Preserve keyboard access, explicit labels, and readable feedback.
