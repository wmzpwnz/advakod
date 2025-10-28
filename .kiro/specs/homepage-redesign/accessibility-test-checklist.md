# Accessibility Testing Checklist

## Manual Testing Checklist

### ✅ Keyboard Navigation
- [ ] Tab through all interactive elements in logical order
- [ ] Shift+Tab navigates backwards correctly
- [ ] Enter/Space activates buttons and links
- [ ] Escape closes modals and dropdowns (if applicable)
- [ ] Focus indicators are clearly visible on all elements
- [ ] No keyboard traps (can navigate away from all elements)
- [ ] Skip-to-content link works and is visible on focus

### ✅ Screen Reader Testing
- [ ] Page title is descriptive
- [ ] Headings are in logical order (h1, h2, h3, etc.)
- [ ] All images have appropriate alt text
- [ ] Form inputs have associated labels
- [ ] ARIA labels are present where needed
- [ ] Landmark regions are properly defined
- [ ] Dynamic content changes are announced
- [ ] Error messages are announced
- [ ] Loading states are announced

### ✅ Color Contrast
- [ ] All text meets WCAG AA standards (4.5:1 for normal, 3:1 for large)
- [ ] UI components meet 3:1 contrast ratio
- [ ] Focus indicators have sufficient contrast
- [ ] Hover states maintain contrast
- [ ] Test with color blindness simulators

### ✅ Visual Testing
- [ ] Page is usable at 200% zoom
- [ ] Text can be resized without breaking layout
- [ ] Content reflows properly on mobile
- [ ] No horizontal scrolling at standard zoom
- [ ] Animations respect prefers-reduced-motion
- [ ] High contrast mode is supported

### ✅ Touch/Mobile
- [ ] Touch targets are at least 44x44px
- [ ] Gestures have keyboard alternatives
- [ ] Orientation changes don't break functionality
- [ ] Pinch-to-zoom is not disabled
- [ ] Touch interactions provide feedback

## Automated Testing Tools

### Browser Extensions
- **WAVE**: https://wave.webaim.org/extension/
- **axe DevTools**: https://www.deque.com/axe/devtools/
- **Lighthouse**: Built into Chrome DevTools
- **Color Contrast Analyzer**: https://www.tpgi.com/color-contrast-checker/

### Screen Readers
- **macOS**: VoiceOver (Cmd+F5)
- **Windows**: NVDA (free) or JAWS
- **Chrome**: ChromeVox extension
- **iOS**: VoiceOver (Settings > Accessibility)
- **Android**: TalkBack (Settings > Accessibility)

### Testing Commands

#### Run Lighthouse Audit
```bash
# In Chrome DevTools
1. Open DevTools (F12)
2. Go to Lighthouse tab
3. Select "Accessibility" category
4. Click "Generate report"
```

#### Test with Screen Reader (macOS)
```bash
# Enable VoiceOver
Cmd + F5

# Navigate
Control + Option + Right Arrow (next item)
Control + Option + Left Arrow (previous item)
Control + Option + Cmd + H (next heading)
Control + Option + U (rotor menu)
```

#### Test Keyboard Navigation
```bash
# Basic navigation
Tab (next element)
Shift + Tab (previous element)
Enter (activate)
Space (activate/toggle)
Escape (close)
Arrow keys (within components)
```

## Test Results Template

### Test Session Information
- **Date**: [Date]
- **Tester**: [Name]
- **Browser**: [Browser + Version]
- **Screen Reader**: [SR + Version]
- **Device**: [Desktop/Mobile/Tablet]

### Issues Found
| Severity | Issue | Location | WCAG Criterion | Status |
|----------|-------|----------|----------------|--------|
| High | [Description] | [Component] | [e.g., 1.4.3] | Open |
| Medium | [Description] | [Component] | [e.g., 2.1.1] | Fixed |
| Low | [Description] | [Component] | [e.g., 3.2.1] | Open |

