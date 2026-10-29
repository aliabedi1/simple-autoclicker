---
name: Simple Autoclicker
description: A clear local workspace for configuring, scheduling, and stopping desktop clicks.
colors:
  primary: "#245db5"
  primary-foreground: "#ffffff"
  background: "#f8fafc"
  foreground: "#172335"
  card: "#ffffff"
  muted: "#f1f5f9"
  muted-foreground: "#58677d"
  secondary: "#edf2f7"
  secondary-foreground: "#334155"
  accent: "#eaf1fc"
  accent-foreground: "#194a96"
  border: "#dfe6ef"
  input: "#d6deea"
  destructive: "oklch(0.577 0.245 27.325)"
  dark-primary: "#82aaff"
  dark-primary-foreground: "#101b31"
  dark-background: "#101318"
  dark-foreground: "#e8edf5"
  dark-card: "#171b22"
  dark-muted: "#202630"
  dark-muted-foreground: "#a1adbd"
  dark-secondary: "#252d39"
  dark-secondary-foreground: "#dce5f1"
  dark-accent: "#24354f"
  dark-accent-foreground: "#b6ceff"
  dark-border: "#303947"
  dark-input: "#3c485b"
  dark-destructive: "oklch(0.704 0.191 22.216)"
typography:
  headline:
    fontFamily: "Geist Variable, sans-serif"
    fontSize: "clamp(26px, 3vw, 32px)"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.035em"
  title:
    fontFamily: "Geist Variable, sans-serif"
    fontSize: "17px"
    fontWeight: 620
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Geist Variable, sans-serif"
    fontSize: "14px"
    lineHeight: 1.5
  label:
    fontFamily: "Geist Variable, sans-serif"
    fontSize: "14px"
    fontWeight: 500
    lineHeight: "20px"
  helper:
    fontFamily: "Geist Variable, sans-serif"
    fontSize: "13px"
    lineHeight: 1.65
rounded:
  sm: "7.2px"
  md: "9.6px"
  lg: "12px"
  panel: "14px"
  badge: "31.2px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  workspace: "22px"
  lg: "24px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    typography: "{typography.label}"
    rounded: "{rounded.lg}"
    height: "32px"
    padding: "0 10px"
  button-outline:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.lg}"
    height: "32px"
    padding: "0 10px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.foreground}"
    rounded: "{rounded.lg}"
    height: "28px"
    width: "28px"
  input:
    backgroundColor: "transparent"
    textColor: "{colors.foreground}"
    rounded: "{rounded.lg}"
    height: "40px"
    padding: "4px 10px"
  panel:
    backgroundColor: "{colors.card}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.panel}"
    padding: "24px"
  badge-outline:
    textColor: "{colors.foreground}"
    rounded: "{rounded.badge}"
    height: "20px"
    padding: "2px 8px"
---

# Design System: Simple Autoclicker

## Overview

**Creative North Star: "Operate"**

A task-focused desktop control surface: precise, calm, and readable while a run is active. The pointer-and-clock identity is retained; blue connects the primary action, focus, and run indicator. Controls use the existing shadcn/ui Radix Nova vocabulary with locally hosted Geist.

The interface follows the system appearance by default and offers explicit light and dark choices. Semantic color roles change together, keeping the same visual hierarchy across both appearances.

**Key Characteristics:**
- Blue primary actions and focus treatment.
- Compact semantic controls with explicit labels.
- Flat, bordered surfaces and restrained tonal layering.
- Responsive setup and schedule panels with a separate run strip.

## Colors

Cool slate neutrals support a clear blue action color; red communicates errors and destructive intent.

### Primary

The primary blue identifies starting a run and adding or saving pattern steps. Its lighter dark-theme counterpart preserves the same role. Primary foreground is the contrasting label color. The focus ring uses the primary color in each theme.

### Neutral

Background is the surrounding workspace; card is the header and panel surface. Foreground carries titles and entered values. Muted foreground carries helper text, metadata, and secondary icons. Muted and secondary provide quiet control states; accent supplies the run icon's tinted surface. Border separates surfaces; input distinguishes field boundaries. Tokens prefixed `dark-` record the corresponding `.dark` overrides, rather than an additional palette for arbitrary use.

Destructive retains the library's OKLCH source values for validation feedback. Popovers inherit the library's white light surface and use the custom dark popover surface in the implementation.

**The Semantic Theme Rule.** Use semantic CSS variables for every surface and state so system, light, and dark appearances remain coherent.

