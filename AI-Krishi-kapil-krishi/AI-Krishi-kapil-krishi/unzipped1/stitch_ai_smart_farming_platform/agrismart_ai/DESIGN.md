---
name: AgriSmart AI
colors:
  surface: '#f9f9f9'
  surface-dim: '#dadada'
  surface-bright: '#f9f9f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3f3'
  surface-container: '#eeeeee'
  surface-container-high: '#e8e8e8'
  surface-container-highest: '#e2e2e2'
  on-surface: '#1a1c1c'
  on-surface-variant: '#40493d'
  inverse-surface: '#2f3131'
  inverse-on-surface: '#f0f1f1'
  outline: '#707a6c'
  outline-variant: '#bfcaba'
  surface-tint: '#1b6d24'
  primary: '#0d631b'
  on-primary: '#ffffff'
  primary-container: '#2e7d32'
  on-primary-container: '#cbffc2'
  inverse-primary: '#88d982'
  secondary: '#00639a'
  on-secondary: '#ffffff'
  secondary-container: '#51b2fe'
  on-secondary-container: '#00436a'
  tertiary: '#6e5100'
  on-tertiary: '#ffffff'
  tertiary-container: '#8c6800'
  on-tertiary-container: '#ffefd7'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#a3f69c'
  primary-fixed-dim: '#88d982'
  on-primary-fixed: '#002204'
  on-primary-fixed-variant: '#005312'
  secondary-fixed: '#cee5ff'
  secondary-fixed-dim: '#96ccff'
  on-secondary-fixed: '#001d32'
  on-secondary-fixed-variant: '#004a75'
  tertiary-fixed: '#ffdfa0'
  tertiary-fixed-dim: '#f8bd2a'
  on-tertiary-fixed: '#261a00'
  on-tertiary-fixed-variant: '#5c4300'
  background: '#f9f9f9'
  on-background: '#1a1c1c'
  surface-variant: '#e2e2e2'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
  hindi-body:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 30px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-margin: 24px
  gutter: 16px
  card-padding: 24px
  touch-target-min: 48px
---

## Brand & Style

The design system is engineered for the modern agricultural frontier, balancing high-intelligence AI capabilities with the practical needs of rural accessibility. The brand personality is **stewardship-focused, authoritative, and empowering**. It moves away from overly technical "lab" aesthetics toward a "field-ready" premium feel that instills trust in farmers and stakeholders alike.

The visual style employs a **Modern-Corporate** foundation infused with **Glassmorphism** for data visualization. This hybrid approach ensures that while the core infrastructure feels solid and reliable, the AI-driven insights appear lightweight and cutting-edge. The UI must remain high-contrast and legible under direct sunlight, emphasizing clarity of action over decorative complexity.

## Colors

The palette is derived from the natural agricultural lifecycle. **Earthy Green** serves as the anchor, representing growth and the primary brand identity. **Sky Blue** is utilized for secondary actions and water-related data points (irrigation, weather), while **Warm Yellow** highlights alerts, sunlight metrics, and critical focus areas.

The background uses a specific **neutral off-white** (#FAFAFA) to reduce glare in outdoor environments while maintaining a clean, premium paper-like quality. Text colors must maintain a minimum 7:1 contrast ratio against this background to ensure readability for users with varying visual acuity.

## Typography

This design system prioritizes **Inter** for its exceptional legibility and neutral character, which bridges the gap between technology and utility. For rural accessibility, base body sizes are increased to **18px** to compensate for outdoor glare and mobile-first usage.

**Bilingual Support (English + Hindi):** The system uses a unified sans-serif approach. When rendering Hindi script, line-heights are increased by 20% to prevent "matra" (diacritic) clipping. All labels use uppercase tracking for English but transition to standard sentence case for Hindi to maintain character integrity.

## Layout & Spacing

The design system utilizes a **12-column fluid grid** for desktop and a **4-column grid** for mobile. A strict 8px rhythmic scale governs all padding and margins. 

To accommodate users in the field, the "Touch-First" philosophy is applied: all interactive elements have a minimum height of 48px. Spacing between interactive elements is generous (minimum 16px) to prevent accidental taps, especially when the user may be wearing gloves or handling devices in motion.

## Elevation & Depth

Hierarchy is established through **Ambient Shadows** and **Glassmorphism**. 
- **Level 0 (Background):** #FAFAFA.
- **Level 1 (Cards/Containers):** Solid white with a 15% opacity green-tinted shadow (0px 4px 20px).
- **Level 2 (Data Overlays/Glass):** A semi-transparent white (70% opacity) with a 20px backdrop blur. This is reserved for AI-generated insights and dashboard metrics to create a sense of "intellectual layers" over the physical farm data.

Avoid heavy black shadows; use the Primary Green or Sky Blue to tint shadows for a more organic, modern appearance.

## Shapes

The shape language is defined by **large, friendly radii**. A base corner radius of **16px (1rem)** is applied to all primary cards and buttons to convey approachability and "soft" technology. 

- **Primary Buttons:** Fully pill-shaped (100px) to signify distinct actionability.
- **Dashboard Cards:** 24px (1.5rem) to create a premium, containerized look for data.
- **Input Fields:** 12px (0.75rem) to maintain a professional, structured feel within the softer environment.

## Components

**Buttons:** High-contrast primary buttons use the Earthy Green (#2E7D32) with white text. Secondary buttons utilize the Sky Blue for "Utility" actions (Export, Share, Map View).

**Glass Cards:** Used exclusively for "AI Insights." These cards feature a subtle 1px white border and a 20px backdrop blur. They should always contain a "Call to Action" to maintain the system's action-oriented atmosphere.

**Bilingual Toggles:** A prominent, persistent language switcher is located in the top-right of the global navigation. It uses a pill-shaped segmented control style.

**Input Fields:** Large tap areas with floating labels. Validation states use high-contrast icons (Checkmark/Warning) rather than just color, ensuring accessibility for color-blind users in bright environments.

**Status Chips:** Used for crop health and soil moisture levels. These utilize the Primary Green (Healthy), Warm Yellow (Attention), and Sky Blue (Irrigating) with semi-transparent backgrounds of the same hue for a modern "tinted" look.