### Severity Levels
- **Critical**: Blocks access to core functionality
- **High**: Significantly impacts user experience
- **Medium**: Causes inconvenience but has workaround
- **Low**: Minor issue with minimal impact

## WCAG 2.1 Level AA Quick Reference

### Perceivable
- **1.1.1** Non-text Content (A)
- **1.3.1** Info and Relationships (A)
- **1.4.3** Contrast (Minimum) (AA) - 4.5:1 for text
- **1.4.4** Resize text (AA) - Up to 200%
- **1.4.11** Non-text Contrast (AA) - 3:1 for UI components

### Operable
- **2.1.1** Keyboard (A) - All functionality via keyboard
- **2.1.2** No Keyboard Trap (A)
- **2.4.3** Focus Order (A) - Logical tab order
- **2.4.7** Focus Visible (AA) - Visible focus indicator

### Understandable
- **3.1.1** Language of Page (A)
- **3.2.1** On Focus (A) - No context change on focus
- **3.2.2** On Input (A) - No context change on input
- **3.3.1** Error Identification (A)
- **3.3.2** Labels or Instructions (A)

### Robust
- **4.1.1** Parsing (A) - Valid HTML
- **4.1.2** Name, Role, Value (A) - Proper ARIA
- **4.1.3** Status Messages (AA) - Announced to AT

## Common Issues and Fixes

### Issue: Low Contrast
**Fix**: Adjust colors to meet 4.5:1 ratio
```css
/* Before */
color: #999; /* 2.8:1 on white */

/* After */
color: #666; /* 5.7:1 on white */
```

### Issue: Missing Alt Text
**Fix**: Add descriptive alt text
```jsx
/* Before */
<img src="logo.png" />

/* After */
<img src="logo.png" alt="Company Name - Home" />
```

### Issue: No Focus Indicator
**Fix**: Add visible focus styles
```css
button:focus {
  outline: 2px solid #007AFF;
  outline-offset: 2px;
}
```

### Issue: Missing ARIA Label
**Fix**: Add appropriate ARIA attributes
```jsx
/* Before */
<button onClick={handleClose}>×</button>

/* After */
<button onClick={handleClose} aria-label="Close dialog">×</button>
```

### Issue: Keyboard Trap
**Fix**: Ensure all elements can be navigated away from
```jsx
// Add escape key handler
useEffect(() => {
  const handleEscape = (e) => {
    if (e.key === 'Escape') {
      closeModal();
    }
  };
  document.addEventListener('keydown', handleEscape);
  return () => document.removeEventListener('keydown', handleEscape);
}, []);
```

## Resources

### Documentation
- **WCAG 2.1**: https://www.w3.org/WAI/WCAG21/quickref/
- **ARIA Authoring Practices**: https://www.w3.org/WAI/ARIA/apg/
- **WebAIM**: https://webaim.org/resources/

### Testing Tools
- **WAVE**: https://wave.webaim.org/
- **axe**: https://www.deque.com/axe/
- **Pa11y**: https://pa11y.org/
- **Lighthouse**: https://developers.google.com/web/tools/lighthouse

### Color Tools
- **Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **Color Blindness Simulator**: https://www.color-blindness.com/coblis-color-blindness-simulator/
- **Accessible Colors**: https://accessible-colors.com/

### Screen Reader Guides
- **VoiceOver**: https://www.apple.com/voiceover/info/guide/
- **NVDA**: https://www.nvaccess.org/files/nvda/documentation/userGuide.html
- **JAWS**: https://www.freedomscientific.com/training/jaws/

## Sign-off

### Accessibility Compliance Statement
- [ ] All WCAG 2.1 Level AA criteria met
- [ ] Keyboard navigation fully functional
- [ ] Screen reader compatible
- [ ] Color contrast compliant
- [ ] Mobile accessibility verified
- [ ] Documentation updated

**Tested by**: _______________
**Date**: _______________
**Approved by**: _______________
**Date**: _______________
