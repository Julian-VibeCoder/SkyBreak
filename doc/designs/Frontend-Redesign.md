# SkyBreak Frontend Redesign - Mobile Responsive Design Plan

## 1. Overview
This plan addresses three key requirements:
1. Make the Sidebar collapsible on mobile browsers
2. Make all Pages use Layout and Designed components
3. Replace current date selector with a week view (Monday to Sunday)

## 2. Current Issues
- Sidebar is fixed width (260px) and not collapsible on mobile
- Layout is inconsistent across pages - some use custom layouts
- Date selector shows Sunday to Saturday instead of Monday to Sunday

## 3. Design Principles
- Mobile-first approach: start with mobile layout, enhance for desktop
- Consistent layout across all pages using Layout component
- Accessible date picker showing full week
- Collapsible sidebar with smooth transition animation

## 4. Component Analysis

### 4.1 Sidebar (Current Structure)
- Located in /src/App.js (lines 72-111)
- Fixed width: 260px
- Contains navigation menu (NAV) and app branding
- No responsive behavior for mobile

### 4.2 Page Layouts (Current)
- All pages use the same main structure (aside + main content)
- Inconsistent padding and spacing between pages
- Some pages have additional sections (e.g., airports has two columns)

### 4.3 Date Display (Current)
- Line 131: `new Date().toLocaleDateString('de-DE', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })`
- Shows current date only, not week view

## 5. Proposed Solutions

### 5.1 Collapsible Sidebar
- Add a toggle button (hamburger icon) in mobile view
- Sidebar should collapse to 64px on mobile with expanded/collapsed states
- Use CSS transitions for smooth animation
- Implement using React state management

### 5.2 Layout Standardization
- Create a Layout component that wraps all pages
- Ensure consistent padding, spacing, and structure
- Make pages use this standardized layout

### 5.3 Week View Date Picker
- Replace current date display with a date range selector
- Show Monday to Sunday for the current week
- Include navigation arrows to switch weeks
- Use a proper date library or custom implementation

## 6. Implementation Approach

### 6.1 Phase 1: Mobile Sidebar Component
- Create a CollapsibleSidebar component
- Implement responsive behavior using CSS media queries
- Add toggle state management
- Ensure accessibility (ARIA attributes)

### 6.2 Phase 2: Layout Component
- Create a Layout component with:
  - Standard header with date display
  - Main content area with consistent padding
  - Responsive grid system
- Update all pages to use this Layout

### 6.3 Phase 3: Week View Date Picker
- Replace current date display with WeekPicker component
- Implement Monday-Sunday week view
- Add navigation controls for week switching
- Ensure proper date formatting

## 7. Technical Considerations

### 7.1 State Management
- Use React context or state management for sidebar state
- Ensure date picker state is properly managed

### 7.2 Styling
- Use CSS Flexbox/Grid for responsive layouts
- Implement smooth transitions for sidebar collapse
- Ensure mobile-first breakpoints

### 7.3 Accessibility
- Add ARIA labels for collapsible sidebar
- Ensure date picker is keyboard accessible
- Maintain proper contrast ratios

## 8. Page-by-Page Updates

### 8.1 Airports Page
- Use Layout component
- Ensure two-column layout works on desktop and single column on mobile

### 8.2 Flights Page
- Use Layout component
- Date picker will be replaced with WeekPicker

### 8.3 Trips Page
- Use Layout component
- Ensure consistent spacing and structure

### 8.4 Costs Page
- Use Layout component
- Maintain existing content structure

### 8.5 Settings Page
- Use Layout component
- Ensure form elements work well in mobile view

## 9. Testing Plan

### 9.1 Mobile Testing
- Test sidebar collapse on mobile browsers
- Verify date picker shows correct week view
- Check all pages maintain consistent layout

### 9.2 Desktop Testing
- Verify desktop view maintains proper spacing
- Ensure all features work as expected

## 10. Deliverables
- Collapsible Sidebar component for mobile
- Standardized Layout component
- Week View Date Picker component
- Updated pages using Layout component
- Documentation of changes