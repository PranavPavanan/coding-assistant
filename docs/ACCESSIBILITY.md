# Accessibility (A11y) Guide

## Current Accessibility Features

### Keyboard Navigation
- ✅ All interactive elements accessible via Tab key
- ✅ Enter/Space activate buttons and submit forms
- ✅ Tab navigation follows logical flow: Search → Index → Query

### Screen Reader Support
- ✅ Semantic HTML elements (button, input, nav, main, etc.)
- ✅ ARIA labels on icon-only buttons
- ✅ Descriptive button text ("Start Indexing" not just "Start")
- ✅ Error messages announced to screen readers

### Visual Accessibility
- ✅ Color contrast meets WCAG AA standards
- ✅ Focus indicators visible on all interactive elements
- ✅ Icons paired with text labels
- ✅ Loading states clearly indicated with spinners and text

### Form Accessibility
- ✅ Label elements associated with inputs
- ✅ Placeholder text provides examples
- ✅ Error messages clearly describe issues
- ✅ Required fields indicated

## Testing Recommendations

### Automated Testing
```bash
# Install axe-core for accessibility testing
npm install --save-dev @axe-core/react

# Run accessibility tests
npm run test:a11y
```

### Manual Testing Checklist

#### Keyboard Navigation
- [ ] Can navigate entire app using only keyboard
- [ ] Tab order is logical and intuitive
- [ ] No keyboard traps
- [ ] Skip links available for long content
- [ ] Focus visible at all times

#### Screen Reader Testing
Test with:
- **Windows**: NVDA (free) or JAWS
- **Mac**: VoiceOver (built-in)
- **Linux**: Orca

Checklist:
- [ ] All content read in logical order
- [ ] Images have alt text
- [ ] Form labels read correctly
- [ ] Error messages announced
- [ ] Loading states announced
- [ ] Dynamic content updates announced

#### Visual Testing
- [ ] Zoom to 200% - content still readable
- [ ] Test with reduced motion preference
- [ ] Test with high contrast mode
- [ ] Test color blindness (use browser extensions)
- [ ] Minimum touch target size: 44x44px

#### Cognitive Accessibility
- [ ] Clear, simple language
- [ ] Consistent navigation patterns
- [ ] Meaningful error messages
- [ ] Avoid time-based interactions
- [ ] Provide undo/cancel options

## Improvements Needed

### High Priority
1. **Add ARIA Live Regions**
   ```tsx
   <div role="status" aria-live="polite" aria-atomic="true">
     {isIndexing && "Indexing in progress: 50% complete"}
   </div>
   ```

2. **Improve Focus Management**
   ```tsx
   // Focus first input when tab becomes active
   useEffect(() => {
     if (activeTab === 'search') {
       searchInputRef.current?.focus()
     }
   }, [activeTab])
   ```

3. **Add Skip Links**
   ```tsx
   <a href="#main-content" className="sr-only focus:not-sr-only">
     Skip to main content
   </a>
   ```

### Medium Priority
4. **Enhance Loading States**
   ```tsx
   <Button disabled={isLoading} aria-busy={isLoading}>
     {isLoading ? 'Loading...' : 'Search'}
   </Button>
   ```

5. **Add Tooltips for Context**
   ```tsx
   <Tooltip content="Search for repositories to analyze">
     <Button>Search</Button>
   </Tooltip>
   ```

6. **Announce Dynamic Updates**
   ```tsx
   <div role="alert" aria-live="assertive">
     {error && `Error: ${error}`}
   </div>
   ```

### Low Priority
7. **Dark Mode Support** (respects prefers-color-scheme)
8. **Reduced Motion Support** (respects prefers-reduced-motion)
9. **Larger Text Options**
10. **Keyboard Shortcuts** (with customization)

## WCAG 2.1 Compliance

### Level A (Minimum)
- ✅ Keyboard accessible
- ✅ Text alternatives for images
- ✅ Consistent navigation
- ✅ Error identification

### Level AA (Recommended)
- ✅ Color contrast ratio ≥ 4.5:1
- ⚠️ Resize text up to 200% (needs testing)
- ⚠️ Focus visible (partially implemented)
- ✅ Multiple ways to navigate

### Level AAA (Enhanced)
- ❌ Color contrast ratio ≥ 7:1 (not required)
- ❌ Sign language interpretation (out of scope)
- ❌ Extended audio descriptions (out of scope)

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [React Accessibility Docs](https://react.dev/learn/accessibility)
- [Radix UI Accessibility](https://www.radix-ui.com/primitives/docs/overview/accessibility)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

## Testing Tools

- **axe DevTools** (Browser extension)
- **WAVE** (Web accessibility evaluation tool)
- **Lighthouse** (Chrome DevTools)
- **NVDA** (Screen reader for Windows)
- **VoiceOver** (Screen reader for Mac)