## Typography

**Body and heading font:** locally bundled Geist Variable, with sans-serif fallback. There is no separate display face.

The hierarchy uses modest size changes and variable weights. Main headings tighten tracking; instructional text stays quieter without becoming a separate editorial style.

- **Headline:** the responsive page title uses the frontmatter headline role; at the narrowest breakpoint it becomes 24px.
- **Title:** section titles use the title role; the brand uses 16px, weight 650, and tracking -0.025em.
- **Body:** default text uses the body role.
- **Label:** controls use medium-weight text; metadata and schedule toggle labels step down to 12px.
- **Helper:** instructions use the helper role. Longer point instructions use line-height 1.7 and a 46ch maximum.

**The Stable Numbers Rule.** Use tabular numerals for coordinates, wait values, step numbers, and running counters so updates do not shift their alignment.

## Layout

The workspace is centered at a maximum width of 1120px, with 40px top padding and a 22px vertical rhythm. The main grid pairs a flexible setup panel with a 360px schedule panel, separated by 22px. Panel padding is 24px. Coordinates and intervals use paired columns with 16px gaps.

At 1190px and below, workspace side margins become 28px. At 850px and below, the main panels stack, side margins become 20px, and schedule groups temporarily share two columns. At 560px and below, margins become 12px, panels use 18px padding, schedule groups return to a vertical flow, and run actions span the row. The body supports a 320px minimum width.

The separate run strip wraps its status, actions, and optional full-width progress. It uses 20px by 24px padding, reduced to 16px on small screens. It is in normal document flow.

## Elevation & Depth

The main workspace is flat: card/background contrast and one-pixel borders establish grouping. Panels and the run strip have no decorative shadows. Select popovers use the library's medium shadow; dialogs use a subtle foreground ring, dimmed backdrop, and modal layering. Focus uses a three-pixel ring at half opacity instead of adding persistent elevation.

**The Quiet Surface Rule.** Use borders and semantic surface contrast for ordinary panels; reserve overlay depth for floating library components.

## Shapes

The base radius is 12px. Nova derives small and medium corners from it; full-size buttons and inputs use the base radius. The custom workspace panels and run strip use 14px corners. Badges use the library's broad rounded shape, while step counters use compact 6px corners. Lucide line icons accompany controls; retain the existing pointer-and-clock image for the brand.

## Components

### Buttons

Compact, labeled actions with optional leading line icons. Default buttons are 32px tall; run actions are 36px tall. Primary buttons use the blue semantic role and fade to 80% color on hover. Outline buttons use a bordered background surface; ghost buttons give secondary icon actions a quiet resting state. Focus is visible, disabled controls reduce opacity to 50%, and ordinary pressed buttons move down one pixel. Icon-only actions require accessible names.

### Inputs / Fields

Fields are 40px tall with one-pixel input borders, 12px corners, and 10px horizontal padding. Text is 16px below the library's medium breakpoint and 14px above it. Dark inputs have a translucent input-colored surface. Focus changes the border and adds the shared ring; invalid state uses destructive border and ring colors. Keep labels visible above their inputs.

### Chips / Status

The outline badge is a compact 20px-high status marker with foreground text and a border. Hide the header badge at the intermediate responsive layout, where space is needed for actions.

### Cards / Containers

Setup and schedule containers share card surfaces, one-pixel borders, 14px corners, and responsive padding. Their section headings pair a title and short explanation with a quiet line icon.

### Mode Controls

Radix single-select toggle groups expose click mode, start mode, and stop mode. Selected segments use muted fill, while focus retains the semantic ring. Click mode segments have a 42px minimum height; schedule segments have a 36px minimum height.

### Run Strip

The run strip combines a tinted pointer or activity icon, tabular live status, Stop, Start clicking, and optional progress. Stop stays visible as the outline action during a run. At small widths the two actions share a full-width row. Respect reduced motion; spinning indicators are motion-safe and global reduced-motion styles shorten transitions and animations.

## Do's and Don'ts

### Do:
- **Do** use semantic theme variables and keep system appearance as the default.
- **Do** retain the name, pointer-and-clock icon, and blue action identity.
- **Do** keep visible field labels, keyboard focus, and accessible names for icon actions.
- **Do** preserve tabular numerals and the distinct run controls.

### Don't:
- **Don't** replace the requested Radix Nova controls with a competing visual vocabulary.
- **Don't** hard-code light surfaces into components that participate in dark mode.
- **Don't** hide Stop while a run is active.
